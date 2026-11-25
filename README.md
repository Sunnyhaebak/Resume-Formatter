# AI-Powered LaTeX Resume Tailoring Engine (Desktop + Mobile PWA)

A full-stack, mobile-responsive Progressive Web App (PWA) and containerized backend that accepts a raw Job Description (JD) and optional custom instructions, applies truthful transferable framing using Google Gemini API structured outputs, sanitizes LaTeX reserved characters, renders a single-page LaTeX template via Jinja2, and compiles a strictly 1-page PDF using `pdflatex`.

---

## 1. System Architecture

```
                                  +------------------------------------+
                                  |     Desktop & Mobile PWA (Next.js) |
                                  |  - Desktop: 2-column split view    |
                                  |  - Mobile: 3-tab layout (< md)     |
                                  |  - Web Share Target API (Android)  |
                                  +-----------------+------------------+
                                                    | POST /api/tailor
                                                    v
+--------------------------------------------------------------------------------------------------------+
|                                    Backend Engine (FastAPI + Docker)                                   |
|                                                                                                        |
|  1. Master Resume JSON  ---> 2. Gemini Tailoring Engine ---> 3. LaTeX Sanitizer ---> 4. Jinja2 Render  |
|     (Verified Candidate)       (Transferable Framing &         (Escapes &, %, $,        (Custom Non-   |
|                                 Zero-Fabrication Guard)         #, _, {, }, ~, ^, \)     Colliding Tags)
|                                                                                             |          |
|                                                                                             v          |
|  7. JSON Diff + PDF64   <--- 6. 1-Page Overflow Guard   <--- 5. pdflatex Compilation <------+          |
|     (Transparent Diff &         (Trims 15% verbosity if         (texlive-latex-base)                   |
|      Single-Page PDF)            page count > 1)                                                       |
+--------------------------------------------------------------------------------------------------------+
```

---

## 2. Directory Layout

```text
├── backend/
│   ├── Dockerfile                   # Multi-stage image with Python 3.12 & TeX Live
│   ├── requirements.txt             # FastAPI, Uvicorn, Pydantic v2, Jinja2, pypdf, google-genai
│   ├── .env.example                 # GEMINI_API_KEY, PORT, ALLOWED_ORIGINS
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, POST /api/tailor
│   │   ├── schemas.py               # Pydantic v2 request/response and diff models
│   │   ├── llm_service.py           # Gemini Structured Outputs + Anti-Hallucination rules
│   │   ├── latex_service.py         # Character escaper, Jinja2 renderer, pdflatex runner
│   │   └── data/
│   │       ├── master_resume.json   # Verified superset of candidate experience
│   │       └── resume_template.tex  # Single-page Helvetica/Navy LaTeX template
│   └── tests/
│       └── test_pipeline.py         # Pytest verifying sanitization, 1-page PDF & endpoints
└── frontend/
    ├── package.json                 # Next.js 16, React 19, Tailwind CSS, Lucide React
    ├── next.config.ts
    ├── public/
    │   ├── icon-192x192.png         # PWA icon
    │   └── icon-512x512.png         # PWA high-res icon
    └── src/
        ├── app/
        │   ├── layout.tsx           # Global layout with PWA metadata
        │   ├── page.tsx             # Responsive desktop split / mobile tabbed view
        │   └── manifest.ts          # Native PWA manifest + Web Share Target
        └── components/
            ├── InputPanel.tsx       # JD textarea, custom instructions & quick presets
            ├── DiffPanel.tsx        # Transparent original vs. tailored diff viewer
            └── PdfPreview.tsx       # Embedded PDF iframe, Share & Download
```

---

## 3. Quickstart & Local Development

### Free-Tier Deployment

The recommended split is a Vercel Hobby frontend and a Render Free Docker backend. The backend uses the included TeX Live packages so deployed PDFs use the LaTeX template.

1. Push the project to a private or public GitHub repository. Do not commit `backend/.env`; rotate the Gemini key previously used locally, then add the replacement only as a Render secret.
2. In Render, create a Blueprint from the repository root. Render reads `render.yaml`; provide `GEMINI_API_KEY` and temporarily set `ALLOWED_ORIGINS` to `*` for the first deployment.
3. In Vercel, import the same repository and set the project root to `frontend`. Add `NEXT_PUBLIC_API_URL` with the deployed Render service URL (for example, `https://resume-tailor-api.onrender.com`) and deploy.
4. Copy the Vercel production URL into Render's `ALLOWED_ORIGINS` setting, replacing `*`, then redeploy the backend.

Free Render services sleep after 15 minutes without traffic and can take about a minute to wake. They have 512 MB RAM and limited monthly service hours; the TeX Live image may make initial builds slower or exceed free-tier resources. Vercel Hobby and Render Free limits can change, so check each provider's current plan details.

### Prerequisites
- Python 3.12+ (Python 3.14 installed on host with all dependencies pre-installed)
- Node.js 18+ (Node 20+ installed on host with all dependencies pre-installed)
- Optional for local PDF compilation: `pdflatex` (TeX Live or MiKTeX). If not installed locally, a graceful fallback PDF is generated, and full `pdflatex` runs inside the Docker container.

### ⚡ 1-Click Launch (Recommended for Windows)
Simply run or double-click:
```cmd
run_all.bat
```
This automatically starts both the FastAPI Backend (port 8000) and Next.js Frontend (port 3000), and opens `http://localhost:3000` in your browser.

Or run individually:
- Backend: `run_backend.bat` (or in PowerShell: `.\run_backend.ps1`)
- Frontend: `run_frontend.bat` (or in PowerShell: `.\run_frontend.ps1`)

### Manual Setup (Cross-Platform)

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Optional: Add your GEMINI_API_KEY to .env

# Run unit tests
pytest tests/test_pipeline.py -v

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run build
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 4. Key Engineering Features

1. **Strict Zero-Fabrication Rule:** The LLM cannot invent dates, companies, metrics, or technologies not present in `master_resume.json`.
2. **Transferable Framing:** If applying to an adjacent role (e.g. Node.js engineer applying to a Java/Spring role), bullets are reframed around shared architectural concepts (distributed microservices, event streams, caching, ACID transactions) without falsely claiming fictional tool usage.
3. **LaTeX Reserved Character Sanitization:** Recursively escapes special characters (`&`, `%`, `$`, `#`, `_`, `{`, `}`, `~`, `^`, `\`) so strings like `C#`, `100%`, and `R&D` compile cleanly.
4. **1-Page Overflow Guard:** Uses `pypdf` to inspect page count after compilation. If page count exceeds 1, an automatic retry pass trims bullet verbosity by 15% and recompiles.
5. **Mobile PWA & Web Share Target:** Android users can share a job description directly from LinkedIn or job boards into the PWA via the Android native Share sheet (`share_target` API in `manifest.ts`).
