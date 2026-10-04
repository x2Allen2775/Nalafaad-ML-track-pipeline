"use client";

import React, { useState } from "react";
import { Users, Plus, X, ArrowRight, UserPlus } from "lucide-react";
import { Person } from "../lib/types";

interface StepPartyProps {
  people: Person[];
  onUpdatePeople: (people: Person[]) => void;
  onContinue: () => void;
}

const AVATAR_COLORS = [
  "bg-zinc-800 text-zinc-200 border-zinc-700",
  "bg-slate-800 text-slate-200 border-slate-700",
  "bg-neutral-800 text-neutral-200 border-neutral-700",
  "bg-stone-800 text-stone-200 border-stone-700",
  "bg-zinc-900 text-zinc-100 border-zinc-600"
];

export const StepParty: React.FC<StepPartyProps> = ({
  people,
  onUpdatePeople,
  onContinue
}) => {
  const [inputName, setInputName] = useState("");

  const handleAddPerson = (nameToAdd?: string) => {
    const raw = (nameToAdd || inputName).trim();
    if (!raw) return;

    if (people.some((p) => p.name.toLowerCase() === raw.toLowerCase())) {
      setInputName("");
      return;
    }

    const color = AVATAR_COLORS[people.length % AVATAR_COLORS.length];
    const newPerson: Person = {
      id: `p_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
      name: raw,
      avatarColor: color
    };

    onUpdatePeople([...people, newPerson]);
    setInputName("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddPerson();
    }
  };

  const handleRemovePerson = (id: string) => {
    onUpdatePeople(people.filter((p) => p.id !== id));
  };

  const loadPresetParty = (names: string[]) => {
    const newParty: Person[] = names.map((nm, idx) => ({
      id: `p_${Date.now()}_${idx}`,
      name: nm,
      avatarColor: AVATAR_COLORS[idx % AVATAR_COLORS.length]
    }));
    onUpdatePeople(newParty);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl sm:text-2xl font-bold text-zinc-100">
          Who is sharing this bill?
        </h2>
        <p className="text-xs text-zinc-400 mt-1">
          Add the names of everyone at the table.
        </p>
      </div>

      {/* Input Field */}
      <div className="app-panel p-4 rounded-xl space-y-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <UserPlus className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <input
              type="text"
              value={inputName}
              onChange={(e) => setInputName(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Name (e.g. Rahul, Priya, Amit)..."
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-10 pr-4 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-zinc-500"
            />
          </div>
          <button
            onClick={() => handleAddPerson()}
            className="btn-primary flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm transition active:scale-95"
          >
            <Plus className="w-4 h-4" />
            <span>Add</span>
          </button>
        </div>

        {/* Quick presets */}
        <div className="flex items-center gap-2 flex-wrap text-xs text-zinc-400 pt-1">
          <span className="text-zinc-500">Quick add:</span>
          <button
            onClick={() => loadPresetParty(["Rahul", "Priya", "Amit"])}
            className="px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 transition"
          >
            Rahul, Priya, Amit
          </button>
          <button
            onClick={() => loadPresetParty(["Rahul", "Priya", "Amit", "Sneha"])}
            className="px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 transition"
          >
            4 People
          </button>
          <button
            onClick={() => loadPresetParty(["Rahul", "Priya"])}
            className="px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 transition"
          >
            2 People
          </button>
        </div>
      </div>

      {/* People Chips */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold uppercase tracking-wider text-zinc-400">
            People ({people.length})
          </span>
          {people.length > 0 && (
            <button
              onClick={() => onUpdatePeople([])}
              className="text-zinc-500 hover:text-rose-400 transition"
            >
              Clear
            </button>
          )}
        </div>

        {people.length === 0 ? (
          <div className="app-card p-6 rounded-xl text-center border-dashed border-zinc-800 text-zinc-500 text-xs">
            <Users className="w-6 h-6 mx-auto text-zinc-600 mb-2" />
            <p>No one added yet.</p>
            <p className="mt-1">Add people above to start splitting.</p>
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {people.map((p) => {
              const initials = p.name.slice(0, 2).toUpperCase();
              return (
                <div
                  key={p.id}
                  className="flex items-center gap-2 pl-2 pr-2.5 py-1 rounded-full bg-zinc-900 border border-zinc-800"
                >
                  <div className="w-5 h-5 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-[10px] font-bold text-zinc-300">
                    {initials}
                  </div>
                  <span className="text-xs font-medium text-zinc-200">
                    {p.name}
                  </span>
                  <button
                    onClick={() => handleRemovePerson(p.id)}
                    className="p-0.5 rounded-full text-zinc-500 hover:text-rose-400 transition ml-0.5"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Next Button */}
      <div className="flex justify-end pt-4">
        <button
          onClick={onContinue}
          disabled={people.length === 0}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-semibold text-sm transition active:scale-98 ${
            people.length > 0
              ? "btn-primary shadow-sm"
              : "bg-zinc-900 text-zinc-600 border border-zinc-800 cursor-not-allowed"
          }`}
        >
          <span>Continue to Assign</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
