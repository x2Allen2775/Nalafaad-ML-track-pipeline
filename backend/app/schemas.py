"""
Pydantic Schemas for Receipts, Apportionment, and Explanations.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class ReceiptItem(BaseModel):
    id: str
    name: str
    quantity: int = 1
    price: float
    is_low_confidence: bool = False
    confidence: float = 1.0

class TaxItem(BaseModel):
    name: str
    rate: Optional[float] = None
    amount: float
    is_low_confidence: bool = False
    confidence: float = 1.0

class AmountField(BaseModel):
    amount: float
    is_low_confidence: bool = False
    confidence: float = 1.0

class MerchantInfo(BaseModel):
    name: str = "Restaurant"
    date: Optional[str] = None

class ReceiptData(BaseModel):
    merchant: MerchantInfo = Field(default_factory=MerchantInfo)
    items: List[ReceiptItem] = []
    subtotal: AmountField = Field(default_factory=lambda: AmountField(amount=0.0))
    taxes: List[TaxItem] = []
    service_charge: AmountField = Field(default_factory=lambda: AmountField(amount=0.0))
    discount: AmountField = Field(default_factory=lambda: AmountField(amount=0.0))
    total: AmountField = Field(default_factory=lambda: AmountField(amount=0.0))

class Person(BaseModel):
    id: str
    name: str
    avatar_color: Optional[str] = None

class AssignedItemDetail(BaseModel):
    item_id: str
    item_name: str
    full_price: float
    share_fraction: str  # e.g. "1/1", "1/2", "1/3"
    num_sharers: int
    share_amount: float

class PersonSplitResult(BaseModel):
    person_id: str
    person_name: str
    assigned_items: List[AssignedItemDetail] = []
    subtotal: float
    proportion_ratio: float  # e.g. 0.452
    proportion_percentage: float  # e.g. 45.2%
    taxes_share: float
    service_charge_share: float
    discount_share: float
    calculated_total: float
    final_total: float
    is_overridden: bool = False
    override_difference: float = 0.0
    explanation: str

class SplitCalculationRequest(BaseModel):
    receipt: ReceiptData
    people: List[Person]
    item_assignments: Dict[str, List[str]]  # item_id -> list of person_ids
    manual_overrides: Optional[Dict[str, float]] = None  # person_id -> manual amount

class SplitCalculationResponse(BaseModel):
    global_subtotal: float
    total_taxes: float
    total_service_charge: float
    total_discount: float
    bill_total: float
    calculated_sum: float
    difference_from_bill: float
    splits: List[PersonSplitResult]
    unassigned_items: List[str] = []


##hostel hamara kesa ho, barak hostel jesa ho
