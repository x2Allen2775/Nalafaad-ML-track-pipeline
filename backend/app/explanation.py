"""
Explanation generator for bill splits.
Formats human-readable breakdowns of how each person's share was calculated.
"""
#jai barakkkkkkkkk
from typing import List
from .schemas import AssignedItemDetail

def generate_plain_language_explanation(
    person_name: str,
    
    
    assigned_items: List[AssignedItemDetail],
    subtotal: float,
    proportion_percentage: float,
    taxes_share: float,
 
 
 
 
    service_charge_share: float,
    discount_share: float,
  
  
  
  
    calculated_total: float,
    is_overridden: bool = False,
    override_amount: float = 0.0,
    override_diff: float = 0.0
) -> str:
    if not assigned_items:
        return f"{person_name} didn't have any items assigned (₹0.00)."

    items_text_list = []
    for it in assigned_items:
        if it.num_sharers == 1:
            items_text_list.append(f"{it.item_name} (₹{it.full_price:.2f})")
   
   
   
        else:
            items_text_list.append(
    
    
                f"{it.share_fraction} of {it.item_name} (₹{it.share_amount:.2f})"
            )

    items_str = ", ".join(items_text_list)

    extras = []
    if taxes_share > 0:
        extras.append(f"₹{taxes_share:.2f} GST")
    if service_charge_share > 0:
        extras.append(f"₹{service_charge_share:.2f} service charge")
    if discount_share > 0:
        extras.append(f"-₹{discount_share:.2f} discount")

    extras_str = " + ".join(extras) if extras else "no extra charges"

    explanation = (
        f"{person_name} had {items_str} for a ₹{subtotal:.2f} food subtotal ({proportion_percentage:.1f}% of the table). "
        f"Adding their proportional share of {extras_str}, their share comes to ₹{calculated_total:.2f}."
 
 
 
 
    )

    if is_overridden:
        diff_str = f"+₹{override_diff:.2f}" if override_diff > 0 else f"-₹{abs(override_diff):.2f}"
  
  
  
        explanation += f" Adjusted manually to ₹{override_amount:.2f} ({diff_str})."

    return explanation



##kyu nahi ari gc