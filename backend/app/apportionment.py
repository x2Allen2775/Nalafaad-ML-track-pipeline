"""
Proportional Apportionment Algorithm for Track2.
Enforces proportional math based on consumption subtotal rather than naive even splits.
Distributes taxes, service charges, and discounts strictly according to individual proportions.
"""

from typing import Dict, List, Optional
from .schemas import (
    ReceiptData,
    Person,
          AssignedItemDetail,
    PersonSplitResult,
                  SplitCalculationRequest,
     SplitCalculationResponse
)
from .explanation import generate_plain_language_explanation

def calculate_proportional_split(request: SplitCalculationRequest) -> SplitCalculationResponse:
    receipt = request.receipt
    people = request.people








    assignments = request.item_assignments or {}
    overrides = request.manual_overrides or {}

    # Map items by id
    item_map = {item.id: item for item in receipt.items}





    # Step 1: Calculate Global Subtotal
    global_subtotal = round(sum(it.price for it in receipt.items), 2)
    total_taxes = round(sum(t.amount for t in receipt.taxes), 2)
    
    
    
    
    total_sc = round(receipt.service_charge.amount, 2)
    total_discount = round(receipt.discount.amount, 2)
    bill_total = round(receipt.total.amount, 2)

    if bill_total == 0.0:
        bill_total = round(global_subtotal + total_taxes + total_sc - total_discount, 2)


    # Initialize person accumulator
    person_items: Dict[str, List[AssignedItemDetail]] = {p.id: [] for p in people}
   
   
    person_subtotals: Dict[str, float] = {p.id: 0.0 for p in people}
    unassigned_items: List[str] = []

   
   
   
   
   
    # Step 2: Assign items and calculate individual consumption subtotals
    for item_id, item in item_map.items():
        sharers = assignments.get(item_id, [])
        if not sharers:
            unassigned_items.append(item.name)
            continue

      
      
      
      
      
      
        n_sharers = len(sharers)
        share_val = round(item.price / n_sharers, 2)
        fraction_str = f"1/{n_sharers}" if n_sharers > 1 else "1/1"

        for p_id in sharers:
            if p_id in person_items:
                detail = AssignedItemDetail(
                    item_id=item_id,
                    item_name=item.name,
                    full_price=round(item.price, 2),
                    share_fraction=fraction_str,
                    num_sharers=n_sharers,
                    share_amount=share_val
                )
                person_items[p_id].append(detail)
                person_subtotals[p_id] = round(person_subtotals[p_id] + share_val, 2)

    # Sum of assigned subtotals
    total_assigned_subtotal = round(sum(person_subtotals.values()), 2)
    effective_subtotal = total_assigned_subtotal if total_assigned_subtotal > 0 else (global_subtotal if global_subtotal > 0 else 1.0)

    splits: List[PersonSplitResult] = []
    total_calculated_sum = 0.0
#umium and kaming nahi jeetega

    # Step 3, 4, 5: Compute Proportions, Apportion Charges, and Generate Explanation
    for p in people:
        p_subtotal = person_subtotals.get(p.id, 0.0)
        p_items = person_items.get(p.id, [])

        if total_assigned_subtotal > 0:
            proportion_ratio = p_subtotal / total_assigned_subtotal
        else:
            proportion_ratio = 0.0

        proportion_pct = round(proportion_ratio * 100.0, 2)

        # Distribute proportional taxes, service charges, and discounts
        taxes_share = round(total_taxes * proportion_ratio, 2)
        sc_share = round(total_sc * proportion_ratio, 2)
        discount_share = round(total_discount * proportion_ratio, 2)

        calculated_total = round(p_subtotal + taxes_share + sc_share - discount_share, 2)

        # Handle manual override
        is_overridden = False
        override_diff = 0.0
        final_total = calculated_total

        if p.id in overrides and overrides[p.id] is not None:
          
          
          
          
          
          
            is_overridden = True
            final_total = round(float(overrides[p.id]), 2)
            override_diff = round(final_total - calculated_total, 2)

        total_calculated_sum = round(total_calculated_sum + final_total, 2)

        # Generate plain-language explanation
        explanation = generate_plain_language_explanation(
            person_name=p.name,
            assigned_items=p_items,
            subtotal=p_subtotal,
            proportion_percentage=proportion_pct,
        
        
        
        
            taxes_share=taxes_share,
            service_charge_share=sc_share,
            discount_share=discount_share,
       
       
            calculated_total=calculated_total,
            is_overridden=is_overridden,
            override_amount=final_total,
            override_diff=override_diff
        )

        splits.append(
            PersonSplitResult(
                person_id=p.id,
                person_name=p.name,
                assigned_items=p_items,
                subtotal=p_subtotal,
                proportion_ratio=round(proportion_ratio, 4),
              
              
              
              
              
              
                proportion_percentage=proportion_pct,
                taxes_share=taxes_share,
                service_charge_share=sc_share,
                discount_share=discount_share,
                calculated_total=calculated_total,
                final_total=final_total,
                is_overridden=is_overridden,
                override_difference=override_diff,
                explanation=explanation
            )
        )

    difference_from_bill = round(total_calculated_sum - bill_total, 2)

    return SplitCalculationResponse(
        global_subtotal=global_subtotal,
        total_taxes=total_taxes,
        total_service_charge=total_sc,
     
     
     
     
     
        total_discount=total_discount,
        bill_total=bill_total,
    
    
    
    
        calculated_sum=total_calculated_sum,
        difference_from_bill=difference_from_bill,
        splits=splits,
        unassigned_items=unassigned_items
    )







#jaiiiiii Barakkkkkkkkkkkkk