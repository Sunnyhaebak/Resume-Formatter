import os
import base64
import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.schemas import (
    MasterResume,
    TailorRequest,
    TailorResponse,
)
from app.llm_service import tailor_resume_with_gemini
from app.latex_service import (
    render_latex,
    compile_latex_to_pdf,
    verify_page_count,
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resume_tailor_backend")

app = FastAPI(
    title="AI-Powered LaTeX Resume Tailoring Engine",
    description="Truthful, structured AI resume tailoring with 1-page LaTeX compilation",
    version="1.0.0",
)

# CORS configuration
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [orig.strip() for orig in allowed_origins_raw.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_MASTER_RESUME_PATH = DATA_DIR / "master_resume.json"


def load_default_master_resume() -> MasterResume:
    if not DEFAULT_MASTER_RESUME_PATH.exists():
        raise FileNotFoundError(f"Master resume data missing at {DEFAULT_MASTER_RESUME_PATH}")
    with open(DEFAULT_MASTER_RESUME_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return MasterResume.model_validate(data)


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {
        "status": "healthy",
        "service": "resume-tailor-backend",
        "version": "1.0.0",
    }


@app.get("/api/master-resume", response_model=MasterResume)
def get_master_resume():
    """Returns the verified master resume JSON."""
    return load_default_master_resume()


@app.post("/api/tailor", response_model=TailorResponse)
def tailor_resume_endpoint(request: TailorRequest):
    """
    Main tailoring pipeline:
    1. Validates inputs & loads master resume.
    2. Invokes Gemini LLM with strict anti-hallucination and character-budget prompts.
    3. Escapes LaTeX characters and renders single-page template with Jinja2.
    4. Compiles PDF using pdflatex (or fallback if outside container).
    5. Checks page count; triggers 1-page overflow guard retry if page count > 1.
    6. Returns base64 PDF and changes diff.
    """
    if not request.job_description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description cannot be empty.",
        )

    # 1. Resolve master resume
    master = request.master_resume or load_default_master_resume()

    logger.info("Starting resume tailoring process...")

    # 2. Invoke AI Tailoring Engine
    tailored_result = tailor_resume_with_gemini(
        master_resume=master,
        job_description=request.job_description,
        custom_instructions=request.custom_instructions,
        trim_percentage=0,
    )

    # 3. Render LaTeX
    rendered_tex = render_latex(tailored_result.tailored_resume)

    # 4. Compile PDF
    try:
        pdf_bytes = compile_latex_to_pdf(rendered_tex, tailored_resume=tailored_result.tailored_resume)
    except Exception as e:
        logger.error(f"LaTeX compilation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LaTeX compilation error: {str(e)}",
        )

    # 5. 1-Page Overflow Guard
    page_count = verify_page_count(pdf_bytes)
    logger.info(f"Initial compiled PDF has {page_count} page(s).")

    if page_count > 1:
        logger.warning("PDF exceeds 1 page! Triggering 15% verbosity trimming retry pass...")
        tailored_result = tailor_resume_with_gemini(
            master_resume=master,
            job_description=request.job_description,
            custom_instructions=request.custom_instructions,
            trim_percentage=15,
        )
        rendered_tex = render_latex(tailored_result.tailored_resume)
        pdf_bytes = compile_latex_to_pdf(rendered_tex, tailored_resume=tailored_result.tailored_resume)
        page_count = verify_page_count(pdf_bytes)
        logger.info(f"Retried PDF page count: {page_count}")

    # 6. Encode Base64 and return
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    return TailorResponse(
        pdf_base64=pdf_b64,
        page_count=page_count,
        changes_summary=tailored_result.changes_summary,
        tailored_data=tailored_result.tailored_resume,
        latex_source=rendered_tex,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
