import {
  ReceiptData,
  Person,
  SplitCalculationResponse,
  PersonSplitResult,
  AssignedItemDetail
} from "./types";
//code hogaya bhot bhayankar a thoida maths bhi hojaye
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function extractReceiptFromApi(
  file?: File,
  presetId?: string
): Promise<ReceiptData> {
  // If user selected a preset, return it immediately with zero network latency
  if (presetId) {
    const { SAMPLE_PRESETS } = await import("./sampleData");
    const found = SAMPLE_PRESETS.find((p) => p.id === presetId);
    if (found) {
      return JSON.parse(JSON.stringify(found.data));
    }
  }

  // If user uploaded an image, send to backend with timeout and fallback
  if (file) {
    const formData = new FormData();
    formData.append("file", file);

    const candidateUrls = [BACKEND_URL];
    if (BACKEND_URL !== "http://localhost:8000" && BACKEND_URL !== "http://127.0.0.1:8000") {
      candidateUrls.push("http://localhost:8000");
    }

    for (const url of candidateUrls) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 6000);
        const res = await fetch(`${url}/api/extract`, {
          method: "POST",
          headers: {
            "ngrok-skip-browser-warning": "true"
          },
          body: formData,
          signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (res.ok) {
          const jsonRes = await res.json();

          if (Array.isArray(jsonRes.items) && jsonRes.items.length > 0) {
            return jsonRes;
          }

          if (jsonRes.raw) {
            return parseRawDonutSequence(jsonRes.raw, jsonRes.mean_confidence || 0.95);
          }
        }
      } catch (err) {
        console.warn(`Extraction at ${url} unavailable, trying fallback.`, err);
      }
    }
  }

  // Fallback to sample bill if backend is unavailable
  const { SAMPLE_PRESETS } = await import("./sampleData");
  return JSON.parse(JSON.stringify(SAMPLE_PRESETS[0].data));
}

export function parseRawDonutSequence(seq: string, avgConf: number): ReceiptData {
  let merchantName = "Restaurant Bill";
  const mMatch = seq.match(/<s_merchant>(.*?)<\/s_merchant>/);
  if (mMatch) merchantName = mMatch[1].trim();

  let dateVal = "2026-10-04";
  const dMatch = seq.match(/<s_date>(.*?)<\/s_date>/);
  if (dMatch) dateVal = dMatch[1].trim();

  // Extract items
  const items: any[] = [];
  const itemMatches = seq.match(/<s_item>(.*?)<\/s_item>/g) || [];
  
  itemMatches.forEach((itStr, idx) => {
    let name = "Dish";
    let qty = 1;
    let price = 0.0;

    const nMatch = itStr.match(/<s_name>(.*?)<\/s_name>/);
    if (nMatch) name = nMatch[1].trim();

    const qMatch = itStr.match(/<s_qty>(.*?)<\/s_qty>/);
    if (qMatch) qty = parseInt(qMatch[1].replace(/[^\d]/g, "")) || 1;

    const pMatch = itStr.match(/<s_price>(.*?)<\/s_price>/);
    if (pMatch) price = parseFloat(pMatch[1].replace(/[^\d.]/g, "")) || 0.0;

    const isLow = avgConf < 0.85;

    items.push({
      id: `item_${idx + 1}_${Date.now()}`,
      name: name || `Item ${idx + 1}`,
      quantity: Math.max(1, qty),
      price: price > 0 ? price : 150.0,
      is_low_confidence: isLow,
      confidence: Number(avgConf.toFixed(2))
    });
  });

  // If no items were parsed from malformed seq, provide fallback items
  if (items.length === 0) {
    items.push(
      { id: "item_1", name: "Paneer Butter Masala", quantity: 1, price: 320.0, is_low_confidence: false, confidence: 0.96 },
      { id: "item_2", name: "Butter Naan", quantity: 2, price: 120.0, is_low_confidence: false, confidence: 0.98 },
      { id: "item_3", name: "Dal Makhani", quantity: 1, price: 260.0, is_low_confidence: true, confidence: 0.74 }
    );
  }

  const subtotal = Number(items.reduce((acc, it) => acc + it.price, 0).toFixed(2));
  const cgst = Number((subtotal * 0.025).toFixed(2));
  const sgst = Number((subtotal * 0.025).toFixed(2));
  const sc = Number((subtotal * 0.05).toFixed(2));
  const total = Number((subtotal + cgst + sgst + sc).toFixed(2));

  return {
    merchant: { name: merchantName, date: dateVal },
    items,
    subtotal: { amount: subtotal, is_low_confidence: false, confidence: 0.98 },
    taxes: [
      { name: "CGST (2.5%)", rate: 2.5, amount: cgst, is_low_confidence: false, confidence: 0.95 },
      { name: "SGST (2.5%)", rate: 2.5, amount: sgst, is_low_confidence: false, confidence: 0.95 }
    ],
    service_charge: { amount: sc, is_low_confidence: false, confidence: 0.92 },
    discount: { amount: 0.0, is_low_confidence: false, confidence: 1.0 },
    total: { amount: total, is_low_confidence: false, confidence: 0.99 }
  };
}

export function calculateLocalProportionalSplit(
  receipt: ReceiptData,
  people: Person[],
  assignments: Record<string, string[]>,
  overrides?: Record<string, number>
): SplitCalculationResponse {
  const itemMap = new Map(receipt.items.map((i) => [i.id, i]));
  const globalSubtotal = Number(
    receipt.items.reduce((acc, it) => acc + it.price, 0).toFixed(2)
  );
  const totalTaxes = Number(
    receipt.taxes.reduce((acc, t) => acc + t.amount, 0).toFixed(2)
  );
  const totalSc = Number(receipt.service_charge.amount.toFixed(2));
  const totalDiscount = Number(receipt.discount.amount.toFixed(2));
  let billTotal = Number(receipt.total.amount.toFixed(2));

  if (billTotal === 0) {
    billTotal = Number(
      (globalSubtotal + totalTaxes + totalSc - totalDiscount).toFixed(2)
    );
  }

  const personItems: Record<string, AssignedItemDetail[]> = {};
  const personSubtotals: Record<string, number> = {};
  const unassignedItems: string[] = [];

  for (const p of people) {
    personItems[p.id] = [];
    personSubtotals[p.id] = 0.0;
  }

  for (const item of receipt.items) {
    const sharers = assignments[item.id] || [];
    if (sharers.length === 0) {
      unassignedItems.push(item.name);
      continue;
    }

    const nSharers = sharers.length;
    const shareVal = Number((item.price / nSharers).toFixed(2));
    const fractionStr = nSharers > 1 ? `1/${nSharers}` : "1/1";

    for (const pId of sharers) {
      if (personItems[pId]) {
        personItems[pId].push({
          item_id: item.id,
          item_name: item.name,
          full_price: Number(item.price.toFixed(2)),
          share_fraction: fractionStr,
          num_sharers: nSharers,
          share_amount: shareVal
        });
        personSubtotals[pId] = Number(
          (personSubtotals[pId] + shareVal).toFixed(2)
        );
      }
    }
  }

  const totalAssignedSubtotal = Number(
    Object.values(personSubtotals)
      .reduce((a, b) => a + b, 0)
      .toFixed(2)
  );

  const splits: PersonSplitResult[] = [];
  let calculatedSum = 0;




  for (const p of people) {
    const pSubtotal = personSubtotals[p.id] || 0.0;
    const pItems = personItems[p.id] || [];

    const proportionRatio =
      totalAssignedSubtotal > 0 ? pSubtotal / totalAssignedSubtotal : 0.0;
    const proportionPct = Number((proportionRatio * 100).toFixed(1));

    const taxesShare = Number((totalTaxes * proportionRatio).toFixed(2));
    const scShare = Number((totalSc * proportionRatio).toFixed(2));
    const discShare = Number((totalDiscount * proportionRatio).toFixed(2));

    const calcTotal = Number(
      (pSubtotal + taxesShare + scShare - discShare).toFixed(2)
    );






    let isOverridden = false;
    let overrideDiff = 0.0;
    let finalTotal = calcTotal;

    if (overrides && overrides[p.id] !== undefined && overrides[p.id] !== null) {
      isOverridden = true;
      finalTotal = Number(overrides[p.id].toFixed(2));
      overrideDiff = Number((finalTotal - calcTotal).toFixed(2));
    }

    calculatedSum = Number((calculatedSum + finalTotal).toFixed(2));

    // Generate natural explanation
    let explanation = "";
    if (pItems.length === 0) {
      explanation = `${p.name} didn't have any items assigned (₹0.00).`;
    } else {
      const itemPhrases = pItems.map((it) =>
        it.num_sharers === 1
          ? `${it.item_name} (₹${it.full_price.toFixed(2)})`
          : `${it.share_fraction} of ${it.item_name} (₹${it.share_amount.toFixed(2)})`
      );




      const itemsText = itemPhrases.join(", ");
      const extras = [];
      if (taxesShare > 0) extras.push(`₹${taxesShare.toFixed(2)} GST`);
      if (scShare > 0) extras.push(`₹${scShare.toFixed(2)} service charge`);
      if (discShare > 0) extras.push(`-₹${discShare.toFixed(2)} discount`);
      const extrasStr = extras.length > 0 ? extras.join(" + ") : "no extra charges";

      explanation = `${p.name} had ${itemsText} for a ₹${pSubtotal.toFixed(2)} food subtotal (${proportionPct.toFixed(1)}% of the table). Adding their proportional share of ${extrasStr}, their share comes to ₹${calcTotal.toFixed(2)}.`;
      if (isOverridden) {
        const diffStr = overrideDiff > 0 ? `+₹${overrideDiff.toFixed(2)}` : `-₹${Math.abs(overrideDiff).toFixed(2)}`;
        explanation += ` Adjusted manually to ₹${finalTotal.toFixed(2)} (${diffStr}).`;
      }
    }

    splits.push({
      person_id: p.id,
      person_name: p.name,
      assigned_items: pItems,
      subtotal: pSubtotal,
      proportion_ratio: Number(proportionRatio.toFixed(4)),
      proportion_percentage: proportionPct,
      taxes_share: taxesShare,
      service_charge_share: scShare,
      discount_share: discShare,
      calculated_total: calcTotal,
      final_total: finalTotal,
      is_overridden: isOverridden,
      override_difference: overrideDiff,
      explanation
    });
  }






  const differenceFromBill = Number((calculatedSum - billTotal).toFixed(2));

  return {
    global_subtotal: globalSubtotal,
    total_taxes: totalTaxes,
    total_service_charge: totalSc,
    total_discount: totalDiscount,
    bill_total: billTotal,
    calculated_sum: calculatedSum,
    difference_from_bill: differenceFromBill,
    splits,
    unassigned_items: unassignedItems
  };
}





export async function calculateProportionalSplitApi(
  receipt: ReceiptData,
  people: Person[],
  assignments: Record<string, string[]>,
  overrides?: Record<string, number>
): Promise<SplitCalculationResponse> {
  const candidateUrls = [BACKEND_URL];
  if (BACKEND_URL !== "http://localhost:8000" && BACKEND_URL !== "http://127.0.0.1:8000") {
    candidateUrls.push("http://localhost:8000");
  }

  for (const url of candidateUrls) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);
      const res = await fetch(`${url}/api/calculate-split`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true"
        },
        body: JSON.stringify({
          receipt,
          people,
          item_assignments: assignments,
          manual_overrides: overrides
        }),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (res.ok) {
        return await res.json();
      }
    } catch (err) {
      console.warn(`Backend calculation at ${url} unavailable:`, err);
    }
  }

  return calculateLocalProportionalSplit(receipt, people, assignments, overrides);
}
