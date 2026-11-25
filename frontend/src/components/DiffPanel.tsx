"use client";

import React, { useState } from "react";
import { GitCompare, CheckCircle, ArrowRight, Info, Layers, Briefcase, Code, Sparkles } from "lucide-react";

export interface DiffItem {
  category: string;
  item_name: string;
  original: string | string[];
  tailored: string | string[];
  reason: string;
}

interface DiffPanelProps {
  changesSummary: DiffItem[];
  pageCount?: number;
}

export default function DiffPanel({ changesSummary, pageCount = 1 }: DiffPanelProps) {
  const [activeFilter, setActiveFilter] = useState<string>("All");

  if (!changesSummary || changesSummary.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800/80 text-slate-400 mb-3">
          <GitCompare className="h-6 w-6" />
        </div>
        <h4 className="text-base font-semibold text-slate-300">No Changes to Display Yet</h4>
        <p className="mt-1.5 max-w-sm text-xs text-slate-500 leading-relaxed">
          Paste a Job Description and click &ldquo;Generate Tailored Resume&rdquo;. The AI will transparently log every bullet rewrite, skill reordering, and project selection here.
        </p>
      </div>
    );
  }

  const categories = ["All", ...Array.from(new Set(changesSummary.map((d) => d.category)))];
  const filtered =
    activeFilter === "All"
      ? changesSummary
      : changesSummary.filter((d) => d.category.toLowerCase() === activeFilter.toLowerCase());

  const getCategoryIcon = (cat: string) => {
    switch (cat.toLowerCase()) {
      case "skills":
        return <Code className="h-4 w-4 text-sky-400" />;
      case "experience":
        return <Briefcase className="h-4 w-4 text-emerald-400" />;
      case "projects":
        return <Layers className="h-4 w-4 text-purple-400" />;
      default:
        return <Sparkles className="h-4 w-4 text-amber-400" />;
    }
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Header & Status Indicator */}
      <div className="flex items-center justify-between flex-wrap gap-2 rounded-xl bg-slate-900/70 border border-slate-800 p-3.5">
        <div className="flex items-center gap-2">
          <GitCompare className="h-4 w-4 text-blue-400" />
          <span className="text-sm font-semibold text-slate-200">
            {changesSummary.length} Strategic Adaptations Applied
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-1 font-medium text-emerald-400 border border-emerald-500/20">
            <CheckCircle className="h-3 w-3" /> Zero Fabrication
          </span>
          <span className="inline-flex items-center gap-1 rounded-full bg-blue-500/10 px-2.5 py-1 font-medium text-blue-400 border border-blue-500/20">
            Strict {pageCount}-Page Fit
          </span>
        </div>
      </div>

      {/* Filter Tabs */}
      {categories.length > 2 && (
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setActiveFilter(cat)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all cursor-pointer ${
                activeFilter === cat
                  ? "bg-blue-600 text-white"
                  : "bg-slate-900/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      )}

      {/* Diff Cards List */}
      <div className="flex flex-col gap-3.5">
        {filtered.map((item, idx) => (
          <div
            key={idx}
            className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 transition-all hover:border-slate-700/80"
          >
            {/* Card Header */}
            <div className="flex items-center justify-between gap-2 border-b border-slate-800/80 pb-2.5 mb-3">
              <div className="flex items-center gap-2">
                {getCategoryIcon(item.category)}
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  {item.category}
                </span>
                <span className="text-xs text-slate-600">•</span>
                <span className="text-xs font-medium text-slate-200">{item.item_name}</span>
              </div>
            </div>

            {/* Content Comparison */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 text-xs">
              {/* Original */}
              <div className="rounded-lg bg-rose-950/20 border border-rose-900/30 p-3">
                <div className="font-semibold text-rose-300 mb-1.5 flex items-center gap-1">
                  <span>Original (Master Resume)</span>
                </div>
                {Array.isArray(item.original) ? (
                  <ul className="list-disc list-inside space-y-1 text-slate-400">
                    {item.original.map((b, i) => (
                      <li key={i} className="leading-relaxed">
                        {b}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-slate-400 leading-relaxed font-mono">{item.original}</p>
                )}
              </div>

              {/* Tailored */}
              <div className="rounded-lg bg-emerald-950/20 border border-emerald-900/30 p-3">
                <div className="font-semibold text-emerald-300 mb-1.5 flex items-center gap-1">
                  <ArrowRight className="h-3 w-3" />
                  <span>Tailored for Target Role</span>
                </div>
                {Array.isArray(item.tailored) ? (
                  <ul className="list-disc list-inside space-y-1 text-slate-200">
                    {item.tailored.map((b, i) => (
                      <li key={i} className="leading-relaxed font-medium">
                        {b}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-slate-200 leading-relaxed font-mono font-medium">{item.tailored}</p>
                )}
              </div>
            </div>

            {/* Strategic Rationale */}
            <div className="mt-3 flex items-start gap-2 rounded-lg bg-slate-950/50 p-2.5 text-xs text-slate-300">
              <Info className="h-3.5 w-3.5 text-blue-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-blue-400">Alignment Rationale: </span>
                {item.reason}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
