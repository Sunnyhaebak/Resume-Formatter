"use client";

import React, { useState } from "react";
import { Sparkles, FileText, CheckCircle2, ArrowRight, Wand2, ShieldAlert } from "lucide-react";

interface InputPanelProps {
  jobDescription: string;
  setJobDescription: (val: string) => void;
  customInstructions: string;
  setCustomInstructions: (val: string) => void;
  onTailor: () => void;
  isLoading: boolean;
  onSelectTab?: (tab: "input" | "diff" | "pdf") => void;
}

const PRESET_CHIPS = [
  {
    label: "Backend & Distributed Systems",
    instruction:
      "Emphasize enterprise microservices at Nielsen, REST APIs, Redis caching (CPU dropped 60% to 22%), and high-concurrency database transactions.",
  },
  {
    label: "AI, Semantic Search & RAG",
    instruction:
      "Highlight OpenSearch RAG pipeline over 226M records, Titan v2 embeddings, MCP server development with 10+ tools, and Langfuse tracing (33% token reduction).",
  },
  {
    label: "Full-Stack & React Admin",
    instruction:
      "Promote full-stack development, self-service React Admin Console, Next.js, NestJS backend, and real-time Socket.IO communication.",
  },
  {
    label: "Cloud, AWS & Async Workers",
    instruction:
      "Showcase AWS SDK v2 to v3 migration, S3/EC2/Bedrock/OpenSearch, asynchronous FastAPI workers processing 10K+ daily jobs via RabbitMQ, and Docker.",
  },
];

export default function InputPanel({
  jobDescription,
  setJobDescription,
  customInstructions,
  setCustomInstructions,
  onTailor,
  isLoading,
}: InputPanelProps) {
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);

  const handleChipClick = (label: string, text: string) => {
    setSelectedPreset(label);
    setCustomInstructions(text);
  };

  const sampleJD = `Backend / Full-Stack Engineer (Node.js, FastAPI, Distributed Systems & RAG)
We are looking for a Software Engineer to design high-throughput microservices and generative AI integrations.
Requirements:
- Production experience building and maintaining enterprise REST APIs and distributed microservices.
- Solid experience in Node.js/NestJS, Python (FastAPI), or Spring Boot with PostgreSQL/Redis.
- Hands-on experience with cloud infrastructure (AWS S3, EC2) and asynchronous pipelines (RabbitMQ).
- Familiarity with Vector Search, Semantic Retrieval, RAG architectures, or LLM agent tool calling.
- Passion for performance debugging, query optimization, and clean architectural design.`;

  return (
    <div className="flex flex-col gap-5">
      {/* Verified Master Resume Card */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600/20 text-blue-400">
              <FileText className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-slate-200">Sunny Patel</span>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-400 border border-emerald-500/20">
                  <CheckCircle2 className="h-3 w-3" /> Verified Master Resume
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Nielsen (18 Mo) $\cdot$ 3 Key Projects $\cdot$ 5 Categorized Skill Stacks $\cdot$ Strict 1-Page LaTeX
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              setJobDescription(sampleJD);
              setCustomInstructions(PRESET_CHIPS[0].instruction);
              setSelectedPreset(PRESET_CHIPS[0].label);
            }}
            className="text-xs text-blue-400 hover:text-blue-300 font-medium underline underline-offset-2 transition-colors cursor-pointer"
          >
            Load Sample JD
          </button>
        </div>
      </div>

      {/* Target Job Description Area */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <label htmlFor="jd-input" className="text-sm font-medium text-slate-200 flex items-center gap-1.5">
            <span>Target Job Description (JD)</span>
            <span className="text-rose-400">*</span>
          </label>
          <span className="text-xs text-slate-400">
            {jobDescription.length > 0 ? `${jobDescription.split(/\s+/).filter(Boolean).length} words` : "Paste raw text"}
          </span>
        </div>
        <textarea
          id="jd-input"
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Paste full job description from LinkedIn, Indeed, or Greenhouse here..."
          rows={7}
          className="w-full rounded-xl border border-slate-800 bg-slate-900/90 p-3.5 text-sm text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all font-mono leading-relaxed resize-y"
        />
      </div>

      {/* Custom AI Instructions & Presets */}
      <div className="flex flex-col gap-2.5">
        <div className="flex items-center justify-between">
          <label htmlFor="instructions-input" className="text-sm font-medium text-slate-200 flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-amber-400" />
            <span>Custom AI Instructions</span>
            <span className="text-xs text-slate-400 font-normal">(Optional High-Priority Guidance)</span>
          </label>
        </div>
        <input
          id="instructions-input"
          type="text"
          value={customInstructions}
          onChange={(e) => {
            setCustomInstructions(e.target.value);
            setSelectedPreset(null);
          }}
          placeholder="e.g., Emphasize Spring Boot, microservices, and RAG architectures at Nielsen..."
          className="w-full rounded-lg border border-slate-800 bg-slate-900/90 px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all"
        />

        {/* Quick-fill preset chips */}
        <div className="flex flex-wrap gap-1.5 pt-1">
          <span className="text-xs text-slate-400 self-center mr-1">Quick Presets:</span>
          {PRESET_CHIPS.map((chip) => (
            <button
              key={chip.label}
              type="button"
              onClick={() => handleChipClick(chip.label, chip.instruction)}
              className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-all cursor-pointer border ${
                selectedPreset === chip.label
                  ? "bg-blue-600 text-white border-blue-500 shadow-sm shadow-blue-500/25"
                  : "bg-slate-900/80 text-slate-300 border-slate-800 hover:border-slate-700 hover:text-white"
              }`}
            >
              {chip.label}
            </button>
          ))}
        </div>
      </div>

      {/* Strict Anti-Hallucination Guard Callout */}
      <div className="flex items-start gap-2.5 rounded-lg border border-slate-800/80 bg-slate-900/40 p-3 text-xs text-slate-400">
        <ShieldAlert className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-300">Truthful Production Framing:</span> Reframes production metrics and stack priorities around JD concepts without ever inventing fictional roles or companies. Strictly fit on Sunny&apos;s custom single-page LaTeX template.
        </div>
      </div>

      {/* Tailor Action Button */}
      <button
        type="button"
        disabled={isLoading || !jobDescription.trim()}
        onClick={onTailor}
        className={`relative mt-2 flex items-center justify-center gap-2 rounded-xl py-3.5 px-6 font-semibold text-sm transition-all shadow-lg cursor-pointer ${
          isLoading || !jobDescription.trim()
            ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50"
            : "bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-500 hover:to-indigo-500 text-white shadow-blue-900/30 hover:shadow-blue-700/40 border border-blue-400/30"
        }`}
      >
        {isLoading ? (
          <>
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            <span>Tailoring with Gemini & Compiling LaTeX...</span>
          </>
        ) : (
          <>
            <Wand2 className="h-4 w-4" />
            <span>Generate Tailored 1-Page Resume</span>
            <ArrowRight className="h-4 w-4" />
          </>
        )}
      </button>
    </div>
  );
}
