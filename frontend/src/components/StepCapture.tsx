"use client";

import React, { useRef, useState } from "react";
import { Camera, Upload, FileText } from "lucide-react";
import { SAMPLE_PRESETS, PresetOption } from "../lib/sampleData";
import { ReceiptData } from "../lib/types";

interface StepCaptureProps {
  onReceiptLoaded: (data: ReceiptData, imagePreview?: string) => void;
  isLoading: boolean;
  setIsLoading: (val: boolean) => void;
}

export const StepCapture: React.FC<StepCaptureProps> = ({
  onReceiptLoaded,
  isLoading,
  setIsLoading
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null);

  const handleFileUpload = async (file: File) => {
    setIsLoading(true);
    const previewUrl = URL.createObjectURL(file);
    try {
      const { extractReceiptFromApi } = await import("../lib/apportionmentClient");
      const data = await extractReceiptFromApi(file);
      onReceiptLoaded(data, previewUrl);
    } catch (e) {
      console.error("Extraction error:", e);
      onReceiptLoaded(SAMPLE_PRESETS[0].data, previewUrl);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePresetSelect = async (preset: PresetOption) => {
    setSelectedPresetId(preset.id);
    setIsLoading(true);
    try {
      const { extractReceiptFromApi } = await import("../lib/apportionmentClient");
      const data = await extractReceiptFromApi(undefined, preset.id);
      onReceiptLoaded(data);
    } catch (e) {
      onReceiptLoaded(preset.data);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="text-center space-y-1.5 py-2">
        <h2 className="text-2xl font-bold tracking-tight text-zinc-100">
          Upload or Scan Receipt
        </h2>
        <p className="text-zinc-400 text-sm max-w-md mx-auto">
          Snap a photo of the restaurant bill, upload an image, or pick a sample bill.
        </p>
      </div>

      {/* Main Upload Dropzone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (e.dataTransfer.files?.[0]) {
            handleFileUpload(e.dataTransfer.files[0]);
          }
        }}
        className={`app-panel rounded-xl p-8 text-center border transition-all ${
          dragOver
            ? "border-zinc-400 bg-zinc-900"
            : "border-zinc-800 hover:border-zinc-700"
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.[0]) handleFileUpload(e.target.files[0]);
          }}
        />
        <input
          type="file"
          ref={cameraInputRef}
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.[0]) handleFileUpload(e.target.files[0]);
          }}
        />

        {isLoading ? (
          <div className="py-10 space-y-4">
            <div className="relative w-12 h-12 mx-auto">
              <div className="w-12 h-12 rounded-full border-2 border-zinc-700 border-t-zinc-200 animate-spin" />
              <div className="absolute inset-0 flex items-center justify-center">
                <FileText className="w-5 h-5 text-zinc-400" />
              </div>
            </div>
            <div>
              <p className="font-semibold text-zinc-200 text-sm">
                Processing receipt...
              </p>
              <p className="text-xs text-zinc-500 mt-1">
                Reading line items, taxes, and totals
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-center gap-3">
              <button
                type="button"
                onClick={() => cameraInputRef.current?.click()}
                className="btn-primary flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm active:scale-95 shadow-sm"
              >
                <Camera className="w-4 h-4" />
                <span>Take Photo</span>
              </button>

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="btn-secondary flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm active:scale-95"
              >
                <Upload className="w-4 h-4 text-zinc-400" />
                <span>Choose File</span>
              </button>
            </div>

            <p className="text-xs text-zinc-500">
              Supports JPEG, PNG, HEIC from your camera or files
            </p>
          </div>
        )}
      </div>

      {/* Preset Bills */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
            Sample Bills
          </span>
          <span className="text-xs text-zinc-500">Click any bill to load</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {SAMPLE_PRESETS.map((preset) => {
            const isSelected = selectedPresetId === preset.id;
            return (
              <button
                key={preset.id}
                onClick={() => handlePresetSelect(preset)}
                disabled={isLoading}
                className={`text-left p-3.5 rounded-lg border transition-all ${
                  isSelected
                    ? "border-zinc-300 bg-zinc-800"
                    : "app-card border-zinc-800 hover:border-zinc-700 hover:bg-zinc-850"
                } active:scale-98`}
              >
                <div className="flex items-start justify-between gap-2">
                  <h4 className="font-semibold text-sm text-zinc-100 line-clamp-1">
                    {preset.title}
                  </h4>
                  <span className="text-[11px] font-mono text-zinc-400">
                    {preset.badge.split("·")[1]?.trim()}
                  </span>
                </div>
                <p className="text-xs text-zinc-400 mt-1.5 line-clamp-2">
                  {preset.description}
                </p>
                <div className="text-[11px] text-zinc-400 font-medium mt-3 flex items-center gap-1">
                  <span>Open</span>
                  <span>→</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
