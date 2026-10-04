"""
Unit tests for Proportional Apportionment Algorithm and Explanation Generator.
Validates proportional fairness, manual adjustments, and explanation structure.
"""

import unittest
from backend.app.schemas import (
    ReceiptData,
    ReceiptItem,
    TaxItem,
    AmountField,
    MerchantInfo,
    Person,
    SplitCalculationRequest
)
from backend.app.apportionment import calculate_proportional_split

def test_proportional_split_basic():
    # Setup receipt:
    # Item 1: Paneer Butter Masala (₹300) -> Rahul only
    # Item 2: Butter Naan (₹100) -> Priya only
    # Item 3: Crispy Corn (₹200) -> Rahul and Priya (1/2 each = ₹100 each)
    # Total Subtotal = ₹600. Rahul = 300 + 100 = 400 (66.67%). Priya = 100 + 100 = 200 (33.33%).
    # Tax: CGST 2.5% (₹15), SGST 2.5% (₹15). Total Tax = ₹30.
    # Service Charge: ₹60.
    # Grand Total = ₹690.
    receipt = ReceiptData(
        merchant=MerchantInfo(name="Punjab Grill"),
        items=[
            ReceiptItem(id="item_1", name="Paneer Butter Masala", price=300.0),
            ReceiptItem(id="item_2", name="Butter Naan", price=100.0),
            ReceiptItem(id="item_3", name="Crispy Corn", price=200.0),
        ],
        subtotal=AmountField(amount=600.0),
        taxes=[
            TaxItem(name="CGST (2.5%)", amount=15.0),
            TaxItem(name="SGST (2.5%)", amount=15.0),
        ],
        service_charge=AmountField(amount=60.0),
        discount=AmountField(amount=0.0),
        total=AmountField(amount=690.0)
    )

    people = [
        Person(id="p1", name="Rahul"),
        Person(id="p2", name="Priya")
    ]

    assignments = {
        "item_1": ["p1"],
        "item_2": ["p2"],
        "item_3": ["p1", "p2"]
    }

    req = SplitCalculationRequest(
        receipt=receipt,
        people=people,
        item_assignments=assignments
    )

    resp = calculate_proportional_split(req)

    assert resp.global_subtotal == 600.0
    assert resp.total_taxes == 30.0
    assert resp.total_service_charge == 60.0

    rahul_split = next(s for s in resp.splits if s.person_id == "p1")
    priya_split = next(s for s in resp.splits if s.person_id == "p2")

    # Rahul subtotal: 300 + 100 = 400
    assert rahul_split.subtotal == 400.0
    assert round(rahul_split.proportion_percentage, 1) == 66.7
    # Rahul taxes share: 30 * (400/600) = 20.0
    assert rahul_split.taxes_share == 20.0
    # Rahul service charge: 60 * (400/600) = 40.0
    assert rahul_split.service_charge_share == 40.0
    # Rahul calculated total: 400 + 20 + 40 = 460.0
    assert rahul_split.calculated_total == 460.0

    # Priya subtotal: 100 + 100 = 200
    assert priya_split.subtotal == 200.0
    assert round(priya_split.proportion_percentage, 1) == 33.3
    # Priya taxes share: 30 * (200/600) = 10.0
    assert priya_split.taxes_share == 10.0
    # Priya service charge: 60 * (200/600) = 20.0
    assert priya_split.service_charge_share == 20.0
    # Priya calculated total: 200 + 10 + 20 = 230.0
    assert priya_split.calculated_total == 230.0

    # Total check
    assert rahul_split.calculated_total + priya_split.calculated_total == 690.0

    # Check explanation is generated
    assert "Rahul" in rahul_split.explanation
    assert "Paneer Butter Masala" in rahul_split.explanation
    assert "Crispy Corn" in rahul_split.explanation
    assert "460.00" in rahul_split.explanation

def test_manual_override():
    receipt = ReceiptData(
        items=[ReceiptItem(id="i1", name="Thali", price=500.0)],
        subtotal=AmountField(amount=500.0),
        taxes=[TaxItem(name="GST", amount=25.0)],
        total=AmountField(amount=525.0)
    )
    people = [Person(id="p1", name="Amit")]
    assignments = {"i1": ["p1"]}
    overrides = {"p1": 550.0}

    req = SplitCalculationRequest(
        receipt=receipt,
        people=people,
        item_assignments=assignments,
        manual_overrides=overrides
    )

    resp = calculate_proportional_split(req)
    amit_split = resp.splits[0]
    assert amit_split.is_overridden is True
    assert amit_split.calculated_total == 525.0
    assert amit_split.final_total == 550.0
    assert amit_split.override_difference == 25.0
    assert "Adjusted manually" in amit_split.explanation

if __name__ == "__main__":
    test_proportional_split_basic()
    test_manual_override()
    print("All apportionment tests passed!")
