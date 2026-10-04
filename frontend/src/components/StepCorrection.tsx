"use client";

import React, { useState } from "react";
import {
  AlertCircle,
  Plus,
  Trash2,
  Check,
  CheckCircle2,
  Store,
  Calendar,
  ArrowRight
} from "lucide-react";
import { ReceiptData, ReceiptItem } from "../lib/types";

interface StepCorrectionProps {
  receipt: ReceiptData;
  onUpdateReceipt: (updated: ReceiptData) => void;
  onContinue: () => void;
}

export const StepCorrection: React.FC<StepCorrectionProps> = ({
  receipt,
  onUpdateReceipt,
  onContinue
}) => {
  const [data, setData] = useState<ReceiptData>(receipt);

  const updateItem = (index: number, patch: Partial<ReceiptItem>) => {
    const newItems = [...data.items];
    newItems[index] = { ...newItems[index], ...patch };
    recalcAndSave(newItems);
  };

  const addItem = () => {
    const newItem: ReceiptItem = {
      id: `item_${Date.now()}`,
      name: "New Item",
      quantity: 1,
      price: 100.0,
      is_low_confidence: false,
      confidence: 1.0
    };
    const newItems = [...data.items, newItem];
    recalcAndSave(newItems);
  };

  const removeItem = (index: number) => {
    const newItems = data.items.filter((_, i) => i !== index);
    recalcAndSave(newItems);
  };

  const confirmLowConfidenceField = (index: number) => {
    const newItems = [...data.items];
    newItems[index] = {
      ...newItems[index],
      is_low_confidence: false,
      confidence: 1.0
    };
    recalcAndSave(newItems);
  };

  const confirmServiceCharge = () => {
    const updated = {
      ...data,
      service_charge: {
        ...data.service_charge,
        is_low_confidence: false,
        confidence: 1.0
      }
    };
    setData(updated);
    onUpdateReceipt(updated);
  };

  const recalcAndSave = (items: ReceiptItem[]) => {
    const subtotal = Number(items.reduce((s, it) => s + (it.price || 0), 0).toFixed(2));
    const totalTaxes = Number(data.taxes.reduce((s, t) => s + (t.amount || 0), 0).toFixed(2));
    const sc = Number((data.service_charge.amount || 0).toFixed(2));
    const disc = Number((data.discount.amount || 0).toFixed(2));
    const total = Number((subtotal + totalTaxes + sc - disc).toFixed(2));

    const updated: ReceiptData = {
      ...data,
      items,
      subtotal: { ...data.subtotal, amount: subtotal },
      total: { ...data.total, amount: total }
    };
    setData(updated);
    onUpdateReceipt(updated);
  };

  const handleChargeChange = (field: "service_charge" | "discount", val: number) => {
    const subtotal = data.subtotal.amount;
    const totalTaxes = data.taxes.reduce((s, t) => s + t.amount, 0);
    const sc = field === "service_charge" ? val : data.service_charge.amount;
    const disc = field === "discount" ? val : data.discount.amount;
    const total = Number((subtotal + totalTaxes + sc - disc).toFixed(2));

    const updated: ReceiptData = {
      ...data,
      [field]: { ...data[field], amount: val, is_low_confidence: false },
      total: { ...data.total, amount: total }
    };
    setData(updated);
    onUpdateReceipt(updated);
  };

  const handleTaxChange = (index: number, val: number) => {
    const newTaxes = [...data.taxes];
    newTaxes[index] = { ...newTaxes[index], amount: val };
    const totalTaxes = newTaxes.reduce((s, t) => s + t.amount, 0);
    const subtotal = data.subtotal.amount;
    const sc = data.service_charge.amount;
    const disc = data.discount.amount;
    const total = Number((subtotal + totalTaxes + sc - disc).toFixed(2));

    const updated: ReceiptData = {
      ...data,
      taxes: newTaxes,
      total: { ...data.total, amount: total }
    };
    setData(updated);
    onUpdateReceipt(updated);
  };

  const lowConfidenceCount = data.items.filter((i) => i.is_low_confidence).length +
    (data.service_charge.is_low_confidence ? 1 : 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-zinc-100">
            Verify Receipt Items
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            Check the extracted items and prices. You can edit any field or add missing items.
          </p>
        </div>

        {lowConfidenceCount > 0 ? (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>Please double-check {lowConfidenceCount} highlighted item(s)</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 text-xs">
            <CheckCircle2 className="w-3.5 h-3.5 text-zinc-400" />
            <span>All items confirmed</span>
          </div>
        )}
      </div>

      {/* Merchant Info Banner */}
      <div className="app-panel p-3.5 rounded-lg flex flex-wrap items-center justify-between gap-3 text-sm">
        <div className="flex items-center gap-2">
          <Store className="w-4 h-4 text-zinc-400" />
          <input
            type="text"
            value={data.merchant.name}
            onChange={(e) => {
              const updated = {
                ...data,
                merchant: { ...data.merchant, name: e.target.value }
              };
              setData(updated);
              onUpdateReceipt(updated);
            }}
            placeholder="Restaurant Name"
            className="bg-transparent font-medium text-zinc-100 focus:outline-none focus:underline"
          />
        </div>
        <div className="flex items-center gap-1.5 text-xs text-zinc-400">
          <Calendar className="w-3.5 h-3.5 text-zinc-500" />
          <span>{data.merchant.date || "2026-10-04"}</span>
        </div>
      </div>

      {/* Line Items List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
            Items ({data.items.length})
          </span>
          <button
            onClick={addItem}
            className="flex items-center gap-1 text-xs text-zinc-300 hover:text-white font-medium px-2 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Item</span>
          </button>
        </div>

        <div className="space-y-2">
          {data.items.map((item, idx) => (
            <div
              key={item.id}
              className={`p-3 rounded-lg transition-all ${
                item.is_low_confidence
                  ? "review-highlight"
                  : "app-card border-zinc-800"
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center gap-2.5">
                {/* Item Name */}
                <div className="flex-1 flex items-center gap-2">
                  <span className="text-xs text-zinc-500 font-mono w-4">
                    {idx + 1}.
                  </span>
                  <input
                    type="text"
                    value={item.name}
                    onChange={(e) => updateItem(idx, { name: e.target.value })}
                    className="w-full bg-zinc-900/80 border border-zinc-800 rounded-md px-3 py-1.5 text-sm font-medium text-zinc-100 focus:outline-none focus:border-zinc-500"
                    placeholder="Item name"
                  />
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {/* Qty */}
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-zinc-500">Qty:</span>
                    <input
                      type="number"
                      min={1}
                      value={item.quantity}
                      onChange={(e) =>
                        updateItem(idx, { quantity: parseInt(e.target.value) || 1 })
                      }
                      className="w-12 bg-zinc-900/80 border border-zinc-800 rounded-md px-2 py-1.5 text-sm text-center text-zinc-100 focus:outline-none focus:border-zinc-500"
                    />
                  </div>

                  {/* Price */}
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-zinc-500">₹</span>
                    <input
                      type="number"
                      step="0.5"
                      value={item.price}
                      onChange={(e) =>
                        updateItem(idx, { price: parseFloat(e.target.value) || 0 })
                      }
                      className={`w-24 bg-zinc-900/80 border rounded-md px-2.5 py-1.5 text-sm font-semibold text-right text-zinc-100 focus:outline-none ${
                        item.is_low_confidence
                          ? "border-amber-500 text-amber-300"
                          : "border-zinc-800 focus:border-zinc-500"
                      }`}
                    />
                  </div>

                  {/* Confirm or Delete */}
                  {item.is_low_confidence ? (
                    <button
                      onClick={() => confirmLowConfidenceField(idx)}
                      title="Confirm price"
                      className="px-2.5 py-1.5 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-semibold flex items-center gap-1 hover:bg-amber-500/30 transition"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Confirm</span>
                    </button>
                  ) : (
                    <button
                      onClick={() => removeItem(idx)}
                      className="p-1.5 rounded-md text-zinc-500 hover:text-rose-400 hover:bg-zinc-800 transition"
                      title="Remove item"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>

              {item.is_low_confidence && (
                <div className="mt-1.5 text-[11px] text-amber-400/90 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3 text-amber-400" />
                  <span>Unclear on receipt scan — please verify this price.</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Taxes & Charges */}
      <div className="app-panel p-4 rounded-lg space-y-3">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          Taxes & Extra Charges
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {data.taxes.map((tax, tIdx) => (
            <div
              key={tIdx}
              className="flex items-center justify-between p-2.5 rounded-md bg-zinc-900/80 border border-zinc-800"
            >
              <span className="text-xs text-zinc-300 font-medium">{tax.name}</span>
              <div className="flex items-center gap-1">
                <span className="text-xs text-zinc-500">₹</span>
                <input
                  type="number"
                  step="0.25"
                  value={tax.amount}
                  onChange={(e) =>
                    handleTaxChange(tIdx, parseFloat(e.target.value) || 0)
                  }
                  className="w-20 bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-xs font-medium text-right focus:outline-none focus:border-zinc-500"
                />
              </div>
            </div>
          ))}

          {/* Service charge */}
          <div
            className={`flex items-center justify-between p-2.5 rounded-md border transition ${
              data.service_charge.is_low_confidence
                ? "review-highlight"
                : "bg-zinc-900/80 border-zinc-800"
            }`}
          >
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-zinc-300 font-medium">Service Charge</span>
              {data.service_charge.is_low_confidence && (
                <button
                  onClick={confirmServiceCharge}
                  className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40"
                >
                  Confirm
                </button>
              )}
            </div>
            <div className="flex items-center gap-1">
              <span className="text-xs text-zinc-500">₹</span>
              <input
                type="number"
                step="0.5"
                value={data.service_charge.amount}
                onChange={(e) =>
                  handleChargeChange("service_charge", parseFloat(e.target.value) || 0)
                }
                className="w-20 bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-xs font-medium text-right focus:outline-none focus:border-zinc-500"
              />
            </div>
          </div>

          {/* Discount */}
          <div className="flex items-center justify-between p-2.5 rounded-md bg-zinc-900/80 border border-zinc-800">
            <span className="text-xs text-zinc-300 font-medium">Discount / Promo</span>
            <div className="flex items-center gap-1">
              <span className="text-xs text-zinc-500">-₹</span>
              <input
                type="number"
                step="0.5"
                value={data.discount.amount}
                onChange={(e) =>
                  handleChargeChange("discount", parseFloat(e.target.value) || 0)
                }
                className="w-20 bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-xs font-medium text-right focus:outline-none focus:border-zinc-500"
              />
            </div>
          </div>
        </div>

        {/* Totals Summary */}
        <div className="pt-3 border-t border-zinc-800 flex items-center justify-between text-sm">
          <div className="text-zinc-400">
            Subtotal: <span className="font-semibold text-zinc-200">₹{data.subtotal.amount.toFixed(2)}</span>
          </div>
          <div className="text-base font-bold text-zinc-100 flex items-center gap-1.5">
            <span>Total:</span>
            <span className="text-lg text-zinc-100 font-mono">
              ₹{data.total.amount.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Continue Button */}
      <div className="flex justify-end pt-2">
        <button
          onClick={onContinue}
          className="btn-primary flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm active:scale-98 shadow-sm"
        >
          <span>Continue to People</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
