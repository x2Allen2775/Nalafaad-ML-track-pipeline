"use client";

import React from "react";
import { Receipt, RefreshCw } from "lucide-react";

interface HeaderProps {
  currentStep: number;
  onReset: () => void;
}

const STEPS = [
  { id: 1, label: "Upload" },
  { id: 2, label: "Verify Items" },
  { id: 3, label: "People" },
  { id: 4, label: "Assign" },
  { id: 5, label: "Breakdown" }
];
/*me to thak gaya yaar*/

export const Header: React.FC<HeaderProps> = ({ currentStep, onReset }) => {
  return (
    <header className="sticky top-0 z-40 w-full bg-zinc-950/90 backdrop-blur-md border-b border-zinc-800/80 px-4 py-3 sm:px-6">
      <div className="max-w-3xl mx-auto flex flex-col gap-3">
        {/* Brand row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-zinc-100 flex items-center justify-center text-zinc-950">
              <Receipt className="w-4 h-4 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-zinc-100">
                  SplitSnap
                </span>
                <span className="text-[11px] text-zinc-400 font-normal">
                  Bill Splitter
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={onReset}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-medium text-zinc-300 hover:text-white transition"
            title="Start new bill"
          >
            <RefreshCw className="w-3 h-3 text-zinc-400" />
            <span>New Bill</span>
          </button>
        </div>

        {/* Clean Step Progress Bar */}
        <div className="flex items-center justify-between pt-1 relative">
          <div className="absolute top-1/2 left-0 right-0 h-px bg-zinc-800 -translate-y-1/2 z-0" />
          <div
            className="absolute top-1/2 left-0 h-px bg-zinc-400 -translate-y-1/2 z-0 transition-all duration-300"
            style={{ width: `${((currentStep - 1) / (STEPS.length - 1)) * 100}%` }}
          />

          {STEPS.map((s) => {
            const isCompleted = currentStep > s.id;
            const isCurrent = currentStep === s.id;
            return (
              <div
                key={s.id}
                className="relative z-10 flex flex-col items-center gap-1"
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-all duration-150 ${
                    isCurrent
                      ? "bg-zinc-100 text-zinc-950 ring-4 ring-zinc-800"
                      : isCompleted
                      ? "bg-zinc-700 text-zinc-200"
                      : "bg-zinc-900 text-zinc-500 border border-zinc-800"
                  }`}
                >
                  {isCompleted ? "✓" : s.id}
                </div>
                <span
                  className={`text-[11px] hidden sm:inline ${
                    isCurrent
                      ? "text-zinc-100 font-semibold"
                      : isCompleted
                      ? "text-zinc-400 font-normal"
                      : "text-zinc-600 font-normal"
                  }`}
                >
                  {s.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </header>
  );
};
