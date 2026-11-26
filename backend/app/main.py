import os
import base64
import json
import logging
import re
import ipaddress
import socket
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx

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


class _VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data).strip()
        if text:
            self.parts.append(text)


def _public_http_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443)}
        for address in addresses:
            ip = ipaddress.ip_address(address)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        return True
    except socket.gaierror:
        return False


def extract_job_post(job_url: str) -> tuple[str, Optional[str], Optional[str]]:
    if not _public_http_url(job_url):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enter a valid public http(s) job-post URL.")

    try:
        response = httpx.get(job_url.strip(), follow_redirects=True, timeout=8.0, headers={
            "User-Agent": "Mozilla/5.0 (compatible; ResumeTailorBot/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        })
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Could not read this job link: {str(exc)}")

    html = response.text
    job_post: dict = {}
    for match in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S):
        try:
            payload = json.loads(match)
        except json.JSONDecodeError:
            continue
        candidates = payload if isinstance(payload, list) else [payload]
        for candidate in candidates:
            if isinstance(candidate, dict) and candidate.get("@type") in {"JobPosting", "Occupation"}:
                job_post = candidate
                break
        if job_post:
            break

    title = job_post.get("title") if job_post else None
    organization = job_post.get("hiringOrganization") if job_post else None
    organization_name = organization.get("name") if isinstance(organization, dict) else None

    if not title:
        match = re.search(r'<meta[^>]+(?:property|name)=["\'](?:og:title|twitter:title)["\'][^>]+content=["\']([^"\']+)', html, re.I)
        if match:
            title = match.group(1)
    if not title:
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        if match:
            title = re.sub(r"<[^>]+>", "", match.group(1)).strip()

    description = job_post.get("description") if job_post else None
    if isinstance(description, str):
        visible = re.sub(r"<[^>]+>", " ", description)
        description = re.sub(r"\s+", " ", visible).strip()

    if not description:
        parser = _VisibleTextParser()
        parser.feed(re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S))
        description = " ".join(parser.parts)

    description = re.sub(r"\s+", " ", description).strip()
    if len(description) < 100:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="The job link returned too little readable job-description text. Paste the description directly instead.")

    return description[:50000], title, organization_name


def _slug(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return cleaned[:50] or fallback


def build_download_filename(title: Optional[str], organization: Optional[str]) -> str:
    post_name = _slug(title or "Job_Post", "Job_Post")
    org_name = _slug(organization or "Organization", "Organization")
    return f"Sunny_Patel_{org_name}_{post_name}_Resume.pdf"


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
    job_description = request.job_description.strip()
    job_title: Optional[str] = None
    organization_name: Optional[str] = None

    job_url = request.job_url.strip() if request.job_url else ""
    if job_url:
        job_description, job_title, organization_name = extract_job_post(job_url)
    elif re.match(r"^https?://", job_description, re.I):
        job_description, job_title, organization_name = extract_job_post(job_description)

    if not job_description.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job description or job-post URL is required.")

    # 1. Resolve master resume
    master = request.master_resume or load_default_master_resume()

    logger.info("Starting resume tailoring process...")

    # 2. Invoke AI Tailoring Engine
    tailored_result = tailor_resume_with_gemini(
        master_resume=master,
        job_description=job_description,
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
            job_description=job_description,
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
        extracted_job_description=job_description,
        download_filename=build_download_filename(job_title, organization_name),
        page_count=page_count,
        changes_summary=tailored_result.changes_summary,
        tailored_data=tailored_result.tailored_resume,
        latex_source=rendered_tex,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
