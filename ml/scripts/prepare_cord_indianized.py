"""
Script to prepare and adapt the CORD dataset for Indian Restaurant Bills.
Domain adaptation steps:
- Injects Indian dishes and beverage names
- Injects Indian restaurant merchants
- Splits generic taxes into CGST (2.5%) + SGST (2.5%) or GST (5%/18%)
- Adds realistic Service Charge (5-10%) and discounts
- Converts ground truth into standardized Target Extraction Schema JSON
"""

import os
import json
import random
import re
import glob
from typing import Dict, Any, List, Optional
import pandas as pd
from PIL import Image
import io

INDIAN_MERCHANTS = [
    "Punjab Grill & Bar",
    "Bawarchi Biryani House",
    "Saravanaa Bhavan",
    "Haldiram's Pure Veg",
    "Empire Restaurant & Cafe",
    "Barbeque Nation",
    "Paradise Food Court",
    "Karim's Mughal Delights",
    "Toit Brewpub & Kitchen",
    "The Fatty Bao Asian Gastro",
    "Chai Point & Snacks",
    "Sagar Ratna Express",
    "Ananda Bhavan Grand",
    "Social Offline Cafe",
    "Mainland China Bistro"
]

INDIAN_DISHES = [
    {"name": "Paneer Butter Masala", "price_range": (240, 380)},
    {"name": "Butter Chicken", "price_range": (320, 480)},
    {"name": "Dal Makhani", "price_range": (200, 320)},
    {"name": "Garlic Naan", "price_range": (60, 95)},
    {"name": "Butter Naan", "price_range": (50, 80)},
    {"name": "Tandoori Roti", "price_range": (30, 50)},
    {"name": "Hyderabadi Chicken Biryani", "price_range": (280, 420)},
    {"name": "Veg Dum Biryani", "price_range": (220, 320)},
    {"name": "Jeera Rice", "price_range": (140, 200)},
    {"name": "Crispy Chilli Paneer", "price_range": (220, 310)},
    {"name": "Chicken Tikka Kebab", "price_range": (290, 390)},
    {"name": "Masala Dosa", "price_range": (110, 170)},
    {"name": "Idli Vada Combo", "price_range": (90, 140)},
    {"name": "Gulab Jamun (2 pcs)", "price_range": (80, 130)},
    {"name": "Rasmalai", "price_range": (90, 150)},
    {"name": "Masala Chai", "price_range": (40, 70)},
    {"name": "Fresh Lime Soda", "price_range": (60, 110)},
    {"name": "Cold Coffee with Ice Cream", "price_range": (120, 180)},
    {"name": "Mango Lassi", "price_range": (90, 140)},
    {"name": "Mineral Water (1L)", "price_range": (30, 50)}
]

def clean_price(val: Any) -> Optional[float]:
    if val is None:
        return None
    s = str(val).strip().replace("₹", "").replace("Rs.", "").replace("Rs", "").replace("$", "")
    # Remove unwanted punctuation except dots and commas
    s = re.sub(r"[^\d.,\-]", "", s)
    if not s:
        return None
    # Handle European / Indonesian format (e.g. 60.000 or 24,000)
    if "." in s and "," in s:
        # e.g. 1,234.56 or 1.234,56
        if s.rfind(".") > s.rfind(","):
            s = s.replace(",", "")
        else:
            s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." not in s:
        # Could be thousand separator (24,000) or decimal (24,50)
        parts = s.split(",")
        if len(parts[-1]) == 3:
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    elif "." in s and "," not in s:
        parts = s.split(".")
        if len(parts) > 1 and len(parts[-1]) == 3 and len(parts[0]) <= 3:
            # e.g. 60.000 -> 60000 or scaled to 60.00
            s = "".join(parts)
    try:
        val_f = float(s)




        # Normalize excessively high Indonesian Rupiah amounts down to Indian Rupee scale
        
        if val_f > 10000:
            val_f = round(val_f / 100.0, 2)
       
       
       
        elif val_f > 2000:
            val_f = round(val_f / 10.0, 2)
      
        return round(abs(val_f), 2)
    except ValueError:
        return None




def indianize_record(gt_parse: Dict[str, Any], record_idx: int) -> Dict[str, Any]:
    """
    Transforms CORD gt_parse into the SplitSnap Target Extraction Schema,
    substituting Indian dish names, restaurant names, and GST / Service Charge.
    """




    rng = random.Random(record_idx + 42)
    merchant_name = rng.choice(INDIAN_MERCHANTS)
    date_str = f"2026-09-{rng.randint(10, 28):02d}"




    raw_menu = gt_parse.get("menu", [])
    if isinstance(raw_menu, dict):
        raw_menu = [raw_menu]





    extracted_items = []
    dish_pool = list(INDIAN_DISHES)
    rng.shuffle(dish_pool)

    for i, item in enumerate(raw_menu):
      
        dish_info = dish_pool[i % len(dish_pool)]
        item_name = dish_info["name"]

        # Parse quantity



        cnt = item.get("cnt") or item.get("sub_cnt") or "1"
        try:
       
            qty_clean = re.sub(r"[^\d]", "", str(cnt))
            qty = int(qty_clean) if qty_clean else 1
        except Exception:
            qty = 1
        qty = max(1, min(qty, 10))

        # Parse or assign price
        p = clean_price(item.get("price"))
        if p is None or p <= 0:

            p = float(rng.randint(dish_info["price_range"][0], dish_info["price_range"][1]))
        else:

            # Constrain to sensible Indian restaurant price range
            if p < 25:
                p = float(rng.randint(dish_info["price_range"][0], dish_info["price_range"][1]))
            elif p > 1500:
                p = round(p / 10.0, 2)





        # Calculate confidence scores
        confidence = round(rng.uniform(0.92, 0.99), 2)

        # Introduce a few low confidence items to test user verification


        is_low = False
        if rng.random() < 0.15:
            confidence = round(rng.uniform(0.68, 0.83), 2)
            is_low = True

        extracted_items.append({



            "name": item_name,

            "quantity": qty,
            "price": round(p * qty, 2),
            "is_low_confidence": is_low,
            "confidence": confidence
        })

    if not extracted_items:







        # Fallback default items
        for i in range(rng.randint(2, 4)):
            dish = dish_pool[i]
            qty = rng.randint(1, 2)
            pr = float(rng.randint(dish["price_range"][0], dish["price_range"][1])) * qty
            extracted_items.append({
                "name": dish["name"],
                "quantity": qty,
                "price": round(pr, 2),
                "is_low_confidence": False,
                "confidence": 0.96
            })


    subtotal = round(sum(it["price"] for it in extracted_items), 2)

    # Indian Tax System: 5% GST split into CGST (2.5%) and SGST (2.5%)
    cgst_rate = 2.5
    sgst_rate = 2.5
    cgst_amount = round(subtotal * (cgst_rate / 100.0), 2)
    sgst_amount = round(subtotal * (sgst_rate / 100.0), 2)

    # Optional Service Charge (5% to 8%)
    has_sc = rng.random() > 0.35
    sc_amount = round(subtotal * 0.05, 2) if has_sc else 0.0


    # Optional Discount
    has_discount = rng.random() > 0.75
    discount_amount = round(subtotal * 0.10, 2) if has_discount else 0.0

    total = round(subtotal + cgst_amount + sgst_amount + sc_amount - discount_amount, 2)

    result = {

        "merchant": {
            "name": merchant_name,
            "date": date_str
        },
        "items": extracted_items,
        "subtotal": {
            "amount": subtotal,
            "is_low_confidence": False,
            "confidence": 0.98

        },
        "taxes": [
            {
                "name": f"CGST ({cgst_rate}%)",
                "rate": cgst_rate,
                "amount": cgst_amount,
                "is_low_confidence": False,
                "confidence": 0.95

            },
            {
                "name": f"SGST ({sgst_rate}%)",
                "rate": sgst_rate,
                "amount": sgst_amount,
                "is_low_confidence": False,
                "confidence": 0.95

            }
        ],
        "service_charge": {
            "amount": sc_amount,
            "is_low_confidence": False,

            "confidence": 0.94 if has_sc else 1.0
        },
        "discount": {

            "amount": discount_amount,
            "is_low_confidence": False,
            "confidence": 0.97 if has_discount else 1.0
        },
        "total": {
            "amount": total,

            "is_low_confidence": False,
            "confidence": 0.99
        }
    }

    return result

def to_donut_format(schema_json: Dict[str, Any]) -> str:
    """
    Serializes schema_json into the Donut model token sequence format.

    """
    items_xml = ""
    for item in schema_json["items"]:
        items_xml += f"<s_item><s_name>{item['name']}</s_name><s_qty>{item['quantity']}</s_qty><s_price>{item['price']}</s_price></s_item>"


    taxes_xml = ""
    for tax in schema_json["taxes"]:

        taxes_xml += f"<s_tax><s_name>{tax['name']}</s_name><s_amount>{tax['amount']}</s_amount></s_tax>"


    seq = (
        f"<s_splitsnap>"


        f"<s_merchant>{schema_json['merchant']['name']}</s_merchant>"
        f"<s_date>{schema_json['merchant'].get('date', '')}</s_date>"
        f"<s_items>{items_xml}</s_items>"
        f"<s_subtotal>{schema_json['subtotal']['amount']}</s_subtotal>"
        f"<s_taxes>{taxes_xml}</s_taxes>"
        f"<s_service_charge>{schema_json['service_charge']['amount']}</s_service_charge>"
        f"<s_discount>{schema_json['discount']['amount']}</s_discount>"

        f"<s_total>{schema_json['total']['amount']}</s_total>"
        f"</s_splitsnap>"
    )
    return seq

def process_parquet_files(cord_dir: str, output_dir: str, max_samples: int = 500):
    os.makedirs(output_dir, exist_ok=True)

    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)


    files = glob.glob(os.path.join(cord_dir, "*.parquet"))
    print(f"Found {len(files)} parquet files in {cord_dir}")

    records = []
    processed_count = 0


    for file_path in sorted(files):
        print(f"Reading {file_path}...")
        df = pd.read_parquet(file_path)
        for i in range(len(df)):
            if processed_count >= max_samples:
                break
            try:
                row = df.iloc[i]
                gt = json.loads(row["ground_truth"])

                gt_parse = gt.get("gt_parse", {})

                indianized = indianize_record(gt_parse, processed_count)
                donut_seq = to_donut_format(indianized)


                # Save image
                img_data = row["image"]
                img_filename = f"receipt_{processed_count:05d}.jpg"

                img_path = os.path.join(images_dir, img_filename)

                if isinstance(img_data, dict) and "bytes" in img_data:
                    with open(img_path, "wb") as f_img:

                        f_img.write(img_data["bytes"])
                elif isinstance(img_data, bytes):
                    with open(img_path, "wb") as f_img:
                        f_img.write(img_data)


                record = {
                    "id": f"splitsnap_{processed_count:05d}",
    
                    "image_file": img_filename,
                    "target_json": indianized,
                    "donut_sequence": donut_seq
                }
                records.append(record)
                processed_count += 1
            except Exception as e:
                # print(f"Error processing record {i}: {e}")
                continue

        if processed_count >= max_samples:
            break

    # Save to jsonl
    
    
    jsonl_path = os.path.join(output_dir, "indianized_dataset.jsonl")
    with open(jsonl_path, "w") as f:
    
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"Successfully processed {len(records)} records saved to {jsonl_path}")

if __name__ == "__main__":

    import sys
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    cord_path = os.path.join(base_dir, "cord")
    out_path = os.path.join(base_dir, "ml", "data", "processed")
    process_parquet_files(cord_path, out_path, max_samples=150)


#jaiiiiiiiiiii BARAKKKKKKKK