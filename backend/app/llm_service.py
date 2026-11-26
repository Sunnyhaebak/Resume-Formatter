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
2. EXPERIENCE (NIELSEN) - 5 TO 8 JD-MATCHED BULLETS:
   - Nielsen MUST contain at least 5 bullet points and at most 8, matching the Master Resume bullet supply.
   - Start with 5 of the strongest bullets. Use 6 to 8 only when each extra point is explicitly relevant to the JD and still fits one page.
   - Select and reorder bullets from the Master Resume to match the target JD; remove weaker or less relevant points instead of inventing facts.
   - Rewrite each retained bullet truthfully around the JD's required technologies, impact metrics, and responsibilities.
   - Enhance and reframe the phrasing with high-impact keywords (e.g., high-traffic production scale, 99.95% uptime, API throughput, Redis caching, distributed microservices) to deeply impress HR and hiring managers.
3. PROJECTS - STRICTLY 3 VERIFIED GITHUB PROJECTS IN JD-RANKED ORDER:
   - Select Project 1 as the strongest repository match to the target company's core requirement; do not invent repositories or metrics.
   - Select Project 2 and Project 3 from the remaining verified GitHub project catalog, ranked by technology and domain overlap with the JD.
   - Preserve the repository names, technology stacks, and truthful repository links from the Master Resume.
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
    1. Generates Project 1 matching the company requirements (e.g. high-traffic platform).
    2. Ranks verified GitHub projects 2 and 3 by the target JD.
    3. Selects and reframes up to five Nielsen bullets with the strongest JD alignment.
    """
    jd_lower = job_description.lower()
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
        jd_terms = {term for term in re.findall(r"[a-zA-Z][a-zA-Z0-9+.-]{2,}", jd_lower)}
        sorted_bullets = sorted(
            raw_bullets,
            key=lambda bullet: sum(term in bullet.lower() for term in jd_terms),
            reverse=True,
        )

        # Keep at least five points; use up to eight only when the extra bullets match the JD.
        relevant_bullets = [bullet for bullet in sorted_bullets if sum(term in bullet.lower() for term in jd_terms) > 0]
        final_count = min(len(exp.bullets), max(5, min(8, len(relevant_bullets))))
        final_count = max(5, final_count)
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

    # 4. Projects: rank all verified GitHub repositories deterministically against the JD.
    verified_projects = list(master_resume.projects)

    def project_score(project: ProjectItem) -> int:
        searchable = f"{project.name} {project.tech_stack} {' '.join(project.bullets)}".lower()
        return sum(1 for term in jd_terms if term in searchable)

    ranked_projects = sorted(verified_projects, key=project_score, reverse=True)
    final_projects = ranked_projects[:3]

    diffs.append(
        DiffItem(
            category="Projects",
            item_name="Project 1 (Highest JD-Relevance Repository)",
            original="Unranked GitHub project catalog",
            tailored=f"{final_projects[0].name} ({final_projects[0].tech_stack})",
            reason=f"Project 1 was selected because it has the strongest verified GitHub technology and domain overlap with the JD: {final_projects[0].tech_stack}."
        )
    )
    diffs.append(
        DiffItem(
            category="Projects",
            item_name="Project 2 & 3 JD-Ranked Portfolio Selection",
            original="Unranked GitHub project catalog",
            tailored=" | ".join(project.name for project in final_projects[1:3]),
            reason="Ranked the remaining owned GitHub repositories by technology and domain overlap with the target JD."
        )
    )

    tailored_skills = Skills(
        backend_ai=backend_ai,
        frontend=master_resume.skills.frontend,
        languages=langs,
        cloud_data=master_resume.skills.cloud_data,
        practices=master_resume.skills.practices,
    )

    tailored_summary = master_resume.summary
    if "rag" in jd_lower or "semantic" in jd_lower or "open search" in jd_lower:
        tailored_summary = "Backend and Full-Stack Software Engineer with **18 months of production experience at Nielsen**, specializing in distributed microservices, REST APIs, event-driven pipelines, and production RAG integrations. Experienced in semantic/vector search, Amazon OpenSearch, Redis performance optimization, and cloud-backed scalable systems."
    elif "frontend" in jd_lower or "react" in jd_lower:
        tailored_summary = "Backend and Full-Stack Software Engineer with **18 months of production experience at Nielsen**, building React applications, REST APIs, enterprise microservices, Redis integrations, and distributed cloud services. Experienced in self-service dashboards, real-time communication, RBAC, and production full-stack delivery."
    elif "java" in jd_lower or "spring" in jd_lower:
        tailored_summary = "Backend and Full-Stack Software Engineer with **18 months of production experience at Nielsen**, building enterprise microservices, REST APIs, event-driven systems, Redis caching, and cloud integrations. Experienced in distributed Java-adjacent systems, Spring-ready API design, production resilience, and scalable backend architecture."

    tailored_resume = TailoredResume(
        basics=master_resume.basics,
        summary=tailored_summary,
        skills=tailored_skills,
        experience=tailored_experiences,
        projects=final_projects,
        achievements=master_resume.achievements,
        education=master_resume.education,
    )

    return TailoredResumeResponse(
        tailored_resume=tailored_resume,
        changes_summary=diffs
    )


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

        prompt_payload = {
            "target_job_description": job_description,
            "custom_instructions": custom_instructions or "None provided. Tailor strictly to JD.",
            "rules": rules,
            "verified_master_resume": master_resume.model_dump(),
        }

        user_content = json.dumps(prompt_payload, indent=2)

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
