"use client";
/*color kardunga iskoo*/

import React, { useState } from "react";
import { Header } from "../components/Header";
import { StepCapture } from "../components/StepCapture";
import { StepCorrection } from "../components/StepCorrection";
import { StepParty } from "../components/StepParty";
import { StepAssignment } from "../components/StepAssignment";
import { StepSummary } from "../components/StepSummary";
import {
  ReceiptData,
  Person,
  SplitCalculationResponse
} from "../lib/types";
import { SAMPLE_PRESETS } from "../lib/sampleData";
import {
  calculateProportionalSplitApi,
  calculateLocalProportionalSplit
} from "../lib/apportionmentClient";
/*color kardunga iskoo*/

const DEFAULT_PEOPLE: Person[] = [
  { id: "p_1", name: "Rahul", avatarColor: "bg-zinc-800 text-zinc-200 border-zinc-700" },
  { id: "p_2", name: "Priya", avatarColor: "bg-slate-800 text-slate-200 border-slate-700" },
  { id: "p_3", name: "Amit", avatarColor: "bg-stone-800 text-stone-200 border-stone-700" }
];

export default function Home() {
  const [step, setStep] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [receipt, setReceipt] = useState<ReceiptData>(SAMPLE_PRESETS[0].data);
  const [people, setPeople] = useState<Person[]>(DEFAULT_PEOPLE);
  const [assignments, setAssignments] = useState<Record<string, string[]>>({});
  const [manualOverrides, setManualOverrides] = useState<Record<string, number>>({});
  const [summary, setSummary] = useState<SplitCalculationResponse | null>(null);

  // Step 1: Receipt Loaded
  const handleReceiptLoaded = (data: ReceiptData) => {
    setReceipt(data);
    const initialAssign: Record<string, string[]> = {};
    const safeItems = Array.isArray(data?.items) ? data.items : [];
    for (const item of safeItems) {
      initialAssign[item.id] = [];
    }
    setAssignments(initialAssign);
    setManualOverrides({});
    setStep(2);
  };
/*color kardunga iskoo*/

  // Step 2: Verification complete
  const handleCorrectionComplete = () => {
    setStep(3);
  };

  // Step 3: Party setup complete
  const handlePartyComplete = () => {
    if (Object.keys(assignments).length === 0 || Object.values(assignments).every((v) => v.length === 0)) {
      const defaultAssign: Record<string, string[]> = {};
      receipt.items.forEach((item, idx) => {
        if (people.length > 0) {
          defaultAssign[item.id] = [people[idx % people.length].id];
        } else {
          defaultAssign[item.id] = [];
        }
      });
      setAssignments(defaultAssign);
    }
    setStep(4);
  };

  // Step 4: Assignment complete -> Compute Split
  const handleAssignmentComplete = async () => {
    setIsLoading(true);
    try {
      const res = await calculateProportionalSplitApi(
        receipt,
        people,
        assignments,
        manualOverrides
      );
      setSummary(res);
      setStep(5);
    } catch (e) {
      const localRes = calculateLocalProportionalSplit(
        receipt,
        people,
        assignments,
        manualOverrides
      );
      setSummary(localRes);
      setStep(5);
    } finally {
      setIsLoading(false);
    }
  };

  // Step 5: Adjust amount
  const handleApplyOverride = async (personId: string, amount: number | null) => {
    const updated = { ...manualOverrides };
    if (amount === null) {
      delete updated[personId];
    } else {
      updated[personId] = amount;
    }
    setManualOverrides(updated);

    const res = await calculateProportionalSplitApi(
      receipt,
      people,
      assignments,
      updated
    );
    setSummary(res);
  };

  const handleReset = () => {
    setStep(1);
    setReceipt(SAMPLE_PRESETS[0].data);
    setAssignments({});
    setManualOverrides({});
    setSummary(null);
  };

  return (
    <div className="min-h-screen flex flex-col bg-zinc-950 text-zinc-100">
      <Header currentStep={step} onReset={handleReset} />

      <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-6 sm:px-6">
        {step === 1 && (
          <StepCapture
            onReceiptLoaded={handleReceiptLoaded}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        )}

        {step === 2 && (
          <StepCorrection
            receipt={receipt}
            onUpdateReceipt={setReceipt}
            onContinue={handleCorrectionComplete}
          />
        )}

        {step === 3 && (
          <StepParty
            people={people}
            onUpdatePeople={setPeople}
            onContinue={handlePartyComplete}
          />
        )}

        {step === 4 && (
          <StepAssignment
            receipt={receipt}
            people={people}
            assignments={assignments}
            onUpdateAssignments={setAssignments}
            onContinue={handleAssignmentComplete}
          />
        )}

        {step === 5 && summary && (
          <StepSummary
            summary={summary}
            receipt={receipt}
            people={people}
            onApplyOverride={handleApplyOverride}
            onBackToAssign={() => setStep(4)}
          />
        )}
      </main>

      <footer className="w-full border-t border-zinc-900 py-4 text-center text-xs text-zinc-600">
        <p>SplitSnap</p>
      </footer>
    </div>
  );
}
/*color kardunga iskoo*/
/*color kardunga iskoo*/
/*color kardunga iskoo*/
