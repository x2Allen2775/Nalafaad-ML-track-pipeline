"use client";

import React, { useEffect, useState } from "react";
import {
  Edit2,
  Check,
  Share2,
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle2,
  HelpCircle
} from "lucide-react";
import confetti from "canvas-confetti";
import {
  SplitCalculationResponse,
  PersonSplitResult,
  ReceiptData,
  Person
} from "../lib/types";
import { ManualOverrideModal } from "./ManualOverrideModal";

interface StepSummaryProps {
  summary: SplitCalculationResponse;
  receipt: ReceiptData;
  people: Person[];
  onApplyOverride: (personId: string, amount: number | null) => void;
  onBackToAssign: () => void;
}

export const StepSummary: React.FC<StepSummaryProps> = ({
  summary,
  receipt,
  people,
  onApplyOverride,
  onBackToAssign
}) => {
  const [activeOverrideSplit, setActiveOverrideSplit] =
    useState<PersonSplitResult | null>(null);
  const [expandedExplanations, setExpandedExplanations] = useState<
    Record<string, boolean>
  >({});
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    try {
      confetti({
        particleCount: 35,
        spread: 50,
        origin: { y: 0.6 }
      });
    } catch (e) {
      // ignore
    }
  }, []);

  const toggleExplanation = (pId: string) => {
    setExpandedExplanations((prev) => ({
      ...prev,
      [pId]: !prev[pId]
    }));
  };

  const copyWhatsAppSummary = () => {
    let msg = `🧾 *Bill Split: ${receipt.merchant.name}*\n`;
    msg += `Total Bill: ₹${summary.bill_total.toFixed(2)}\n\n`;

    for (const split of summary.splits) {
      msg += `*${split.person_name}*: *₹${split.final_total.toFixed(2)}*\n`;
      msg += `  ${split.explanation}\n\n`;
    }

    if (summary.difference_from_bill !== 0) {
      msg += `Difference: ₹${summary.difference_from_bill.toFixed(2)}\n`;
    }

    navigator.clipboard.writeText(msg);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const isBalanced = Math.abs(summary.difference_from_bill) <= 0.05;

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-zinc-100">
            Bill Breakdown
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            Taxes and service charges are divided according to what each person ordered.
          </p>
        </div>

        <button
          onClick={copyWhatsAppSummary}
          className="btn-primary flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs active:scale-95 shadow-sm"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5" />
              <span>Copied!</span>
            </>
          ) : (
            <>
              <Share2 className="w-3.5 h-3.5" />
              <span>Copy for WhatsApp</span>
            </>
          )}
        </button>
      </div>

      {/* Bill & Balance Overview */}
      <div className="app-panel p-4 sm:p-5 rounded-xl border border-zinc-800 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <span className="text-xs text-zinc-500 uppercase tracking-wider font-semibold">
              Total Bill
            </span>
            <div className="text-2xl sm:text-3xl font-extrabold text-zinc-100 font-mono">
              ₹{summary.bill_total.toFixed(2)}
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div>
              <span className="text-zinc-500 block">Subtotal</span>
              <span className="font-semibold text-zinc-300">₹{summary.global_subtotal.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-zinc-500 block">GST</span>
              <span className="font-semibold text-zinc-300">₹{summary.total_taxes.toFixed(2)}</span>
            </div>
            {summary.total_service_charge > 0 && (
              <div>
                <span className="text-zinc-500 block">Service Charge</span>
                <span className="font-semibold text-zinc-300">₹{summary.total_service_charge.toFixed(2)}</span>
              </div>
            )}
            {summary.total_discount > 0 && (
              <div>
                <span className="text-zinc-500 block">Discount</span>
                <span className="font-semibold text-emerald-400">-₹{summary.total_discount.toFixed(2)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Balance Status */}
        <div className="pt-2.5 border-t border-zinc-800/80 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="text-zinc-500">Total accounted for:</span>
            <span className="font-mono font-semibold text-zinc-300">
              ₹{summary.calculated_sum.toFixed(2)}
            </span>
          </div>

          {isBalanced ? (
            <div className="flex items-center gap-1.5 text-zinc-400 text-xs">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Exact match</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-amber-400 text-xs font-medium">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>
                Difference: {summary.difference_from_bill > 0 ? "+" : ""}
                ₹{summary.difference_from_bill.toFixed(2)}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Person Split Cards */}
      <div className="space-y-3">
        {summary.splits.map((split) => {
          const isExplanationOpen = expandedExplanations[split.person_id] ?? true;

          return (
            <div
              key={split.person_id}
              className="app-panel rounded-xl p-4 border border-zinc-800/80 space-y-3"
            >
              {/* Person Header */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-xs font-bold text-zinc-200">
                    {split.person_name.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-sm text-zinc-100">
                        {split.person_name}
                      </h3>
                      {split.is_overridden && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
                          Adjusted
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-zinc-500">
                      Share of table: {split.proportion_percentage}%
                    </p>
                  </div>
                </div>

                {/* Amount and Pencil */}
                <div className="flex items-center gap-2 text-right">
                  <div>
                    <div className="text-lg sm:text-xl font-bold text-zinc-100 font-mono">
                      ₹{split.final_total.toFixed(2)}
                    </div>
                    {split.is_overridden && (
                      <span className="text-[10px] text-zinc-500 block">
                        Original: ₹{split.calculated_total.toFixed(2)}
                      </span>
                    )}
                  </div>

                  <button
                    onClick={() => setActiveOverrideSplit(split)}
                    title="Edit amount"
                    className="p-1.5 rounded-md bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 border border-zinc-800 transition"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Items Breakdown */}
              <div className="bg-zinc-900/60 rounded-lg p-2.5 border border-zinc-800/60 text-xs space-y-1">
                {split.assigned_items.length === 0 ? (
                  <p className="text-zinc-500 italic">No items assigned</p>
                ) : (
                  split.assigned_items.map((it, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between text-zinc-300"
                    >
                      <span>
                        {it.share_fraction !== "1/1" && (
                          <span className="font-mono text-zinc-400 mr-1.5">
                            [{it.share_fraction}]
                          </span>
                        )}
                        {it.item_name}
                      </span>
                      <span className="font-mono text-zinc-300">
                        ₹{it.share_amount.toFixed(2)}
                      </span>
                    </div>
                  ))
                )}

                <div className="pt-2 mt-2 border-t border-zinc-800/80 flex flex-wrap items-center justify-between text-[11px] text-zinc-500 gap-y-1">
                  <div>
                    Items: <span className="text-zinc-300">₹{split.subtotal.toFixed(2)}</span>
                  </div>
                  <div>
                    Taxes: <span className="text-zinc-300">+₹{split.taxes_share.toFixed(2)}</span>
                  </div>
                  {split.service_charge_share > 0 && (
                    <div>
                      Service: <span className="text-zinc-300">+₹{split.service_charge_share.toFixed(2)}</span>
                    </div>
                  )}
                  {split.discount_share > 0 && (
                    <div>
                      Discount: <span className="text-emerald-400">-₹{split.discount_share.toFixed(2)}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Explanation Accordion */}
              <div className="border border-zinc-800 rounded-lg overflow-hidden">
                <button
                  type="button"
                  onClick={() => toggleExplanation(split.person_id)}
                  className="w-full px-3 py-1.5 bg-zinc-900/40 hover:bg-zinc-900 flex items-center justify-between text-left text-xs text-zinc-400 transition"
                >
                  <div className="flex items-center gap-1.5">
                    <HelpCircle className="w-3 h-3 text-zinc-500" />
                    <span>How this was calculated</span>
                  </div>
                  <div className="text-zinc-500">
                    {isExplanationOpen ? (
                      <ChevronUp className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5" />
                    )}
                  </div>
                </button>

                {isExplanationOpen && (
                  <div className="p-2.5 bg-zinc-950/60 text-xs text-zinc-400 leading-relaxed border-t border-zinc-800/60 font-sans">
                    <p>{split.explanation}</p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer Buttons */}
      <div className="flex items-center justify-between pt-2">
        <button
          onClick={onBackToAssign}
          className="btn-secondary flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Edit Assignments</span>
        </button>

        <button
          onClick={copyWhatsAppSummary}
          className="btn-primary flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs shadow-sm"
        >
          <Share2 className="w-3.5 h-3.5" />
          <span>Copy Breakdown</span>
        </button>
      </div>

      {activeOverrideSplit && (
        <ManualOverrideModal
          split={activeOverrideSplit}
          isOpen={!!activeOverrideSplit}
          onClose={() => setActiveOverrideSplit(null)}
          onSaveOverride={onApplyOverride}
        />
      )}
    </div>
  );
};
