"use client";
/*ai se bhi galati hoti hai ji, usko theek ye karega*/

import React, { useState } from "react";
import { Edit3, X, Check } from "lucide-react";
import { PersonSplitResult } from "../lib/types";

interface ManualOverrideModalProps {
  split: PersonSplitResult;
  isOpen: boolean;
  onClose: () => void;
  onSaveOverride: (personId: string, amount: number | null) => void;
}

export const ManualOverrideModal: React.FC<ManualOverrideModalProps> = ({
  split,
  isOpen,
  onClose,
  onSaveOverride
}) => {
  const [amountStr, setAmountStr] = useState<string>(
    split.final_total.toString()
  );

  if (!isOpen) return null;

  const handleSave = () => {
    const val = parseFloat(amountStr);
    if (!isNaN(val) && val >= 0) {
      onSaveOverride(split.person_id, val);
    }
    onClose();
  };

  const handleResetToFormula = () => {
    onSaveOverride(split.person_id, null);
    onClose();
  };

  const numVal = parseFloat(amountStr) || 0;
  const diff = Number((numVal - split.calculated_total).toFixed(2));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
      <div className="app-panel w-full max-w-sm rounded-xl p-5 border border-zinc-800 shadow-2xl space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Edit3 className="w-4 h-4 text-zinc-400" />
            <h3 className="font-semibold text-zinc-100 text-sm">
              Adjust Amount for {split.person_name}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-zinc-500 hover:text-white transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <p className="text-xs text-zinc-400">
          Enter a custom final amount (e.g. if rounding up or paying cash).
        </p>

        {/* Amount Input */}
        <div className="space-y-2">
          <label className="text-xs text-zinc-400 font-medium">
            Custom Amount:
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500 font-bold">
              ₹
            </span>
            <input
              type="number"
              step="0.5"
              value={amountStr}
              onChange={(e) => setAmountStr(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-lg pl-7 pr-3 py-2 text-base font-bold text-white focus:outline-none focus:border-zinc-400"
              autoFocus
            />
          </div>

          <div className="flex items-center justify-between text-xs pt-1">
            <span className="text-zinc-500">Calculated share:</span>
            <span className="font-mono text-zinc-300">
              ₹{split.calculated_total.toFixed(2)}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-500">Difference:</span>
            <span
              className={`font-mono font-medium ${
                diff > 0
                  ? "text-emerald-400"
                  : diff < 0
                  ? "text-rose-400"
                  : "text-zinc-400"
              }`}
            >
              {diff > 0 ? `+₹${diff.toFixed(2)}` : diff < 0 ? `-₹${Math.abs(diff).toFixed(2)}` : "₹0.00"}
            </span>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex items-center justify-between pt-2 gap-2">
          {split.is_overridden ? (
            <button
              type="button"
              onClick={handleResetToFormula}
              className="text-xs text-rose-400 hover:underline transition"
            >
              Reset to calculated
            </button>
          ) : (
            <span />
          )}

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary px-3 py-1.5 rounded-md text-xs"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              className="btn-primary flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs active:scale-95 shadow-sm"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Save</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
/*ai se bhi galati hoti hai ji, usko theek ye karega*/
