import base64
import io
import json
from pathlib import Path
import pytest
from pypdf import PdfReader

from app.main import app, load_default_master_resume, tailor_resume_endpoint, get_master_resume, build_download_filename
from app.schemas import (
    MasterResume,
    TailoredResume,
    TailoredResumeResponse,
    DiffItem,
    ExperienceItem,
    ProjectItem,
    Skills,
    Basics,
    Education,
    TailorRequest,
)
from app.latex_service import (
    escape_latex,
    sanitize_for_latex,
    render_latex,
    compile_latex_to_pdf,
    verify_page_count,
)
from app.llm_service import get_mock_tailored_response, tailor_resume_with_gemini


def test_latex_special_character_escaping():
    """
    Verifies that special LaTeX characters like C#, 100%, and R&D
    are properly escaped while preserving bold tags.
    """
    raw_texts = [
        ("C#", r"C\#"),
        ("100%", r"100\%"),
        ("R&D", r"R\&D"),
        ("user_id", r"user\_id"),
        ("$120M+", r"\$120M+"),
        ("{nested}", r"\{nested\}"),
        ("~approx", r"\textasciitilde{}approx"),
        ("^pow", r"\textasciicircum{}pow"),
        ("**12+ REST APIs**", r"\textbf{12+ REST APIs}"),
    ]

    for raw, expected in raw_texts:
        escaped = escape_latex(raw)
        assert escaped == expected, f"Expected {expected}, got {escaped}"


def test_recursive_sanitization():
    """
    Verifies recursive sanitization of nested structures.
    """
    sample = {
        "title": "Senior R&D Engineer (C# / $150k)",
        "skills": ["C#", "100% CI/CD", "PostgreSQL_v15"],
        "nested": {"key": "val & more"}
    }
    sanitized = sanitize_for_latex(sample)
    assert sanitized["title"] == r"Senior R\&D Engineer (C\# / \$150k)"
    assert sanitized["skills"] == [r"C\#", r"100\% CI/CD", r"PostgreSQL\_v15"]
    assert sanitized["nested"]["key"] == r"val \& more"


def test_sunny_patel_template_rendering():
    """
    Verifies that Sunny Patel's master resume renders into the new LaTeX template
    without Jinja2 errors and with all sections intact.
    """
    master = load_default_master_resume()
    assert master.basics.name == "SUNNY PATEL"
    assert master.experience[0].company == "Nielsen"

    tailored_response = tailor_resume_with_gemini(
        master_resume=master,
        job_description="Seeking a Senior Backend / Distributed Systems Engineer with FastAPI, Spring Boot, Redis, and RAG.",
        custom_instructions="Emphasize production microservices and vector search."
    )

    rendered_tex = render_latex(tailored_response.tailored_resume)
    assert r"SUNNY PATEL" in rendered_tex
    assert r"TECHNICAL SKILLS" in rendered_tex
    assert r"EXPERIENCE" in rendered_tex
    assert r"Nielsen" in rendered_tex
    assert r"PROJECTS" in rendered_tex
    assert r"ACHIEVEMENTS" in rendered_tex
    assert r"Lovely Professional University" in rendered_tex


def test_compile_pdf_and_page_count():
    """
    Verifies that the compiled PDF can be generated and verified strictly for 1 page.
    """
    master = load_default_master_resume()
    tailored_response = tailor_resume_with_gemini(
        master_resume=master,
        job_description="Seeking a Backend Engineer with experience in Node.js, FastAPI, AWS S3, and microservices.",
        custom_instructions="Highlight REST APIs and distributed architecture."
    )
    
    rendered_tex = render_latex(tailored_response.tailored_resume)
    pdf_bytes = compile_latex_to_pdf(
        rendered_tex,
        tailored_resume=tailored_response.tailored_resume,
    )
    assert len(pdf_bytes) > 0, "PDF bytes should not be empty"

    page_count = verify_page_count(pdf_bytes)
    assert page_count == 1, f"Expected strictly 1 page, got {page_count}"
    extracted_text = PdfReader(io.BytesIO(pdf_bytes)).pages[0].extract_text()
    assert "SUNNY PATEL" in extracted_text


def test_fastapi_tailor_endpoint():
    """
    End-to-end integration test of POST /api/tailor endpoint logic for Sunny Patel.
    """
    master = get_master_resume()
    assert master.basics.name == "SUNNY PATEL"
    assert "Nielsen" in [e.company for e in master.experience]

    payload = TailorRequest(
        job_description="Backend and Full-Stack Engineer with experience in Spring Boot, NestJS, FastAPI, and OpenSearch RAG.",
        custom_instructions="Highlight transferable microservice architecture and semantic retrieval."
    )

    data = tailor_resume_endpoint(payload)
    assert data.page_count == 1
    assert len(data.changes_summary) > 0
    assert data.pdf_base64 is not None
    assert data.tailored_data.basics.name == "SUNNY PATEL"

    # Verify base64 decode
    decoded = base64.b64decode(data.pdf_base64)
    assert decoded.startswith(b"%PDF"), "Decoded output must be a valid PDF binary"


def test_gemini_503_tries_lower_models_before_falling_back(monkeypatch, caplog):
    master = load_default_master_resume()
    attempts = []
    delays = []

    class ServiceUnavailable(Exception):
        code = 503

    class FailingModels:
        def generate_content(self, **kwargs):
            attempts.append(kwargs)
            raise ServiceUnavailable("model overloaded")

    class FakeClient:
        def __init__(self, api_key, http_options=None):
            self.models = FailingModels()

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("google.genai.Client", FakeClient)
    monkeypatch.setattr("app.llm_service.time.sleep", delays.append)
    monkeypatch.setattr("app.llm_service.random.uniform", lambda low, high: 0)
    caplog.set_level("INFO", logger="uvicorn.error")

    result = tailor_resume_with_gemini(master, "Backend engineer")

    assert len(attempts) == 6
    assert [attempt["model"] for attempt in attempts] == [
        "gemini-3.8-flash",
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-3.6-flash",
        "gemini-3.6-flash",
    ]
    assert len(delays) == 3
    assert "trying next model gemini-3.5-flash-lite" in caplog.text
    assert result.tailored_resume.basics.name == master.basics.name


def test_gemini_uses_flash_lite_when_primary_hits_rate_limit(monkeypatch, caplog):
    master = load_default_master_resume()
    attempts = []
    successful_json = get_mock_tailored_response(master, "Backend engineer").model_dump_json()

    class RateLimitExceeded(Exception):
        code = 429

    class FailingThenSuccessfulModels:
        def generate_content(self, **kwargs):
            attempts.append(kwargs["model"])
            if kwargs["model"] == "gemini-3.8-flash":
                raise RateLimitExceeded("daily request quota exceeded")
            return type("Response", (), {"text": successful_json})()

    class FakeClient:
        def __init__(self, api_key, http_options=None):
            self.models = FailingThenSuccessfulModels()

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("google.genai.Client", FakeClient)
    monkeypatch.setattr("app.llm_service.time.sleep", lambda delay: None)
    monkeypatch.setattr("app.llm_service.random.uniform", lambda low, high: 0)
    caplog.set_level("INFO", logger="uvicorn.error")

    result = tailor_resume_with_gemini(master, "Backend engineer")

    assert attempts == ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
    assert "trying next model gemini-3.5-flash-lite" in caplog.text
    assert "Gemini request succeeded with model gemini-3.5-flash-lite" in caplog.text
    assert result.tailored_resume.basics.name == master.basics.name


def test_gemini_overflow_retry_includes_trim_instruction(monkeypatch):
    master = load_default_master_resume()
    captured_payload = {}
    successful_json = get_mock_tailored_response(master, "Backend engineer").model_dump_json()

    class SuccessfulModels:
        def generate_content(self, **kwargs):
            captured_payload.update(json.loads(kwargs["contents"][1].text))
            captured_payload["thinking_budget"] = kwargs["config"].thinking_config.thinking_budget
            captured_payload["include_thoughts"] = kwargs["config"].thinking_config.include_thoughts
            return type("Response", (), {"text": successful_json})()

    class FakeClient:
        def __init__(self, api_key, http_options=None):
            self.models = SuccessfulModels()

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("google.genai.Client", FakeClient)

    tailor_resume_with_gemini(master, "Backend engineer", trim_percentage=15)

    assert any("approximately 15%" in rule for rule in captured_payload["rules"])
    assert captured_payload["thinking_budget"] == 0
    assert captured_payload["include_thoughts"] is False


def test_download_filename_uses_post_and_organization():
    filename = build_download_filename("Backend Engineer", "Acme Cloud")

    assert filename == "Sunny_Patel_Acme_Cloud_Backend_Engineer_Resume.pdf"


def test_template_preserves_markdown_bold_for_experience_metrics():
    master = load_default_master_resume()

    rendered_tex = render_latex(master)

    assert r"\textbf{Redis caching}" in rendered_tex
    assert r"\textbf{60\% to 22\%}" in rendered_tex
