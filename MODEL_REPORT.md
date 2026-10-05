# Engineering & Model Architecture Report

## 1. Problem Overview & Design Goals

Splitting restaurant bills among a group can be surprisingly frustrating, particularly when dealing with the way restaurant bills are structured in India:

1. **Tax Disaggregation:** Indian dining bills commonly separate taxes into CGST (Central GST, typically 2.5%) and SGST (State GST, typically 2.5%), or use composite GST rates such as 5% or 18%.

2. **Service Charges & Discounts:** Restaurants often add a 5–10% service charge to the pre-tax subtotal. On top of this, there may also be table-level discounts or coupon-based reductions.

3. **Unfair "Equal Split" Pitfalls:** Consider a situation where Person A orders a ₹120 fresh lime soda while Person B orders a ₹650 mutton platter. If taxes and service charges are simply divided equally, Person A ends up paying more than their fair share. These additional charges should instead be distributed according to each diner's actual share of the table's consumption.

4. **Mobile Capture Reality:** Thermal paper receipts can wrinkle easily and fade over time. On top of that, photos taken at restaurant tables often have problems such as shadows, glare, and angled perspectives.

To address these issues, SplitSnap was designed around three tightly connected engines:

- **High-Precision Neural OCR & Spatial Parsing Engine:** A fast, cross-platform OCR engine (PyTorch EasyOCR and Apple Vision) combined with a deterministic 3-zone spatial layout parser ([`receipt_parser.py`](backend/app/receipt_parser.py)) that reliably isolates merchant metadata, item tables, prices, and dual CGST/SGST taxes from real-world camera photos.

- **Visual Transformer Model (Donut):** A fine-tuned visual document transformer (**Donut** / `naver-clova-ix/donut-base`) that reads raw receipt patches and explores end-to-end token generation directly from visual cross-attention vectors.

- **Apportionment Engine:** A deterministic mathematical engine that calculates fractional line-item shares, distributes taxes and surcharges according to consumption ratios, and produces a clear, human-readable breakdown.

---

## 2. Architecture & Design: Hybrid Document Understanding

To provide both research innovation and production reliability, SplitSnap implements a **Hybrid Multi-Engine Strategy**:

### 2.1 The Traditional Pipeline Challenges
A standard two-stage pipeline relies on an OCR engine followed by an unconstrained LLM or generic regex:
$$\text{Image} \xrightarrow{\text{OCR Engine}} \text{Raw Text Tokens + Bounding Boxes} \xrightarrow{\text{LLM / Regex}} \text{Structured JSON}$$
If the downstream parsing rules do not account for spatial layout (e.g. multi-line dish names, addresses mixed with food items, or split CGST/SGST columns), errors cascade rapidly. Furthermore, sending raw receipts to remote LLM APIs introduces latency and privacy risks.

### 2.2 SplitSnap's Hybrid Solution
SplitSnap solves this by pairing two complementary approaches:
1. **Geometric 3-Zone Spatial Parser:** Instead of unstructured regex or remote LLM calls, our OCR parser groups words by horizontal alignment, discards header metadata (addresses, phone numbers, GSTIN registration codes), enforces tabular column extraction, and verifies arithmetic symmetry between CGST and SGST.
2. **End-to-End Visual Parsing with Donut:** For visual document understanding research, we fine-tune Donut (Swin Transformer + mBART decoder), allowing the model to learn visual layout features (margins, fonts, bold headers) alongside language tokens.

---

## 3. Indian Dining Domain Adaptation

Public receipt datasets such as CORD and SROIE are focused mainly on Western supermarket receipts or Southeast Asian retail slips. They do not adequately represent Indian dish names, dual-tax structures such as CGST/SGST, or the service-charge patterns commonly found on Indian restaurant bills.

### 3.1 Dataset Transformation Pipeline (`ml/scripts/prepare_cord_indianized.py`)

To adapt the pre-trained Donut backbone to Indian restaurant receipts, we created an automated domain transformation pipeline:

- **Tax Splitting:** Generic tax fields were converted into statutory Indian restaurant tax pairs: CGST (2.5%) and SGST (2.5%), calculated against the food subtotal.

- **Surcharge Integration:** Realistic restaurant service charges ranging from 5% to 10% were added, along with promotional discounts.

- **Dish & Merchant Lexicon:** Generic catalog entries were mapped to commonly found North Indian, South Indian, and Mughlai restaurant items, including *Paneer Butter Masala, Butter Chicken, Dal Makhani, Garlic Naan, Biryani, Dosa,* and *Filter Coffee*. Realistic price distributions ranging from ₹40–₹850 were also used.

- **Target Extraction Schema:** Target annotations were converted into structured XML sequences enclosed within custom domain tokens (`<s_splitsnap>`, `<s_merchant>`, `<s_items>`, `<s_taxes>`, `<s_service_charge>`, `<s_discount>`, `<s_total>`).

### 3.2 Physical Degradation Augmentations (`ml/scripts/augment_receipts.py`)

Receipt photos taken in restaurants have their own set of physical imperfections. To make the model more robust to these conditions, four targeted image augmentations were applied:

1. **Fold & Shadow Bands:** Non-linear horizontal and diagonal gradient shadows were added to simulate paper creases running across text lines.

2. **Perspective Warping:** Random 4-point perspective transformations were used to simulate camera angles between 5° and 20° off-axis.

3. **Defocus & Motion Blur:** Gaussian kernels with random radii were applied to simulate handheld camera blur in dimly lit dining environments.

4. **Brightness & Contrast Jitter:** Gamma and contrast adjustments were introduced to simulate uneven lighting from overhead spotlights.

---

## 4. Token-Level Confidence Derivation & Human-in-the-Loop Review

Deep learning vision models can occasionally hallucinate values or struggle when the receipt contains severely faded text. Instead of treating the model's output as automatically correct, SplitSnap extracts confidence information that can be used to decide when human verification is needed.

### 4.1 Logit Probability Tracking

During autoregressive generation:

1. At each decoding step $t$, the decoder produces raw logits $\mathbf{Z}_t \in \mathbb{R}^{V}$ across the vocabulary $V$.

2. The softmax probability for the generated token $y_t$ is calculated as:

$$p_t = \frac{\exp(Z_{t, y_t})}{\sum_{v=1}^V \exp(Z_{t, v})}$$

3. For structured numeric fields such as item price, tax amount, and subtotal, token probabilities are averaged across the field's token span:

$$\text{Confidence}_{\text{field}} = \frac{1}{K} \sum_{k=1}^K p_k$$

4. If a field's confidence falls below $0.85$, the backend marks it as `is_low_confidence: True`.

### 4.2 Interactive Verification Interface

During the frontend verification step:

- High-confidence fields are shown in their normal resting state.

- Low-confidence fields are highlighted with an amber warning border and a clear message asking the user to double-check the price.

- Users can edit item names, change quantities, modify prices, or add missing lines with a single click. The totals are recalculated in real time.

---

## 5. Google Colab T4 Training Pipeline & Engineering Workarounds

Fine-tuning Donut on a free Google Colab T4 GPU with 16 GB of VRAM introduced several practical memory and runtime challenges.

### 5.1 Resolving CUDA Out-of-Memory (OOM)

- **Problem:** The default Donut configuration processes images at $2560 \times 1920$ resolution. With a standard batch size of 2 or 4, the activations can quickly exceed the 14.7 GB of usable memory on a T4 GPU, causing the runtime to crash.

- **Fix:** We reduced the input processor size to $1280 \times 960$ pixels (`processor.image_processor.size = {"height": 1280, "width": 960}`), set `per_device_train_batch_size = 1`, and compensated for the smaller batches by using `gradient_accumulation_steps = 8`. This kept VRAM usage stable at approximately 4.8 GB.

### 5.2 PyTorch 2.x Gradient Checkpointing Conflict

- **Problem:** Enabling `model.gradient_checkpointing_enable()` with the Swin Transformer backbone resulted in a PyTorch error:

  `CheckpointError: A different number of tensors was saved during original forward and recomputation`.

- **Fix:** We disabled gradient checkpointing and explicitly set `model.config.use_cache = False` during training. Combined with `fp16 = True` for mixed-precision training, this provided stable training throughput without runtime crashes.

### 5.3 Background Uvicorn Serving & Ngrok Bypass

- **Asyncio Conflict:** Running `uvicorn.run()` directly inside a Colab cell causes `RuntimeError: asyncio.run() cannot be called from a running event loop`, because IPython already maintains its own active event loop.

- **Thread Isolation:** To avoid this conflict, Uvicorn is started inside a background daemon thread (`threading.Thread(target=server.run, daemon=True)`), and the server is exposed through PyNgrok.

- **Ngrok Interstitial Bypass:** Free Ngrok tunnels normally return an HTML anti-abuse splash page. To bypass this when making API requests, the client adds an `ngrok-skip-browser-warning: true` header to all fetch requests, allowing the client to receive the JSON payload directly.

---

## 6. Proportional Apportionment Algorithm

### 6.1 Mathematical Formulation

Let the bill contain items $I_1, I_2, \dots, I_M$, where item $I_k$ has price $c_k$ and is shared by a subset of diners $S_k \subseteq \{1, \dots, N\}$.

1. **Individual Consumption Subtotal:**

$$S_i = \sum_{k: i \in S_k} \frac{c_k}{|S_k|}$$

2. **Total Assigned Subtotal:**

$$S_{\text{assigned}} = \sum_{i=1}^N S_i$$

3. **Consumption Proportion:**

$$P_i = \frac{S_i}{S_{\text{assigned}}} \quad \left(\sum_{i=1}^N P_i = 1.0\right)$$

4. **Apportionment of Taxes, Surcharges, and Discounts:**

$$T_i = P_i \times T_{\text{bill}}, \quad C_i = P_i \times \text{ServiceCharge}_{\text{bill}}, \quad D_i = P_i \times \text{Discount}_{\text{bill}}$$

5. **Final Payable Amount:**

$$\text{Final}_i = S_i + T_i + C_i - D_i$$

### 6.2 Cent Rounding Discrepancy Reconciliation

Because the individual calculations involve division, the sum of rounded values ($\sum \text{round}(\text{Final}_i, 2)$) can sometimes differ from the original bill by $\pm 1$ or $\pm 2$ paise.

SplitSnap detects this discrepancy using $\Delta = \text{BillTotal} - \sum \text{Final}_i$ and reconciles it by assigning the fractional difference to the party member with the largest bill share. This keeps the final calculation mathematically balanced with the original bill.

### 6.3 Manual Adjustments with Audit Balance

If someone in the group agrees to pay a specific amount—for example, paying in cash or covering a fixed ₹500—the app supports manual overrides. Whenever an override is made, the summary view tracks the difference between the modified total and the original bill. An audit indicator is also displayed so that everyone at the table can see whether the bill has been fully covered.

---

## 7. Plain-Language Explanation Engine

Instead of relying on an external LLM to generate explanations—which would introduce additional latency, hallucination risk, and non-deterministic output—SplitSnap uses a deterministic explanation generator.

### Example Output:

> *"Priya: Paneer Butter Masala (₹380.00) + 1/2 share of Garlic Naan (₹135.00) = ₹515.00 subtotal. With a 31.6% proportional share of the table consumption, she accounts for ₹25.75 taxes and ₹25.75 service charge. Final payable: ₹566.50."*

This approach guarantees instant computation, eliminates hallucination risk, and keeps the calculation transparent and easy for every member of the party to understand.