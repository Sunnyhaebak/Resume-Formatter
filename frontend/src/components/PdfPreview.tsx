"use client";

import React, { useState, useEffect } from "react";
import {
  Download,
  Share2,
  FileCode,
  Check,
  Copy,
  ExternalLink,
  ShieldCheck,
  Eye,
  FileText,
  FileCheck2,
} from "lucide-react";
import { TailoredResume } from "@/app/page";

interface PdfPreviewProps {
  pdfBase64: string | null;
  pageCount: number;
  latexSource?: string | null;
  tailoredData?: TailoredResume | null;
  downloadFilename?: string;
  onOpenInputTab?: () => void;
}

export default function PdfPreview({
  pdfBase64,
  pageCount,
  latexSource,
  tailoredData,
  downloadFilename = "Sunny_Patel_Tailored_Resume.pdf",
  onOpenInputTab,
}: PdfPreviewProps) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<"visual" | "pdf" | "latex">("visual");
  const [copiedLatex, setCopiedLatex] = useState(false);
  const [shareSuccess, setShareSuccess] = useState(false);

  // Generate a clean Blob URL from Base64 for native browser PDF rendering
  useEffect(() => {
    if (!pdfBase64) {
      setBlobUrl(null);
      return;
    }
    try {
      const byteCharacters = atob(pdfBase64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      setBlobUrl(url);

      return () => {
        URL.revokeObjectURL(url);
      };
    } catch (err) {
      console.error("Failed to build PDF Blob URL:", err);
    }
  }, [pdfBase64]);

  const handleDownload = () => {
    if (!pdfBase64) return;
    const link = document.createElement("a");
    link.href = blobUrl || `data:application/pdf;base64,${pdfBase64}`;
    link.download = downloadFilename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleOpenPdfNewTab = () => {
    if (blobUrl) {
      window.open(blobUrl, "_blank");
    }
  };

  const handleShare = async () => {
    if (!blobUrl && !pdfBase64) return;

    try {
      const byteCharacters = atob(pdfBase64!);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const file = new File([byteArray], downloadFilename, {
        type: "application/pdf",
      });

      if (
        typeof navigator !== "undefined" &&
        navigator.canShare &&
        navigator.canShare({ files: [file] })
      ) {
        await navigator.share({
          files: [file],
          title: "Sunny Patel - Tailored Resume",
          text: "Here is my tailored single-page resume.",
        });
        setShareSuccess(true);
        setTimeout(() => setShareSuccess(false), 3000);
      } else {
        handleDownload();
      }
    } catch (err: any) {
      if (err.name !== "AbortError") {
        handleDownload();
      }
    }
  };

  const handleCopyLatex = async () => {
    if (!latexSource) return;
    try {
      await navigator.clipboard.writeText(latexSource);
      setCopiedLatex(true);
      setTimeout(() => setCopiedLatex(false), 2500);
    } catch {
      // ignore
    }
  };

  // Helper to format text with bold tags
  const renderFormattedText = (text: string) => {
    if (!text) return null;
    const clean = text
      .replace(/\\textbf\{([^}]+)\}/g, "<strong>$1</strong>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\\%/g, "%")
      .replace(/\\&/g, "&")
      .replace(/\\\$/g, "$")
      .replace(/\\#/g, "#")
      .replace(/\\_/g, "_");

    return <span dangerouslySetInnerHTML={{ __html: clean }} />;
  };

  if (!pdfBase64) {
    return (
      <div className="flex h-full min-h-[520px] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 p-8 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-600/10 text-blue-400 mb-4 border border-blue-500/20 shadow-inner">
          <FileCheck2 className="h-8 w-8" />
        </div>
        <h3 className="text-base font-semibold text-slate-200">No Resume Generated Yet</h3>
        <p className="mt-2 max-w-sm text-xs text-slate-400 leading-relaxed">
          Paste the target job description and click &ldquo;Generate Tailored 1-Page Resume&rdquo; to compile your customized resume draft.
        </p>
        {onOpenInputTab && (
          <button
            type="button"
            onClick={onOpenInputTab}
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-slate-800 hover:bg-slate-700 px-4 py-2 text-xs font-medium text-slate-200 transition-colors cursor-pointer"
          >
            <span>Start Tailoring Now</span>
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full gap-3">
      {/* Top Action & Verification Bar */}
      <div className="flex items-center justify-between flex-wrap gap-2.5 rounded-xl border border-slate-800 bg-slate-900/80 p-3">
        {/* View Switcher Tabs */}
        <div className="flex items-center gap-1 rounded-lg bg-slate-950 p-1 border border-slate-800 text-xs">
          <button
            type="button"
            onClick={() => setActiveView("visual")}
            className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 font-medium transition-all cursor-pointer ${
              activeView === "visual"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Eye className="h-3.5 w-3.5" />
            <span>Visual Draft</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveView("pdf")}
            className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 font-medium transition-all cursor-pointer ${
              activeView === "pdf"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <FileText className="h-3.5 w-3.5" />
            <span>PDF Viewer</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveView("latex")}
            className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 font-medium transition-all cursor-pointer ${
              activeView === "latex"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <FileCode className="h-3.5 w-3.5 text-sky-400" />
            <span>LaTeX Source</span>
          </button>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-1.5">
          {blobUrl && (
            <button
              type="button"
              onClick={handleOpenPdfNewTab}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 px-2.5 py-1.5 text-xs font-medium text-slate-300 transition-colors cursor-pointer"
              title="Open full PDF in a new browser tab"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Full PDF</span>
            </button>
          )}

          <button
            type="button"
            onClick={handleShare}
            className="inline-flex items-center gap-1 rounded-lg border border-blue-500/30 bg-blue-600/20 hover:bg-blue-600/30 px-3 py-1.5 text-xs font-medium text-blue-300 transition-colors cursor-pointer"
          >
            {shareSuccess ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-emerald-300">Shared!</span>
              </>
            ) : (
              <>
                <Share2 className="h-3.5 w-3.5" />
                <span>Share</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleDownload}
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 px-3.5 py-1.5 text-xs font-semibold text-white shadow-md shadow-blue-700/20 transition-all cursor-pointer"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Download PDF</span>
          </button>
        </div>
      </div>

      {/* Main Container */}
      <div className="relative flex-1 min-h-[640px] w-full rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden shadow-2xl flex flex-col">
        {/* 1. VISUAL DRAFT (Exact Sunny Patel LaTeX Layout in HTML) */}
        {activeView === "visual" && tailoredData && (
          <div className="h-full overflow-y-auto bg-slate-900/90 p-4 sm:p-6 flex justify-center">
            <div className="w-full max-w-[800px] bg-white text-[#1A1A1A] rounded-xl shadow-2xl p-6 sm:p-8 font-sans text-[11px] leading-relaxed border border-slate-300">
              {/* Header */}
              <div className="mb-2">
                <h1 className="text-[19px] font-bold text-[#0F2442] tracking-tight">
                  {tailoredData.basics.name}
                </h1>
                <p className="text-[10.5px] font-medium text-[#1D4E89] mt-0.5">
                  {tailoredData.basics.title || "Software Engineer • Backend & Full-Stack Systems"}
                </p>
                <div className="text-[9.5px] text-[#1A1A1A] mt-1 flex flex-wrap items-center gap-1.5">
                  <span className="text-[#1D4E89] font-medium">{tailoredData.basics.email}</span>
                  <span className="text-[#666666]">|</span>
                  <span>{tailoredData.basics.phone}</span>
                  <span className="text-[#666666]">|</span>
                  <span className="text-[#1D4E89] font-medium">LinkedIn</span>
                  <span className="text-[#666666]">|</span>
                  <span className="text-[#1D4E89] font-medium">GitHub</span>
                  {tailoredData.basics.leetcode && (
                    <>
                      <span className="text-[#666666]">|</span>
                      <span className="text-[#1D4E89] font-medium">LeetCode</span>
                    </>
                  )}
                </div>
                <div className="w-full h-[1.3px] bg-[#0F2442] mt-2 mb-2" />
              </div>

              {/* Summary */}
              {tailoredData.summary && (
                <div className="mb-2.5">
                  <div className="text-[10px] font-bold text-[#0F2442] uppercase tracking-wider mb-0.5">
                    SUMMARY
                  </div>
                  <div className="w-full h-[0.8px] bg-[#0F2442] mb-1" />
                  <p className="text-[9.5px] text-[#1A1A1A] leading-relaxed">
                    {renderFormattedText(tailoredData.summary)}
                  </p>
                </div>
              )}

              {/* Technical Skills */}
              <div className="mb-2.5">
                <div className="text-[10px] font-bold text-[#0F2442] uppercase tracking-wider mb-0.5">
                  TECHNICAL SKILLS
                </div>
                <div className="w-full h-[0.8px] bg-[#0F2442] mb-1.5" />
                <div className="grid grid-cols-[110px_1fr] gap-x-2 gap-y-0.5 text-[9.5px]">
                  <span className="font-bold text-[#1A1A1A]">Backend & AI:</span>
                  <span className="text-[#374151]">{tailoredData.skills.backend_ai.join(", ")}</span>
                  <span className="font-bold text-[#1A1A1A]">Frontend:</span>
                  <span className="text-[#374151]">{tailoredData.skills.frontend.join(", ")}</span>
                  <span className="font-bold text-[#1A1A1A]">Languages:</span>
                  <span className="text-[#374151]">{tailoredData.skills.languages.join(", ")}</span>
                  <span className="font-bold text-[#1A1A1A]">Cloud & Data:</span>
                  <span className="text-[#374151]">{tailoredData.skills.cloud_data.join(", ")}</span>
                  <span className="font-bold text-[#1A1A1A]">Practices:</span>
                  <span className="text-[#374151]">{tailoredData.skills.practices.join(", ")}</span>
                </div>
              </div>

              {/* Experience (Nielsen - Exactly 8 Bullets) */}
              <div className="mb-2.5">
                <div className="text-[10px] font-bold text-[#0F2442] uppercase tracking-wider mb-0.5">
                  EXPERIENCE
                </div>
                <div className="w-full h-[0.8px] bg-[#0F2442] mb-1.5" />
                {tailoredData.experience.map((exp) => (
                  <div key={exp.id} className="mb-1.5">
                    <div className="flex justify-between items-baseline text-[10px]">
                      <span className="font-bold text-[#1A1A1A]">{exp.company}</span>
                      <span className="font-bold text-[#1A1A1A]">{exp.location}</span>
                    </div>
                    <div className="flex justify-between items-baseline text-[9.5px] italic text-[#2D3748] mb-1">
                      <span>{exp.role}</span>
                      <span>{exp.duration}</span>
                    </div>
                    <ul className="space-y-0.5 text-[9.2px] text-[#1A1A1A]">
                      {exp.bullets.slice(0, 8).map((b, i) => (
                        <li key={i} className="flex items-start gap-1.5 leading-snug">
                          <span className="text-[#1D4E89] text-[8px] leading-tight mt-0.5">•</span>
                          <span>{renderFormattedText(b)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>

              {/* Projects (Project 1: Company Clone, Project 2: Telemed, Project 3: Field Service) */}
              <div className="mb-2.5">
                <div className="text-[10px] font-bold text-[#0F2442] uppercase tracking-wider mb-0.5">
                  PROJECTS
                </div>
                <div className="w-full h-[0.8px] bg-[#0F2442] mb-1.5" />
                <div className="space-y-2">
                  {tailoredData.projects.slice(0, 3).map((proj, idx) => (
                    <div key={proj.id || idx}>
                      <div className="flex items-baseline gap-1.5 text-[9.8px]">
                        <span className="font-bold text-[#1A1A1A]">{proj.name}</span>
                        <span className="text-[#666666]">|</span>
                        <span className="italic text-[#374151] font-medium">{proj.tech_stack}</span>
                      </div>
                      <ul className="mt-0.5 space-y-0.5 text-[9.2px] text-[#1A1A1A]">
                        {proj.bullets.map((b, bi) => (
                          <li key={bi} className="flex items-start gap-1.5 leading-snug">
                            <span className="text-[#1D4E89] text-[8px] leading-tight mt-0.5">•</span>
                            <span>{renderFormattedText(b)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>

              {/* Achievements */}
              {tailoredData.achievements && tailoredData.achievements.length > 0 && (
                <div className="mb-2">
                  <div className="text-[10px] font-bold text-[#0F2442] uppercase tracking-wider mb-0.5">
                    ACHIEVEMENTS & CERTIFICATIONS
                  </div>
                  <div className="w-full h-[0.8px] bg-[#0F2442] mb-1" />
                  <ul className="space-y-0.5 text-[9.2px] text-[#1A1A1A]">
                    {tailoredData.achievements.slice(0, 4).map((ach, ai) => (
                      <li key={ai} className="flex items-start gap-1.5 leading-snug">
                        <span className="text-[#1D4E89] text-[8px] leading-tight mt-0.5">•</span>
                        <span>{renderFormattedText(ach)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Education */}
              <div>
                <div className="text-[10px] font-bold text-[#0F2442] uppercase tracking-wider mb-0.5">
                  EDUCATION
                </div>
                <div className="w-full h-[0.8px] bg-[#0F2442] mb-1" />
                {tailoredData.education.map((edu, ei) => (
                  <div key={ei}>
                    <div className="flex justify-between items-baseline text-[10px]">
                      <span className="font-bold text-[#1A1A1A]">{edu.institution}</span>
                      <span className="font-bold text-[#1A1A1A]">{edu.location || "Punjab, India"}</span>
                    </div>
                    <div className="flex justify-between items-baseline text-[9.5px] italic text-[#2D3748]">
                      <span>{edu.degree}</span>
                      <span>{edu.graduation_date}</span>
                    </div>
                    {edu.coursework && (
                      <div className="text-[8.5px] italic text-[#374151] mt-0.5">
                        Relevant Coursework: {edu.coursework}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 2. PDF VIEWER (Direct Native Blob URL iframe) */}
        {activeView === "pdf" && (
          <div className="h-full flex-1 flex flex-col bg-slate-900">
            {blobUrl ? (
              <iframe
                src={`${blobUrl}#toolbar=0&navpanes=0`}
                title="Compiled Tailored Resume PDF"
                className="w-full h-full flex-1 border-0"
              />
            ) : (
              <div className="flex h-full items-center justify-center text-slate-400 text-xs">
                Preparing PDF document...
              </div>
            )}
          </div>
        )}

        {/* 3. LATEX CODE VIEW */}
        {activeView === "latex" && (
          <div className="h-full flex flex-col bg-slate-950 p-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
              <span className="text-xs font-semibold text-slate-300">
                Generated LaTeX Source (resume.tex)
              </span>
              <button
                type="button"
                onClick={handleCopyLatex}
                className="inline-flex items-center gap-1 rounded-lg bg-slate-800 hover:bg-slate-700 px-2.5 py-1 text-xs font-medium text-slate-200 transition-colors cursor-pointer"
              >
                {copiedLatex ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    <span>Copy Code</span>
                  </>
                )}
              </button>
            </div>
            <div className="flex-1 overflow-auto rounded-lg bg-slate-900/90 p-4 font-mono text-xs text-slate-300 leading-relaxed">
              <pre className="whitespace-pre-wrap">{latexSource}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
