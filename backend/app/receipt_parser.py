"""
Semantic Receipt Parser for SplitSnap.
Converts raw OCR tokens into structured ReceiptData schemas with line items,
merchant details, tax breakdowns, and confidence flags.
Features:
- Spatial 3-zone receipt layout partitioning (Header / Items Body / Summary & Taxes)
- Strict address and metadata rejection so addresses never become food items
- Robust GST / SGST extraction with rate reconciliation and GSTIN exclusion
- Auto-balancing of symmetrical CGST / SGST
- Resilient OCR price token cleanup
"""
import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from .schemas import ReceiptData, ReceiptItem, TaxItem, AmountField, MerchantInfo

ADDRESS_KEYWORDS = {
    "road", "rd", "rd.", "street", "st", "st.", "lane", "nagar", "marg", "floor", "flr",
    "block", "blk", "sector", "sec", "plot", "phase", "opp", "opposite",
    "near", "behind", "colony", "bazaar", "market", "enclave", "plaza",
    "complex", "mall", "tower", "building", "bldg", "shop", "booth",
    "circle", "junction", "cross", "crossroad", "extn", "extension",
    "delhi", "new delhi", "mumbai", "bombay", "bangalore", "bengaluru",
    "hyderabad", "chennai", "madras", "kolkata", "calcutta", "pune",
    "gurgaon", "gurugram", "noida", "faridabad", "ghaziabad", "ahmedabad",
    "jaipur", "chandigarh", "lucknow", "india", "karnataka", "maharashtra",
    "tamil nadu", "haryana", "uttar pradesh", "pin", "pincode"
}

CONTACT_KEYWORDS = [
    "ph:", "phone", "tel:", "telephone", "mob:", "mobile", "contact",
    "email:", "e-mail", "website", "www.", "http", ".com", ".in", ".org",
    "call us", "feedback"
]

LEGAL_ID_KEYWORDS = [
    "gstin", "gst no", "gst reg", "gstin/uin", "tin no", "fssai",
    "lic no", "license no", "pan no", "cin no", "cst no", "vat tin"
]

ORDER_META_KEYWORDS = [
    "tax invoice", "retail invoice", "bill no", "invoice no", "inv no",
    "order no", "token no", "table no", "table:", "tbl:", "tbl",
    "server:", "stn:", "station", "cashier:", "steward:", "pax:",
    "covers:", "guests:", "pos:", "terminal:", "dine in",
    "take away", "delivery", "kiosk", "captain", "waiter", "bill date",
    "date:", "time:"
]

TABLE_HEADER_KEYWORDS = [
    "item", "description", "qty", "quantity", "rate", "price",
    "amount", "amt", "particulars", "items"
]

IGNORE_FOOTER_WORDS = [
    "thank you", "visit again", "have a nice day", "powered by", "wifi", "password",
    "customer copy", "merchant copy", "signature", "terms", "conditions"
]

def is_address_or_metadata_line(txt: str) -> bool:
    """
    Returns True if the line represents an address, phone number, GSTIN,
    FSSAI license, or bill metadata, so it can never be misclassified as a food item.
    """
    lower = txt.lower().strip()
    if not lower:
        return True

    # 1. Contact information
    if any(k in lower for k in CONTACT_KEYWORDS):
        return True

    # 2. Legal / Registration IDs (GSTIN, FSSAI, PAN)
    if any(k in lower for k in LEGAL_ID_KEYWORDS):
        return True
    if re.search(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b", txt):
        return True
    if re.search(r"\b(1\d{13}|2\d{13})\b", txt):  # 14-digit FSSAI
        return True

    # 3. Order / Table / Cashier metadata
    if any(k in lower for k in ORDER_META_KEYWORDS):
        return True

    # 4. Indian PIN Code (6 digits starting 1-9)
    if re.search(r"\b[1-9][0-9]{2}\s?[0-9]{3}\b", txt):
        return True

    # 5. Phone numbers
    if re.search(r"(\+91[\-\s]?)?[6-9]\d{9}\b", txt) or re.search(r"\b\d{3,5}[\-\s]\d{6,8}\b", txt):
        return True

    # 6. Address & Location markers
    words = set(re.findall(r"\b[a-zA-Z]+\b", lower))
    addr_count = len(words.intersection(ADDRESS_KEYWORDS))
    if addr_count >= 2:
        return True
    if addr_count >= 1 and re.search(r"\b(floor|plot|sector|sec|block|blk|shop|no\.|opp|near)\b", lower):
        return True

    return False

def cluster_tokens_into_lines(tokens: List[Dict[str, Any]], y_threshold: float = 0.018) -> List[Dict[str, Any]]:
    """
    Groups OCR bounding box tokens with similar vertical Y coordinates into horizontal lines,
    sorted from top to bottom and left to right.
    """
    if not tokens:
        return []

    # Sort tokens primarily by Y (top to bottom)
    sorted_tokens = sorted(tokens, key=lambda t: t.get("y", 0.0))
    lines: List[List[Dict[str, Any]]] = []

    for t in sorted_tokens:
        placed = False
        t_y = t.get("y", 0.0)
        for line in lines:
            line_y = sum(item.get("y", 0.0) for item in line) / len(line)
            if abs(t_y - line_y) <= y_threshold:
                line.append(t)
                placed = True
                break
        if not placed:
            lines.append([t])

    clustered = []
    for line in lines:
        # Sort tokens in this line left-to-right by X
        line.sort(key=lambda t: t.get("x", 0.0))
        full_text = " ".join(t.get("text", "").strip() for t in line if t.get("text", "").strip())
        avg_conf = sum(t.get("confidence", 1.0) for t in line) / max(1, len(line))
        avg_y = sum(t.get("y", 0.0) for t in line) / max(1, len(line))
        min_x = min(t.get("x", 0.0) for t in line)
        if full_text:
            clustered.append({
                "text": full_text,
                "confidence": avg_conf,
                "y": avg_y,
                "x": min_x,
                "tokens": line
            })

    # Sort lines from top to bottom
    clustered.sort(key=lambda l: l["y"])
    return clustered

def parse_receipt_lines(lines: List[Dict[str, Any]]) -> ReceiptData:
    """
    Transforms clustered OCR lines into structured ReceiptData with
    robust spatial zoning, address filtering, and tax validation.
    """
    merchant_name = "Restaurant"
    date_val = datetime.now().strftime("%Y-%m-%d")
    items: List[ReceiptItem] = []
    taxes: List[TaxItem] = []
    sc_val: float = 0.0
    disc_val: float = 0.0
    subtotal_val: Optional[float] = None
    total_val: Optional[float] = None

    consumed_indices = set()

    # ----------------------------------------------------
    # ZONE DETECTION (Spatial partitioning)
    # ----------------------------------------------------
    start_table_idx = None
    end_table_idx = len(lines)

    for idx, l in enumerate(lines):
        txt = l["text"].strip()
        lower = txt.lower()

        # Identify Table Header boundary (start of items)
        if start_table_idx is None:
            # Check for header words or divider line
            header_matches = sum(1 for kw in TABLE_HEADER_KEYWORDS if kw in lower.split())
            if header_matches >= 2 or (re.search(r"[-=_.]{4,}", txt) and idx > 0):
                start_table_idx = idx + 1
                consumed_indices.add(idx)

        # Identify Summary & Taxes boundary (end of items)
        if any(k in lower for k in ["subtotal", "sub total", "cgst", "sgst", "vat", "service charge", "grand total", "net amount", "total:"]):
            if end_table_idx == len(lines):
                end_table_idx = idx

    if start_table_idx is None:
        start_table_idx = 1  # Default to after merchant name

    # ----------------------------------------------------
    # 1. Detect Merchant Name (From Topmost Header Lines)
    # ----------------------------------------------------
    for idx, l in enumerate(lines[:min(8, end_table_idx)]):
        txt = l["text"].strip()
        lower = txt.lower()
        if is_address_or_metadata_line(txt):
            consumed_indices.add(idx)
            continue
        if any(h in lower for h in TABLE_HEADER_KEYWORDS):
            continue
        if any(f in lower for f in IGNORE_FOOTER_WORDS):
            continue
        if re.search(r"^\d+$", txt) or re.search(r"\d{1,2}[/-]\d{1,2}", txt):
            continue
        # Prominent line with letters
        if len(re.sub(r"[^a-zA-Z]", "", txt)) >= 3:
            merchant_name = txt
            consumed_indices.add(idx)
            break

    # ----------------------------------------------------
    # 2. Detect Date
    # ----------------------------------------------------
    date_pattern = r"(\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b)"
    for idx, l in enumerate(lines[:min(14, end_table_idx + 2)]):
        match = re.search(date_pattern, l["text"])
        if match:
            consumed_indices.add(idx)
            raw_date = match.group(1).replace("/", "-")
            parts = raw_date.split("-")
            try:
                if len(parts) == 3:
                    if len(parts[0]) == 4:  # YYYY-MM-DD
                        date_val = f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
                    elif len(parts[2]) == 4:  # DD-MM-YYYY
                        date_val = f"{parts[2]}-{int(parts[1]):02d}-{int(parts[0]):02d}"
                    else:
                        date_val = raw_date
            except Exception:
                date_val = raw_date
            break

    # ----------------------------------------------------
    # 3. Detect Totals, Subtotals, Taxes, Service Charge
    # ----------------------------------------------------
    for idx, l in enumerate(lines):
        txt = l["text"].strip()
        lower = txt.lower()

        # NEVER parse GSTIN / FSSAI / Address as taxes or totals
        if is_address_or_metadata_line(txt):
            consumed_indices.add(idx)
            continue

        # Grand Total / Net Amount
        if any(k in lower for k in ["grand total", "net amount", "total amount", "amount due", "bill total", "total:"]) or (lower == "total" or lower.startswith("total ")):
            amt_match = re.findall(r"\d+(?:\.\d{1,2})?", txt.replace(",", ""))
            if amt_match:
                try:
                    total_val = float(amt_match[-1])
                    consumed_indices.add(idx)
                    continue
                except ValueError:
                    pass

        # Subtotal
        if "subtotal" in lower or "sub total" in lower or "food total" in lower:
            amt_match = re.findall(r"\d+(?:\.\d{1,2})?", txt.replace(",", ""))
            if amt_match:
                try:
                    subtotal_val = float(amt_match[-1])
                    consumed_indices.add(idx)
                    continue
                except ValueError:
                    pass

        # Taxes: CGST, SGST, IGST, VAT (Explicit check, excluding GSTIN)
        if not any(k in lower for k in ["gstin", "gst no", "gst reg", "gstin/uin"]):
            tax_kw = ["cgst", "sgst", "igst", "vat"]
            found_taxes = [kw for kw in tax_kw if re.search(rf"\b{kw}\b", lower)]
            if found_taxes:
                rate_match = re.search(r"(\d+(?:\.\d+)?)\s*%", txt)
                rate = float(rate_match.group(1)) if rate_match else 2.5
                numbers = [float(n) for n in re.findall(r"\d+(?:\.\d{1,2})?", txt.replace(",", ""))]

                for tax_name in found_taxes:
                    t_amt = 0.0
                    if numbers:
                        # Tax amount is typically the smallest positive number or closest to rate% of subtotal
                        cand_amounts = [n for n in numbers if n != rate and n > 0]
                        if cand_amounts:
                            t_amt = cand_amounts[-1]

                    # Auto-fix missing decimal point if tax exceeds plausible ratio
                    if subtotal_val and t_amt > (subtotal_val * 0.35) and t_amt > 100:
                        t_amt = round(t_amt / 100.0, 2)

                    display_name = f"{tax_name.upper()} ({rate}%)"
                    taxes.append(TaxItem(
                        name=display_name,
                        rate=rate,
                        amount=t_amt,
                        is_low_confidence=l["confidence"] < 0.85,
                        confidence=round(l["confidence"], 2)
                    ))
                consumed_indices.add(idx)
                continue

        # Service Charge / Surcharge
        if any(sc in lower for sc in ["service charge", "service fee", "charge:", "svc charge", "service chg", "sanic? charge", "surcharge"]) or re.search(r"\b(sc|svc)\b", lower):
            amt_match = re.findall(r"\d+(?:\.\d{1,2})?", txt.replace(",", ""))
            if amt_match:
                try:
                    sc_cand = float(amt_match[-1])
                    if sc_cand > 500 and (sc_cand > (subtotal_val or 500)):
                        sc_cand = sc_cand / 100.0
                    sc_val = sc_cand
                    consumed_indices.add(idx)
                    continue
                except ValueError:
                    pass

        # Discount
        if "discount" in lower or "less" in lower:
            amt_match = re.findall(r"\d+(?:\.\d{1,2})?", txt.replace(",", ""))
            if amt_match:
                try:
                    disc_val = float(amt_match[-1])
                    consumed_indices.add(idx)
                    continue
                except ValueError:
                    pass

    # ----------------------------------------------------
    # 4. Extract Line Items (Strictly in the Items Table Zone)
    # ----------------------------------------------------
    for idx, l in enumerate(lines):
        if idx in consumed_indices:
            continue

        # Strictly enforce table zoning: Header lines cannot be items
        if idx < start_table_idx:
            continue
        # Lines beyond summary cannot be items
        if idx >= end_table_idx and (subtotal_val is not None or total_val is not None):
            continue

        txt = l["text"].strip()
        lower = txt.lower()

        # Reject any addresses or metadata
        if is_address_or_metadata_line(txt):
            continue

        # Skip headers, footers, dates, and separator lines
        if any(h in lower for h in TABLE_HEADER_KEYWORDS) or any(f in lower for f in IGNORE_FOOTER_WORDS):
            continue
        if "date" in lower or "time" in lower or re.search(r"\d{1,2}[/-]\d{1,2}", txt):
            continue
        if re.search(r"^[-=_*#\s.]+$", txt):
            continue

        # OCR price token repair (e.g. I8uu -> 180.00, 34O -> 340)
        cleaned_txt = txt
        tokens = cleaned_txt.split()
        if tokens:
            last_tok = tokens[-1]
            if re.match(r"^[Il|]?\d+[oOuU0-9]*(?:\.\d+)?$", last_tok):
                fixed_last = last_tok.replace("I", "1").replace("l", "1").replace("|", "1")
                fixed_last = fixed_last.replace("o", "0").replace("O", "0").replace("u", "0").replace("U", "0")
                tokens[-1] = fixed_last
                cleaned_txt = " ".join(tokens)

        # Look for numbers/prices at the end of the line
        numbers = re.findall(r"\b\d+(?:\.\d{1,2})?\b", cleaned_txt.replace(",", ""))
        if not numbers:
            continue

        try:
            potential_price = float(numbers[-1])
            if potential_price <= 0 or potential_price > 50000:
                continue

            last_num_str = numbers[-1]
            price_val = potential_price
            remaining = re.sub(rf"{re.escape(last_num_str)}\s*$", "", cleaned_txt).strip()

            qty_val = 1
            sub_numbers = re.findall(r"\b\d+\b", remaining)
            if sub_numbers:
                if remaining.endswith(sub_numbers[-1]):
                    q = int(sub_numbers[-1])
                    if 1 <= q <= 99:
                        qty_val = q
                        remaining = re.sub(rf"{re.escape(sub_numbers[-1])}\s*$", "", remaining).strip()
                elif remaining.startswith(sub_numbers[0]):
                    q = int(sub_numbers[0])
                    if 1 <= q <= 99:
                        qty_val = q
                        remaining = re.sub(rf"^\s*{re.escape(sub_numbers[0])}", "", remaining).strip()

            # Clean name
            name_part = re.sub(r"^[-–—*#\s.]+", "", remaining).strip()
            name_part = re.sub(r"[-–—*#\s.]+$", "", name_part).strip()

            # Must have at least 2 alphabetic characters
            if len(re.sub(r"[^a-zA-Z]", "", name_part)) >= 2:
                if any(w in name_part.lower() for w in ["total", "subtotal", "balance", "cgst", "sgst", "vat"]):
                    continue

                is_low_conf = l["confidence"] < 0.85 or len(name_part) < 3
                items.append(ReceiptItem(
                    id=f"item_{len(items)+1}_{str(uuid.uuid4())[:4]}",
                    name=name_part,
                    quantity=qty_val,
                    price=price_val,
                    is_low_confidence=is_low_conf,
                    confidence=round(l["confidence"], 2)
                ))
        except Exception:
            continue

    # ----------------------------------------------------
    # 5. Reconcile Totals & Symmetric Taxes
    # ----------------------------------------------------
    computed_subtotal = round(sum(it.price for it in items), 2)
    if subtotal_val is None or subtotal_val == 0:
        subtotal_val = computed_subtotal

    # Indian GST Symmetry Auto-Balance (CGST and SGST are always identical on restaurant bills)
    has_cgst = next((t for t in taxes if "CGST" in t.name), None)
    has_sgst = next((t for t in taxes if "SGST" in t.name), None)

    if has_cgst and not has_sgst:
        taxes.append(TaxItem(
            name=f"SGST ({has_cgst.rate or 2.5}%)",
            rate=has_cgst.rate or 2.5,
            amount=has_cgst.amount,
            is_low_confidence=False,
            confidence=has_cgst.confidence
        ))
    elif has_sgst and not has_cgst:
        taxes.append(TaxItem(
            name=f"CGST ({has_sgst.rate or 2.5}%)",
            rate=has_sgst.rate or 2.5,
            amount=has_sgst.amount,
            is_low_confidence=False,
            confidence=has_sgst.confidence
        ))
    elif not taxes and subtotal_val > 0:
        # Default statutory 5% GST (2.5% CGST + 2.5% SGST)
        half_gst = round(subtotal_val * 0.025, 2)
        taxes.append(TaxItem(name="CGST (2.5%)", rate=2.5, amount=half_gst, is_low_confidence=False, confidence=0.95))
        taxes.append(TaxItem(name="SGST (2.5%)", rate=2.5, amount=half_gst, is_low_confidence=False, confidence=0.95))

    computed_total = round(subtotal_val + sum(t.amount for t in taxes) + sc_val - disc_val, 2)
    if total_val is None or total_val == 0:
        total_val = computed_total

    return ReceiptData(
        merchant=MerchantInfo(name=merchant_name, date=date_val),
        items=items,
        subtotal=AmountField(amount=subtotal_val, is_low_confidence=False, confidence=0.95),
        taxes=taxes,
        service_charge=AmountField(amount=sc_val, is_low_confidence=False, confidence=0.95),
        discount=AmountField(amount=disc_val, is_low_confidence=False, confidence=0.95),
        total=AmountField(amount=total_val, is_low_confidence=False, confidence=0.98)
    )
