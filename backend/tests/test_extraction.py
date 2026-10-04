"""
Tests for Neural OCR and Semantic Receipt Extraction Engine.
"""
from PIL import Image
from backend.app.inference import engine

def test_real_receipt_extraction():
    img_path = "sample_receipts/test_real_receipt.png"
    receipt = engine.extract_from_image(Image.open(img_path))
    
    assert "SARAVANAA BHAVAN" in receipt.merchant.name
    assert receipt.merchant.date == "2026-10-04"
    assert len(receipt.items) == 3
    
    item_names = [it.name for it in receipt.items]
    assert any("Masala Dosa" in name for name in item_names)
    assert any("Filter Coffee" in name for name in item_names)
    assert any("Idli Vada Combo" in name for name in item_names)
    
    assert receipt.subtotal.amount == 370.0
    assert receipt.total.amount == 407.0
    print("Receipt extraction tests passed successfully!")

if __name__ == "__main__":
    test_real_receipt_extraction()
