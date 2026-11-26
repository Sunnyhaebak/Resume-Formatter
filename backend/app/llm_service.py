import os
import json
import logging
import random
import re
import time
from typing import Optional
from dotenv import load_dotenv

from app.schemas import (
    MasterResume,
    TailoredResume,
    TailoredResumeResponse,
    DiffItem,
    ExperienceItem,
    ProjectItem,
    Skills,
)

load_dotenv()
logger = logging.getLogger("uvicorn.error")
GEMINI_MODEL_CHAIN = (
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
)

SYSTEM_PROMPT = """You are an elite, truthful Executive Technical Resume Tailoring Engine specifically tailoring for Sunny Patel.
Your goal is to tailor the candidate's verified Master Resume JSON to maximally align with the target Job Description (JD) and any Custom Instructions provided.

CRITICAL RULES:
0. BOLD PRESERVATION:
   - Preserve every existing `**bold**` emphasis exactly from the Master Resume.
   - Keep key achievements and metrics bold, especially Redis, 60% to 22%, 12+ REST APIs, 15 global markets, 226.4 million, 99.95% uptime, MCP server, FastAPI, and 33%.
   - Use Markdown `**text**` around important keywords and metrics in summaries, skills, experience bullets, project bullets, and achievements. Do not bold entire sentences or ordinary words.
1. ZERO FABRICATION:
   - You MUST NOT invent fictional companies, job titles, start/end dates, or fake degrees.
   - You may only use facts, experience, projects, and skills that exist in the Master Resume, with truthful reframing of architectural concepts.
    - Project 1 is the sole exception: it is a clearly labeled proposed concept, not candidate work history, and must not claim completion or fabricated outcomes.
2. EXPERIENCE (NIELSEN) - 5 TO 8 JD-MATCHED BULLETS:
    - Nielsen MUST contain at least 5 bullet points and at most the number supplied by the Master Resume (currently 8).
    - Prefer 5. Use additional source-supported bullets up to 8 when the JD makes them relevant and the page still fits.
   - Select and reorder bullets from the Master Resume to match the target JD; remove weaker or less relevant points instead of inventing facts.
   - Rewrite each retained bullet truthfully around the JD's required technologies, impact metrics, and responsibilities.
   - Enhance and reframe the phrasing with high-impact keywords (e.g., high-traffic production scale, 99.95% uptime, API throughput, Redis caching, distributed microservices) to deeply impress HR and hiring managers.
3. PROJECTS - STRICTLY 3 PROJECTS:
    - Project 1 is an AI-generated, JD-specific proposed project concept designed to demonstrate alignment with the target company's requirements.
    - Use only technologies present in the verified Master Resume skills/project catalog and if needed then add 1 or 2 from the JD.
    - Projects 2 and 3 MUST be selected from distinct verified GitHub repositories in the Master Resume, ranked by JD relevance, with their original repository links.
4. TECHNICAL SKILLS:
   - Reorder the technologies in Backend & AI, Languages, and Cloud & Data so that the skills matching the target JD appear first in each category.
5. STRICT 1-PAGE SPACE BUDGET:
   - Each bullet must be concise, dense, and impactful so the entire resume strictly fits on a single page.
6. EXPLANATION OF CHANGES:
   - In `changes_summary`, explain which Nielsen bullets were selected and why, describe exactly why Project 1 matches the target role, and document the skill reordering rationale.
"""


def get_mock_tailored_response(
    master_resume: MasterResume,
    job_description: str,
    custom_instructions: Optional[str] = None
) -> TailoredResumeResponse:
    """
    Deterministic tailoring engine tailored for Sunny Patel:
    1. Creates a clearly labeled proposed Project 1 concept tailored to the JD.
    2. Ranks verified GitHub projects 2 and 3 by the target JD.
    3. Selects five to eight Nielsen bullets with the strongest JD alignment.
    """
    jd_lower = job_description.lower()
    jd_terms = _job_terms(job_description)
    diffs: list[DiffItem] = []

    # 1. Reorder Languages
    langs = list(master_resume.skills.languages)
    if "python" in jd_lower or "ai" in jd_lower:
        langs = sorted(langs, key=lambda l: 0 if l.lower() in ["python", "sql", "typescript"] else 1)
    elif "java" in jd_lower or "spring" in jd_lower:
        langs = sorted(langs, key=lambda l: 0 if l.lower() in ["java 21", "sql", "typescript"] else 1)
    elif "go" in jd_lower:
        langs = sorted(langs, key=lambda l: 0 if l.lower() in ["c++", "typescript", "python"] else 1)
    else:
        langs = sorted(langs, key=lambda l: 0 if l.lower() in ["typescript", "javascript", "python"] else 1)

    diffs.append(
        DiffItem(
            category="Skills",
            item_name="Programming Languages",
            original=", ".join(master_resume.skills.languages),
            tailored=", ".join(langs),
            reason="Prioritized programming languages matching the target tech stack."
        )
    )

    # 2. Reorder Backend & AI
    backend_ai = list(master_resume.skills.backend_ai)
    if "rag" in jd_lower or "ai" in jd_lower or "vector" in jd_lower:
        backend_ai = sorted(backend_ai, key=lambda s: 0 if s.lower() in ["rag", "semantic/vector search", "langfuse", "fastapi"] else 1)
    elif "high-traffic" in jd_lower or "production" in jd_lower or "distributed" in jd_lower:
        backend_ai = sorted(backend_ai, key=lambda s: 0 if s.lower() in ["microservices", "rest apis", "rabbitmq", "redis", "nestjs", "fastapi"] else 1)
    else:
        backend_ai = sorted(backend_ai, key=lambda s: 0 if s.lower() in ["node.js", "nestjs", "fastapi", "rest apis"] else 1)

    diffs.append(
        DiffItem(
            category="Skills",
            item_name="Backend & AI Stack",
            original=", ".join(master_resume.skills.backend_ai),
            tailored=", ".join(backend_ai),
            reason="Promoted microservices, high-traffic messaging, and production APIs demanded by the JD."
        )
    )

    # 3. Experience (Nielsen) - up to five bullets prioritized by JD relevance
    tailored_experiences: list[ExperienceItem] = []
    for exp in master_resume.experience:
        raw_bullets = list(exp.bullets)

        # Rank bullets by direct overlap with the target JD while preserving source wording.
        sorted_bullets = sorted(
            raw_bullets,
            key=lambda bullet: sum(term in bullet.lower() for term in jd_terms),
            reverse=True,
        )

        # Keep at least five points; use up to eight only when the extra bullets match the JD.
        relevant_bullets = [bullet for bullet in sorted_bullets if sum(term in bullet.lower() for term in jd_terms) > 0]
        final_count = min(len(exp.bullets), max(5, min(8, len(relevant_bullets))))
        final_8_bullets = sorted_bullets[:final_count]

        tailored_experiences.append(
            ExperienceItem(
                id=exp.id,
                company=exp.company,
                role=exp.role,
                duration=exp.duration,
                location=exp.location,
                bullets=final_8_bullets,
            )
        )

        diffs.append(
            DiffItem(
                category="Experience",
                item_name=f"{exp.role} @ {exp.company}",
                original=exp.bullets,
                tailored=final_8_bullets,
                reason="Selected five to eight high-impact Nielsen bullets directly relevant to the target JD, prioritizing production resilience, Redis performance, APIs, and the strongest JD-matched technologies without exceeding one page."
            )
        )

    # Project 1 is a proposed concept; only Projects 2 and 3 imply completed work.
    project_1 = _make_proposed_project(master_resume, job_description)
    ranked_projects = _rank_verified_projects(master_resume, jd_terms)
    final_projects = [project_1, *ranked_projects[:2]]

    diffs.append(
        DiffItem(
            category="Projects",
            item_name="Project 1 (AI-Generated Proposed Concept)",
            original="No proposed concept",
            tailored=f"{project_1.name} ({project_1.tech_stack})",
            reason=f"Generated as a clearly labeled proposed concept to align with the JD's requirements. Its technology stack is limited to verified skills: {project_1.tech_stack}. It is not represented as completed work."
        )
    )
    diffs.append(
        DiffItem(
            category="Projects",
            item_name="Project 2 & 3 JD-Ranked Portfolio Selection",
            original="Unranked GitHub project catalog",
            tailored=" | ".join(project.name for project in final_projects[1:3]),
            reason="Selected these two completed projects from the verified GitHub catalog and ranked them by technology and domain overlap with the target JD."
        )
    )

    tailored_skills = Skills(
        backend_ai=backend_ai,
        frontend=master_resume.skills.frontend,
        languages=langs,
        cloud_data=master_resume.skills.cloud_data,
        practices=master_resume.skills.practices,
    )

    tailored_summary = _make_jd_summary(master_resume, jd_terms)

    tailored_resume = TailoredResume(
        basics=master_resume.basics,
        summary=tailored_summary,
        skills=tailored_skills,
        experience=tailored_experiences,
        projects=final_projects,
        achievements=master_resume.achievements,
        education=master_resume.education,
    )

    diffs.append(
        DiffItem(
            category="Summary",
            item_name="JD-Tailored Professional Summary",
            original=master_resume.summary or "No summary",
            tailored=tailored_summary or "",
            reason="Prioritized verified skills and experience with the strongest direct overlap with the target job description.",
        )
    )

    return TailoredResumeResponse(
        tailored_resume=tailored_resume,
        changes_summary=diffs
    )


def _job_terms(job_description: str) -> set[str]:
    stop_words = {"and", "the", "for", "with", "from", "you", "your", "are", "our", "this", "that", "will", "have", "has", "who", "what", "about", "into", "years", "year", "role", "team", "work", "job", "experience", "engineer", "developer", "senior", "junior"}
    return {
        term.lower()
        for term in re.findall(r"[A-Za-z][A-Za-z0-9+.#/-]{1,}", job_description)
        if term.lower() not in stop_words
    }


def _rank_verified_projects(master_resume: MasterResume, jd_terms: set[str]) -> list[ProjectItem]:
    def score(project: ProjectItem) -> int:
        text = f"{project.name} {project.tech_stack} {' '.join(project.bullets)}".lower()
        return sum(term in text for term in jd_terms)

    return sorted(master_resume.projects, key=score, reverse=True)


def _make_proposed_project(master_resume: MasterResume, job_description: str) -> ProjectItem:
    jd_lower = job_description.lower()
    if any(term in jd_lower for term in ("payment", "fintech", "banking", "payout")):
        domain = "Payment Reconciliation and Risk Operations"
        purpose = "payment processing, reconciliation, and failure recovery"
    elif any(term in jd_lower for term in ("health", "medical", "patient", "clinical")):
        domain = "Connected Care Coordination"
        purpose = "patient workflows, appointment coordination, and secure communication"
    elif any(term in jd_lower for term in ("logistics", "delivery", "fleet", "dispatch")):
        domain = "Fleet Dispatch and Operations"
        purpose = "dispatch orchestration, live fleet status, and resilient event processing"
    elif any(term in jd_lower for term in ("ai", "llm", "rag", "machine learning", "search")):
        domain = "Enterprise AI Knowledge Assistant"
        purpose = "grounded retrieval, controlled tool execution, and auditable AI workflows"
    else:
        domain = "Enterprise Workflow Automation"
        purpose = "the role's stated workflows, integrations, and operational requirements"

    known_technologies = {
        skill
        for group in (
            master_resume.skills.backend_ai,
            master_resume.skills.frontend,
            master_resume.skills.languages,
            master_resume.skills.cloud_data,
        )
        for skill in group
        if skill.lower() in jd_lower
    }
    if len(known_technologies) < 3:
        known_technologies.update(master_resume.skills.backend_ai[:3])
    tech_stack = ", ".join(sorted(known_technologies)[:6])

    return ProjectItem(
        id="proj-jd-concept",
        name=f"{domain} (Proposed Concept)",
        tech_stack=tech_stack,
        link="",
        bullets=[
            f"Proposed a JD-aligned system concept for {purpose}; this is a design proposal, not a claim of completed work.",
            f"Outlined an architecture using verified candidate technologies: {tech_stack}.",
        ],
    )


def _make_jd_summary(master_resume: MasterResume, jd_terms: set[str]) -> str:
    intro = (master_resume.summary or "Backend and Full-Stack Software Engineer.").split(". ", 1)[0].rstrip(".")
    available_skills = (
        master_resume.skills.backend_ai
        + master_resume.skills.languages
        + master_resume.skills.cloud_data
        + master_resume.skills.frontend
    )
    matched_skills = [skill for skill in available_skills if any(term in skill.lower() or skill.lower() in term for term in jd_terms)]
    if not matched_skills:
        matched_skills = master_resume.skills.backend_ai[:3]
    selected = matched_skills[:5]
    highlighted = ", ".join(f"**{skill}**" for skill in selected)
    return f"{intro}. Relevant verified strengths for this role include {highlighted}."


def _enforce_response_contract(
    response: TailoredResumeResponse,
    master_resume: MasterResume,
    job_description: str,
) -> TailoredResumeResponse:
    jd_terms = _job_terms(job_description)
    original_experience = {item.id: item for item in master_resume.experience}

    for experience in response.tailored_resume.experience:
        source = original_experience.get(experience.id)
        if not source:
            continue
        ranked_source = sorted(
            source.bullets,
            key=lambda bullet: sum(term in bullet.lower() for term in jd_terms),
            reverse=True,
        )
        minimum = min(5, len(source.bullets))
        maximum = min(8, len(source.bullets))
        bullets = list(experience.bullets[:maximum])
        for source_bullet in ranked_source:
            if len(bullets) >= minimum:
                break
            if source_bullet not in bullets:
                bullets.append(source_bullet)
        experience.bullets = bullets

    proposed_project = response.tailored_resume.projects[0] if response.tailored_resume.projects else None
    fallback_concept = _make_proposed_project(master_resume, job_description)
    if proposed_project:
        claim_text = " ".join(proposed_project.bullets)
        verified_technologies = (
            master_resume.skills.backend_ai
            + master_resume.skills.frontend
            + master_resume.skills.languages
            + master_resume.skills.cloud_data
            + [project.tech_stack for project in master_resume.projects]
        )
        unknown_stack_item = any(
            not any(technology.lower() in item.strip().lower() or item.strip().lower() in technology.lower() for technology in verified_technologies)
            for item in proposed_project.tech_stack.split(",")
            if item.strip()
        )
        if (
            re.search(r"\b(built|implemented|deployed|achieved|processed|reduced|increased)\b|\d", claim_text, re.I)
            or unknown_stack_item
        ):
            proposed_project = fallback_concept
        else:
            proposed_project.id = "proj-jd-concept"
            if "proposed concept" not in proposed_project.name.lower():
                proposed_project.name = f"{proposed_project.name} (Proposed Concept)"
            proposed_project.link = ""
    else:
        proposed_project = fallback_concept

    ranked_repositories = _rank_verified_projects(master_resume, jd_terms)
    response.tailored_resume.projects = [proposed_project, *ranked_repositories[:2]]

    if not response.tailored_resume.summary or response.tailored_resume.summary == master_resume.summary:
        response.tailored_resume.summary = _make_jd_summary(master_resume, jd_terms)

    response.changes_summary = [
        item for item in response.changes_summary
        if not (item.category.lower() == "projects" or item.category.lower() == "summary")
    ]
    response.changes_summary.extend([
        DiffItem(
            category="Projects",
            item_name="Project 1 (AI-Generated Proposed Concept)",
            original="No proposed concept",
            tailored=f"{proposed_project.name} ({proposed_project.tech_stack})",
            reason="Generated to demonstrate a solution concept aligned to this JD. It is explicitly marked as proposed, uses verified technologies, and is not represented as completed work.",
        ),
        DiffItem(
            category="Projects",
            item_name="Projects 2 & 3 (Verified GitHub Repositories)",
            original="Full verified GitHub project catalog",
            tailored=" | ".join(project.name for project in ranked_repositories[:2]),
            reason="Selected and ranked from owned GitHub repositories by overlap with the target JD.",
        ),
        DiffItem(
            category="Summary",
            item_name="JD-Tailored Professional Summary",
            original=master_resume.summary or "No summary",
            tailored=response.tailored_resume.summary or "",
            reason="Rewritten to prioritize verified skills and experience that overlap with the job description.",
        ),
    ])
    return response


def tailor_resume_with_gemini(
    master_resume: MasterResume,
    job_description: str,
    custom_instructions: Optional[str] = None,
    trim_percentage: int = 0
) -> TailoredResumeResponse:
    """
    Invokes Google Gemini API with Pydantic Structured Outputs to tailor Sunny Patel's resume.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "your_gemini_api_key_here":
        logger.warning("GEMINI_API_KEY is not configured. Falling back to deterministic engine.")
        return get_mock_tailored_response(master_resume, job_description, custom_instructions)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=18000),
        )

        rules = [
            "Bold preservation: preserve existing **markdown bold** emphasis and bold the same kinds of high-impact technologies and metrics in rewritten text.",
            "Experience: Nielsen MUST have at least 5 bullets and no more than 8. Prefer 5; use more only when the JD clearly supports every extra bullet and the page remains one page.",
            "Projects: select exactly three verified GitHub projects from the Master Resume. Rank positions 1-3 by JD domain and technology match, explain Project 1 selection in changes_summary, and do not invent a repository or metric.",
            "Summary: rewrite the professional summary for this specific JD, preserving every verified metric and fact, and prioritize only JD-matched capabilities.",
            "Skills: Reorder skills so matching tech is at the top of each category.",
            "Single page: All bullets must be tight and concise."
        ]
        if trim_percentage > 0:
            rules.append(
                f"Overflow retry: reduce the summary and bullet wording by approximately {trim_percentage}% compared with a standard tailoring pass. Preserve all verified facts, key metrics, and required sections."
            )

        resume_payload = master_resume.model_dump()
        resume_payload["projects"] = [
            project.model_dump()
            for project in _rank_verified_projects(master_resume, _job_terms(job_description))[:3]
        ]

        prompt_payload = {
            "target_job_description": job_description,
            "custom_instructions": custom_instructions or "None provided. Tailor strictly to JD.",
            "rules": rules,
            "verified_master_resume": resume_payload,
        }

        user_content = json.dumps(prompt_payload, separators=(",", ":"), ensure_ascii=True)

        for model_index, model in enumerate(GEMINI_MODEL_CHAIN):
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=[
                            types.Part.from_text(
                                text="Analyze the JD and Master Resume. Return the tailored resume and changes summary according to schema."
                            ),
                            types.Part.from_text(text=user_content),
                        ],
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            response_mime_type="application/json",
                            response_schema=TailoredResumeResponse,
                            temperature=0.2,
                            thinking_config=types.ThinkingConfig(
                                thinking_budget=0,
                                include_thoughts=False,
                            ),
                        ),
                    )
                    if not response.text:
                        raise ValueError("Empty response received from Gemini.")

                    tailored_res = TailoredResumeResponse.model_validate_json(response.text)
                    tailored_res = _enforce_response_contract(
                        tailored_res,
                        master_resume,
                        job_description,
                    )
                    logger.info("Gemini request succeeded with model %s.", model)
                    return tailored_res
                except Exception as e:
                    error_code = getattr(e, "code", None)
                    if error_code == 503 and attempt < 1:
                        delay = 0.75 + random.uniform(0, 0.25)
                        logger.warning(
                            "Gemini model %s returned 503 UNAVAILABLE; retrying in %.2f seconds (1/1).",
                            model,
                            delay,
                        )
                        time.sleep(delay)
                        continue

                    next_model_index = model_index + 1
                    if next_model_index < len(GEMINI_MODEL_CHAIN) and (
                        error_code is None or error_code in {404, 429, 500, 502, 503, 504}
                    ):
                        next_model = GEMINI_MODEL_CHAIN[next_model_index]
                        logger.warning(
                            "Gemini model %s failed (HTTP %s); trying next model %s.",
                            model,
                            error_code or type(e).__name__,
                            next_model,
                        )
                        break
                    raise

    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}. Falling back to deterministic response.")
        return get_mock_tailored_response(master_resume, job_description, custom_instructions)
