"""
Semantic Receipt Parser for SplitSnap.
Converts raw OCR tokens into structured ReceiptData schemas with line items,
merchant details, tax breakdowns, and confidence flags.
"""
import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from .schemas import ReceiptData, ReceiptItem, TaxItem, AmountField, MerchantInfo

IGNORE_HEADER_WORDS = {
    "tax invoice", "retail invoice", "bill", "receipt", "order", "table", "waiter",
    "stn", "station", "server", "cashier", "item", "qty", "rate", "price", "amount",
    "description", "pax", "covers", "guest", "token", "pos", "terminal"
}

IGNORE_FOOTER_WORDS = {
    "thank you", "visit again", "have a nice day", "powered by", "wifi", "password",
    "customer copy", "merchant copy", "signature", "terms", "conditions", "gstin", "fssai"
}

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
    Transforms clustered OCR lines into structured ReceiptData.
    """
    merchant_name = "Restaurant"
    date_val = datetime.now().strftime("%Y-%m-%d")
    items: List[ReceiptItem] = []
    taxes: List[TaxItem] = []
    sc_val: float = 0.0
    disc_val: float = 0.0
    subtotal_val: Optional[float] = None
    total_val: Optional[float] = None

    # Track line indices already consumed
    consumed_indices = set()

    # 1. Detect Merchant Name (Usually topmost prominent line)
    for idx, l in enumerate(lines[:6]):
        txt = l["text"].strip()
        lower = txt.lower()
        if any(h in lower for h in IGNORE_HEADER_WORDS) or any(f in lower for f in IGNORE_FOOTER_WORDS):
            continue
        # Check if line contains digits only or dates
        if re.search(r"^\d+$", txt) or re.search(r"\d{1,2}[/-]\d{1,2}", txt):
            continue
        # Must have at least some alphabetic characters
        if re.search(r"[a-zA-Z]{3,}", txt):
            merchant_name = txt
            consumed_indices.add(idx)
            break

    # 2. Detect Date
    date_pattern = r"(\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b)"
    for idx, l in enumerate(lines[:12]):
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

    # 3. Detect Taxes, Surcharges, Subtotal, and Totals
    for idx, l in enumerate(lines):
        txt = l["text"].strip()
        lower = txt.lower()

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

        # Taxes: CGST, SGST, IGST, VAT, GST
        tax_kw = ["cgst", "sgst", "igst", "vat", "gst"]
        matched_tax = next((kw for kw in tax_kw if kw in lower), None)
        if matched_tax:
            # Extract rate if present (e.g. 2.5% or 5%)
            rate_match = re.search(r"(\d+(?:\.\d+)?)\s*%", txt)
            rate = float(rate_match.group(1)) if rate_match else None
            amt_match = re.findall(r"\d+(?:\.\d{1,2})?", txt.replace(",", ""))
            if amt_match:
                try:
                    t_amt = float(amt_match[-1])
                    name = f"{matched_tax.upper()}" + (f" ({rate}%)" if rate else "")
                    taxes.append(TaxItem(
                        name=name,
                        rate=rate,
                        amount=t_amt,
                        is_low_confidence=l["confidence"] < 0.85,
                        confidence=round(l["confidence"], 2)
                    ))
                    consumed_indices.add(idx)
                    continue
                except ValueError:
                    pass

        # Service Charge
        if "service charge" in lower or "service fee" in lower or re.search(r"\bsc\b", lower):
            amt_match = re.findall(r"\d+(?:\.\d{1,2})?", txt.replace(",", ""))
            if amt_match:
                try:
                    sc_val = float(amt_match[-1])
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

    # 4. Extract Line Items
    # Scan through remaining non-consumed lines
    for idx, l in enumerate(lines):
        if idx in consumed_indices:
            continue
        txt = l["text"].strip()
        lower = txt.lower()

        # Skip headers, footers, dates, and separator lines
        if any(h in lower for h in IGNORE_HEADER_WORDS) or any(f in lower for f in IGNORE_FOOTER_WORDS):
            continue
        if "date" in lower or "time" in lower or re.search(r"\d{1,2}[/-]\d{1,2}", txt):
            continue
        if re.search(r"^[-=_*#\s.]+$", txt):
            continue

        # Look for numbers/prices at the end of the line
        # Common line formats:
        # "Paneer Butter Masala 1 320.00"
        # "2 Butter Naan 120.00"
        # "Filter Coffee 80.00"
        numbers = re.findall(r"\b\d+(?:\.\d{1,2})?\b", txt.replace(",", ""))
        if not numbers:
            continue

        price_val = None
        qty_val = 1
        name_part = txt

        # Check if last number is a valid price (> 0)
        try:
            potential_price = float(numbers[-1])
            if potential_price <= 0 or potential_price > 50000:
                continue

            # Remove price string from line
            last_num_str = numbers[-1]
            price_val = potential_price

            # Remove the price from the end of the text
            remaining = re.sub(rf"{re.escape(last_num_str)}\s*$", "", txt).strip()

            # Check if there is an integer quantity remaining
            sub_numbers = re.findall(r"\b\d+\b", remaining)
            if sub_numbers:
                # If quantity is right at the end of remaining: "Paneer Masala 2"
                if remaining.endswith(sub_numbers[-1]):
                    q = int(sub_numbers[-1])
                    if 1 <= q <= 99:
                        qty_val = q
                        remaining = re.sub(rf"{re.escape(sub_numbers[-1])}\s*$", "", remaining).strip()
                # Or at the start: "2 Paneer Masala"
                elif remaining.startswith(sub_numbers[0]):
                    q = int(sub_numbers[0])
                    if 1 <= q <= 99:
                        qty_val = q
                        remaining = re.sub(rf"^\s*{re.escape(sub_numbers[0])}", "", remaining).strip()

            # Clean name
            name_part = re.sub(r"^[-–—*#\s.]+", "", remaining).strip()
            name_part = re.sub(r"[-–—*#\s.]+$", "", name_part).strip()

            # Must have at least 2 characters of letters
            if len(name_part) >= 2 and re.search(r"[a-zA-Z]", name_part):
                # Don't add total/subtotal as an item if keyword got caught
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

    # 5. Reconcile Totals & Subtotals
    computed_subtotal = round(sum(it.price for it in items), 2)
    if subtotal_val is None or subtotal_val == 0:
        subtotal_val = computed_subtotal

    # If taxes were not explicitly found, check standard 5% GST (2.5% CGST + 2.5% SGST)
    if not taxes and subtotal_val > 0:
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
