import { ReceiptData } from "./types";

export interface PresetOption {
  id: string;
  title: string;
  description: string;
  badge: string;
  data: ReceiptData;
}

export const SAMPLE_PRESETS: PresetOption[] = [
  {
    id: "punjab_grill",
    title: "Punjab Grill & Bar",
    description: "North Indian dinner with CGST, SGST & Service Charge",
    badge: "5 Items · ₹1,793",
    data: {
      merchant: {
        name: "Punjab Grill & Bar",
        date: "2026-10-03"
      },
      items: [
        {
          id: "item_1",
          name: "Paneer Butter Masala",
          quantity: 1,
          price: 380.0,
          is_low_confidence: false,
          confidence: 0.98
        },
        {
          id: "item_2",
          name: "Butter Chicken",
          quantity: 1,
          price: 480.0,
          is_low_confidence: false,
          confidence: 0.97
        },
        {
          id: "item_3",
          name: "Dal Makhani",
          quantity: 1,
          price: 320.0,
          is_low_confidence: false,
          confidence: 0.95
        },
        {
          id: "item_4",
          name: "Garlic Naan (Basket)",
          quantity: 3,
          price: 270.0,
          is_low_confidence: true,
          confidence: 0.76
        },
        {
          id: "item_5",
          name: "Jeera Rice",
          quantity: 1,
          price: 180.0,
          is_low_confidence: false,
          confidence: 0.96
        }
      ],
      subtotal: {
        amount: 1630.0,
        is_low_confidence: false,
        confidence: 0.99
      },
      taxes: [
        {
          name: "CGST (2.5%)",
          rate: 2.5,
          amount: 40.75,
          is_low_confidence: false,
          confidence: 0.95
        },
        {
          name: "SGST (2.5%)",
          rate: 2.5,
          amount: 40.75,
          is_low_confidence: false,
          confidence: 0.95
        }
      ],
      service_charge: {
        amount: 81.50,
        is_low_confidence: true,
        confidence: 0.79
      },
      discount: {
        amount: 0.0,
        is_low_confidence: false,
        confidence: 1.0
      },
      total: {
        amount: 1793.0,
        is_low_confidence: false,
        confidence: 0.99
      }
    }
  },
  {
    id: "bawarchi_biryani",
    title: "Bawarchi Biryani House",
    description: "Biryani feast with kebabs, dessert & discount applied",
    badge: "4 Items · ₹1,330",
    data: {
      merchant: {
        name: "Bawarchi Biryani House",
        date: "2026-10-02"
      },
      items: [
        {
          id: "item_1",
          name: "Special Mutton Biryani",
          quantity: 2,
          price: 760.0,
          is_low_confidence: false,
          confidence: 0.98
        },
        {
          id: "item_2",
          name: "Chicken Tikka Kebab",
          quantity: 1,
          price: 340.0,
          is_low_confidence: false,
          confidence: 0.96
        },
        {
          id: "item_3",
          name: "Double Ka Meetha",
          quantity: 2,
          price: 180.0,
          is_low_confidence: true,
          confidence: 0.74
        },
        {
          id: "item_4",
          name: "Thums Up (Can)",
          quantity: 3,
          price: 120.0,
          is_low_confidence: false,
          confidence: 0.94
        }
      ],
      subtotal: {
        amount: 1400.0,
        is_low_confidence: false,
        confidence: 0.99
      },
      taxes: [
        {
          name: "CGST (2.5%)",
          rate: 2.5,
          amount: 35.0,
          is_low_confidence: false,
          confidence: 0.95
        },
        {
          name: "SGST (2.5%)",
          rate: 2.5,
          amount: 35.0,
          is_low_confidence: false,
          confidence: 0.95
        }
      ],
      service_charge: {
        amount: 0.0,
        is_low_confidence: false,
        confidence: 1.0
      },
      discount: {
        amount: 140.0,
        is_low_confidence: false,
        confidence: 0.97
      },
      total: {
        amount: 1330.0,
        is_low_confidence: false,
        confidence: 0.99
      }
    }
  },
  {
    id: "saravanaa_bhavan",
    title: "Saravanaa Bhavan",
    description: "South Indian traditional breakfast with filter coffee",
    badge: "3 Items · ₹598.50",
    data: {
      merchant: {
        name: "Saravanaa Bhavan",
        date: "2026-10-04"
      },
      items: [
        {
          id: "item_1",
          name: "Ghee Roast Masala Dosa",
          quantity: 2,
          price: 240.0,
          is_low_confidence: false,
          confidence: 0.98
        },
        {
          id: "item_2",
          name: "Idli Vada Combo",
          quantity: 2,
          price: 180.0,
          is_low_confidence: false,
          confidence: 0.95
        },
        {
          id: "item_3",
          name: "South Indian Filter Coffee",
          quantity: 3,
          price: 150.0,
          is_low_confidence: false,
          confidence: 0.97
        }
      ],
      subtotal: {
        amount: 570.0,
        is_low_confidence: false,
        confidence: 0.99
      },
      taxes: [
        {
          name: "GST (5%)",
          rate: 5.0,
          amount: 28.50,
          is_low_confidence: false,
          confidence: 0.96
        }
      ],
      service_charge: {
        amount: 0.0,
        is_low_confidence: false,
        confidence: 1.0
      },
      discount: {
        amount: 0.0,
        is_low_confidence: false,
        confidence: 1.0
      },
      total: {
        amount: 598.50,
        is_low_confidence: false,
        confidence: 0.99
      }
    }
  }
];
