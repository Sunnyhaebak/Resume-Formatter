"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Sparkles,
  FileText,
  GitCompare,
  Eye,
  CheckCircle2,
  AlertCircle,
  Cpu,
} from "lucide-react";
import InputPanel from "@/components/InputPanel";
import DiffPanel, { DiffItem } from "@/components/DiffPanel";
import PdfPreview from "@/components/PdfPreview";

export interface Basics {
  name: string;
  title?: string;
  phone: string;
  email: string;
  linkedin: string;
  github: string;
  leetcode?: string;
  location?: string;
}

export interface Education {
  institution: string;
  degree: string;
  gpa?: string;
  graduation_date: string;
  location?: string;
  coursework?: string;
}

export interface Skills {
  backend_ai: string[];
  frontend: string[];
  languages: string[];
  cloud_data: string[];
  practices: string[];
}

export interface ExperienceItem {
  id: string;
  company: string;
  role: string;
  duration: string;
  location: string;
  bullets: string[];
}

export interface ProjectItem {
  id: string;
  name: string;
  tech_stack: string;
  link?: string;
  bullets: string[];
}

export interface TailoredResume {
  basics: Basics;
  summary?: string;
  skills: Skills;
  experience: ExperienceItem[];
  projects: ProjectItem[];
  achievements?: string[];
  education: Education[];
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function ResumeTailorDashboard() {
  const searchParams = useSearchParams();

  // State
  const [jobDescription, setJobDescription] = useState("");
  const [jobUrl, setJobUrl] = useState("");
  const [customInstructions, setCustomInstructions] = useState("");
  const [activeTab, setActiveTab] = useState<"input" | "diff" | "pdf">("input");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Response state
  const [pdfBase64, setPdfBase64] = useState<string | null>(null);
  const [pageCount, setPageCount] = useState<number>(1);
  const [changesSummary, setChangesSummary] = useState<DiffItem[]>([]);
  const [latexSource, setLatexSource] = useState<string | null>(null);
  const [tailoredData, setTailoredData] = useState<TailoredResume | null>(null);
  const [downloadFilename, setDownloadFilename] = useState("Sunny_Patel_Tailored_Resume.pdf");

  // Pre-fill from PWA Web Share Target (Android share sheet from LinkedIn/Naukri)
  useEffect(() => {
    const sharedText =
      searchParams.get("jd") ||
      searchParams.get("text") ||
      searchParams.get("title");
    if (sharedText) {
      setJobDescription((prev) => (prev ? prev : sharedText));
      setActiveTab("input");
    }
  }, [searchParams]);

  const handleTailor = async () => {
    if (!jobDescription.trim() && !jobUrl.trim()) return;

    setIsLoading(true);
    setErrorMsg(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/tailor`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          job_description: jobDescription,
          job_url: jobUrl.trim() || null,
          custom_instructions: customInstructions || null,
        }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        throw new Error(
          errJson?.detail || `API request failed with status ${res.status}`
        );
      }

      const data = await res.json();
      setPdfBase64(data.pdf_base64);
      setPageCount(data.page_count);
      setChangesSummary(data.changes_summary || []);
      setLatexSource(data.latex_source || null);
      setTailoredData(data.tailored_data || null);
      setDownloadFilename(data.download_filename || "Sunny_Patel_Tailored_Resume.pdf");

      // On mobile, auto-switch to preview
      if (typeof window !== "undefined" && window.innerWidth < 768) {
        setActiveTab("pdf");
      }
    } catch (err: any) {
      console.error("Tailor error:", err);
      setErrorMsg(
        err.message ||
          "Failed to connect to the backend tailoring service. Verify that the backend is running on port 8000."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 text-white shadow-md shadow-blue-500/20">
              <Cpu className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold tracking-tight text-white sm:text-lg">
                  ResumeTailor <span className="text-blue-500">AI</span>
                </h1>
                <span className="rounded-md bg-blue-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-blue-400 border border-blue-500/20">
                  LaTeX PWA
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Truthful Framing · Gemini Structured Outputs · Strict 1-Page LaTeX & PDF
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-1.5 rounded-full bg-slate-900 border border-slate-800 px-3 py-1 text-xs text-slate-300">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Engine Active</span>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Tab Switcher (< md) */}
      <div className="md:hidden sticky top-[61px] z-30 border-b border-slate-800 bg-slate-950/95 backdrop-blur-sm px-3 py-2">
        <div className="grid grid-cols-3 gap-1 rounded-xl bg-slate-900/90 p-1 border border-slate-800 text-xs font-medium">
          <button
            type="button"
            onClick={() => setActiveTab("input")}
            className={`flex items-center justify-center gap-1.5 rounded-lg py-2 transition-all cursor-pointer ${
              activeTab === "input"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <FileText className="h-3.5 w-3.5" />
            <span>1. Context</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("diff")}
            className={`flex items-center justify-center gap-1.5 rounded-lg py-2 transition-all cursor-pointer ${
              activeTab === "diff"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <GitCompare className="h-3.5 w-3.5" />
            <span>2. Diff {changesSummary.length > 0 && `(${changesSummary.length})`}</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("pdf")}
            className={`flex items-center justify-center gap-1.5 rounded-lg py-2 transition-all cursor-pointer ${
              activeTab === "pdf"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Eye className="h-3.5 w-3.5" />
            <span>3. Preview</span>
          </button>
        </div>
      </div>

      {/* Main Responsive Body */}
      <main className="flex-1 mx-auto w-full max-w-7xl p-4 sm:p-6">
        {/* Error Notification Banner */}
        {errorMsg && (
          <div className="mb-5 flex items-start gap-3 rounded-xl border border-rose-500/30 bg-rose-950/30 p-4 text-xs text-rose-300">
            <AlertCircle className="h-5 w-5 text-rose-400 shrink-0" />
            <div className="flex-1">
              <p className="font-semibold text-rose-200">Processing Error</p>
              <p className="mt-0.5 leading-relaxed">{errorMsg}</p>
            </div>
            <button
              type="button"
              onClick={() => setErrorMsg(null)}
              className="text-rose-400 hover:text-white cursor-pointer"
            >
              ✕
            </button>
          </div>
        )}

        {/* Desktop Split-View (md:grid-cols-12) */}
        <div className="hidden md:grid md:grid-cols-12 md:gap-6 items-start">
          {/* Left Column: Context Input + Strategic AI Diff */}
          <div className="md:col-span-6 flex flex-col gap-6">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-4 border-b border-slate-800/80 pb-3">
                <Sparkles className="h-4 w-4 text-blue-400" />
                <h2 className="text-sm font-semibold text-slate-100">
                  Target Role & Custom Instructions
                </h2>
              </div>
              <InputPanel
                jobDescription={jobDescription}
                setJobDescription={setJobDescription}
                jobUrl={jobUrl}
                setJobUrl={setJobUrl}
                customInstructions={customInstructions}
                setCustomInstructions={setCustomInstructions}
                onTailor={handleTailor}
                isLoading={isLoading}
              />
            </div>

            {/* Diff Panel on Desktop */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-4 border-b border-slate-800/80 pb-3">
                <GitCompare className="h-4 w-4 text-emerald-400" />
                <h2 className="text-sm font-semibold text-slate-100">
                  AI Adaptations & Truthful Framing Diff
                </h2>
              </div>
              <DiffPanel
                changesSummary={changesSummary}
                pageCount={pageCount}
              />
            </div>
          </div>

          {/* Right Column: Sticky Live PDF Preview */}
          <div className="md:col-span-6 sticky top-[73px]">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm min-h-[750px] flex flex-col">
              <div className="flex items-center justify-between mb-4 border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2">
                  <Eye className="h-4 w-4 text-sky-400" />
                  <h2 className="text-sm font-semibold text-slate-100">
                    Compiled LaTeX & Visual Preview
                  </h2>
                </div>
                {pdfBase64 && (
                  <span className="flex items-center gap-1 text-xs text-emerald-400 font-medium">
                    <CheckCircle2 className="h-3.5 w-3.5" /> 1-Page Verified
                  </span>
                )}
              </div>
              <div className="flex-1 flex flex-col">
                <PdfPreview
                  pdfBase64={pdfBase64}
                  pageCount={pageCount}
                  latexSource={latexSource}
                  tailoredData={tailoredData}
                  downloadFilename={downloadFilename}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Mobile Tabbed View (< md) */}
        <div className="md:hidden">
          {activeTab === "input" && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 shadow-sm">
              <InputPanel
                jobDescription={jobDescription}
                setJobDescription={setJobDescription}
                jobUrl={jobUrl}
                setJobUrl={setJobUrl}
                customInstructions={customInstructions}
                setCustomInstructions={setCustomInstructions}
                onTailor={handleTailor}
                isLoading={isLoading}
                onSelectTab={setActiveTab}
              />
            </div>
          )}

          {activeTab === "diff" && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 shadow-sm">
              <DiffPanel
                changesSummary={changesSummary}
                pageCount={pageCount}
              />
            </div>
          )}

          {activeTab === "pdf" && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 shadow-sm">
              <PdfPreview
                pdfBase64={pdfBase64}
                pageCount={pageCount}
                latexSource={latexSource}
                tailoredData={tailoredData}
                downloadFilename={downloadFilename}
                onOpenInputTab={() => setActiveTab("input")}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-slate-950 text-slate-400 text-sm">
          Loading ResumeTailor AI Engine...
        </div>
      }
    >
      <ResumeTailorDashboard />
    </Suspense>
  );
}
