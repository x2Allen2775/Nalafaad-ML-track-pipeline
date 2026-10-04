"use client";

import React, { useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Split
} from "lucide-react";
import { ReceiptData, Person } from "../lib/types";

interface StepAssignmentProps {
  receipt: ReceiptData;
  people: Person[];
  assignments: Record<string, string[]>;
  onUpdateAssignments: (assignments: Record<string, string[]>) => void;
  onContinue: () => void;
}

export const StepAssignment: React.FC<StepAssignmentProps> = ({
  receipt,
  people,
  assignments,
  onUpdateAssignments,
  onContinue
}) => {
  const [expandedItemId, setExpandedItemId] = useState<string | null>(
    receipt.items[0]?.id || null
  );

  const toggleSharer = (itemId: string, personId: string) => {
    const current = assignments[itemId] || [];
    const isAssigned = current.includes(personId);
    let updated: string[];

    if (isAssigned) {
      updated = current.filter((id) => id !== personId);
    } else {
      updated = [...current, personId];
    }

    onUpdateAssignments({
      ...assignments,
      [itemId]: updated
    });
  };

  const assignAllToItem = (itemId: string) => {
    onUpdateAssignments({
      ...assignments,
      [itemId]: people.map((p) => p.id)
    });
  };

  const splitAllEvenly = () => {
    const allAssigned: Record<string, string[]> = {};
    const allIds = people.map((p) => p.id);
    for (const item of receipt.items) {
      allAssigned[item.id] = allIds;
    }
    onUpdateAssignments(allAssigned);
  };

  const clearAllAssignments = () => {
    const cleared: Record<string, string[]> = {};
    for (const item of receipt.items) {
      cleared[item.id] = [];
    }
    onUpdateAssignments(cleared);
  };

  const liveSubtotals: Record<string, number> = {};
  for (const p of people) {
    liveSubtotals[p.id] = 0.0;
  }
  for (const item of receipt.items) {
    const sharers = assignments[item.id] || [];
    if (sharers.length > 0) {
      const shareVal = item.price / sharers.length;
      for (const pId of sharers) {
        if (liveSubtotals[pId] !== undefined) {
          liveSubtotals[pId] += shareVal;
        }
      }
    }
  }

  const unassignedCount = receipt.items.filter(
    (item) => !(assignments[item.id]?.length > 0)
  ).length;

  return (
    <div className="space-y-6 pb-20">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-zinc-100">
            Assign Items
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            Tap an item to expand and select who shared it. Shares divide evenly per item.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={splitAllEvenly}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-zinc-900 hover:bg-zinc-800 text-xs font-medium text-zinc-300 transition border border-zinc-800"
          >
            <Split className="w-3.5 h-3.5 text-zinc-400" />
            <span>Split All Equally</span>
          </button>
          <button
            onClick={clearAllAssignments}
            className="px-2.5 py-1.5 text-xs text-zinc-500 hover:text-rose-400 transition"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Unassigned Warning */}
      {unassignedCount > 0 && (
        <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 text-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-500 shrink-0" />
            <span>
              {unassignedCount} item(s) unassigned. Unassigned items are omitted from individual totals.
            </span>
          </div>
        </div>
      )}

      {/* Items List */}
      <div className="space-y-2">
        {receipt.items.map((item, idx) => {
          const isExpanded = expandedItemId === item.id;
          const sharerIds = assignments[item.id] || [];
          const numSharers = sharerIds.length;
          const shareAmount = numSharers > 0 ? (item.price / numSharers).toFixed(2) : "0.00";
          const fractionStr = numSharers > 1 ? `1/${numSharers}` : numSharers === 1 ? "1 person" : "Unassigned";

          return (
            <div
              key={item.id}
              className={`rounded-lg transition-all border ${
                isExpanded
                  ? "app-panel border-zinc-500"
                  : numSharers === 0
                  ? "app-card border-amber-900/50"
                  : "app-card border-zinc-800 hover:border-zinc-700"
              }`}
            >
              {/* Card Header */}
              <div
                onClick={() => setExpandedItemId(isExpanded ? null : item.id)}
                className="p-3.5 cursor-pointer flex items-center justify-between gap-3 select-none"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs text-zinc-500 font-mono w-4">
                    {idx + 1}
                  </span>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-semibold text-zinc-100">
                        {item.name}
                      </h4>
                      {item.quantity > 1 && (
                        <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">
                          x{item.quantity}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-zinc-400 mt-0.5">
                      <span>₹{item.price.toFixed(2)}</span>
                      <span>·</span>
                      <span className={numSharers > 0 ? "text-zinc-300" : "text-amber-400 font-medium"}>
                        {fractionStr} {numSharers > 0 && `(₹${shareAmount} each)`}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2.5">
                  {/* Assigned Avatars */}
                  <div className="flex items-center -space-x-1">
                    {sharerIds.map((pId) => {
                      const person = people.find((p) => p.id === pId);
                      if (!person) return null;
                      return (
                        <div
                          key={pId}
                          title={person.name}
                          className="w-5 h-5 rounded-full bg-zinc-800 border border-zinc-950 flex items-center justify-center text-[9px] font-bold text-zinc-200"
                        >
                          {person.name.slice(0, 2).toUpperCase()}
                        </div>
                      );
                    })}
                  </div>

                  <div className="text-zinc-500">
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </div>
                </div>
              </div>

              {/* Expanded Assignment Body */}
              {isExpanded && (
                <div className="px-4 pb-3.5 pt-1 border-t border-zinc-800 space-y-2.5">
                  <div className="flex items-center justify-between text-xs text-zinc-400">
                    <span>Select who shared this:</span>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        assignAllToItem(item.id);
                      }}
                      className="text-[11px] text-zinc-300 hover:text-white underline font-medium"
                    >
                      Assign to Everyone ({people.length})
                    </button>
                  </div>

                  {/* People Selector Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {people.map((person) => {
                      const isSelected = sharerIds.includes(person.id);
                      return (
                        <button
                          key={person.id}
                          type="button"
                          onClick={() => toggleSharer(item.id, person.id)}
                          className={`flex items-center justify-between p-2 rounded-md border text-left transition-all ${
                            isSelected
                              ? "border-zinc-200 bg-zinc-100 text-zinc-950 font-semibold shadow-sm"
                              : "border-zinc-800 bg-zinc-900/60 text-zinc-300 hover:border-zinc-700"
                          } active:scale-95`}
                        >
                          <div className="flex items-center gap-2">
                            <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold ${
                              isSelected ? "bg-zinc-900 text-zinc-100" : "bg-zinc-800 text-zinc-300"
                            }`}>
                              {person.name.slice(0, 2).toUpperCase()}
                            </div>
                            <span className="text-xs truncate max-w-[80px]">
                              {person.name}
                            </span>
                          </div>
                          {isSelected && (
                            <span className="text-xs">✓</span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Floating Bottom Subtotal Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-zinc-950/95 border-t border-zinc-800 p-3 z-30 shadow-xl backdrop-blur-md">
        <div className="max-w-3xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3 overflow-x-auto w-full sm:w-auto py-1">
            <span className="text-xs text-zinc-500 font-medium shrink-0">
              Subtotals:
            </span>
            {people.map((p) => (
              <div
                key={p.id}
                className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-xs shrink-0"
              >
                <span className="text-zinc-400">{p.name}:</span>
                <span className="font-mono font-semibold text-zinc-100">
                  ₹{liveSubtotals[p.id]?.toFixed(2) || "0.00"}
                </span>
              </div>
            ))}
          </div>

          <button
            onClick={onContinue}
            className="w-full sm:w-auto btn-primary flex items-center justify-center gap-2 px-5 py-2 rounded-lg text-sm active:scale-98 shadow-sm shrink-0"
          >
            <span>See Final Split</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
