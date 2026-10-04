export interface ReceiptItem {
  id: string;
  name: string;
  quantity: number;
  price: number;
  is_low_confidence: boolean;
  confidence: number;
}

export interface TaxItem {
  name: string;
  rate?: number;
  amount: number;
  is_low_confidence: boolean;
  confidence: number;
}

export interface AmountField {
  amount: number;
  is_low_confidence: boolean;
  confidence: number;
}

export interface MerchantInfo {
  name: string;
  date?: string;
}

export interface ReceiptData {
  merchant: MerchantInfo;
  items: ReceiptItem[];
  subtotal: AmountField;
  taxes: TaxItem[];
  service_charge: AmountField;
  discount: AmountField;
  total: AmountField;
}

export interface Person {
  id: string;
  name: string;
  avatarColor: string;
}

export interface AssignedItemDetail {
  item_id: string;
  item_name: string;
  full_price: number;
  share_fraction: string;
  num_sharers: number;
  share_amount: number;
}

export interface PersonSplitResult {
  person_id: string;
  person_name: string;
  assigned_items: AssignedItemDetail[];
  subtotal: number;
  proportion_ratio: number;
  proportion_percentage: number;
  taxes_share: number;
  service_charge_share: number;
  discount_share: number;
  calculated_total: number;
  final_total: number;
  is_overridden: boolean;
  override_difference: number;
  explanation: string;
}

export interface SplitCalculationResponse {
  global_subtotal: number;
  total_taxes: number;
  total_service_charge: number;
  total_discount: number;
  bill_total: number;
  calculated_sum: number;
  difference_from_bill: number;
  splits: PersonSplitResult[];
  unassigned_items: string[];
}
