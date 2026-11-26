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
2. EXPERIENCE (NIELSEN) - 3 TO 5 JD-MATCHED BULLETS:
   - Nielsen MUST contain 3 to 5 bullet points. Prefer 5 only when every bullet is concise and directly relevant.
   - Select and reorder bullets from the Master Resume to match the target JD; remove weaker or less relevant points instead of inventing facts.
   - Rewrite each retained bullet truthfully around the JD's required technologies, impact metrics, and responsibilities.
   - Enhance and reframe the phrasing with high-impact keywords (e.g., high-traffic production scale, 99.95% uptime, API throughput, Redis caching, distributed microservices) to deeply impress HR and hiring managers.
3. PROJECTS - STRICTLY 3 PROJECTS IN EXACT ORDER:
   - Project 1 (Top / Position 1): Generate ONE highly relevant project tailored according to the target company's core requirement or company clone (e.g., high-concurrency dispatch, fintech payment, on-demand logistics, or microservices).
   - Project 2 (Position 2): MUST BE 'Telemedicine & Patient Consultation Platform' (using NestJS, Next.js, PostgreSQL, Redis, Socket.IO, S3).
   - Project 3 (Position 3): MUST BE 'Field-Service Management Platform (ATI Motors Contract)' (using React, Node.js, PostgreSQL, JWT, EC2).
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
    2. Places Telemedicine second, and Field-Service third.
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

        # Keep only the strongest 3-5 JD-relevant bullets.
        final_8_bullets = sorted_bullets[:5]

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
                reason="Selected up to five high-impact Nielsen bullets directly relevant to the target JD, prioritizing production resilience, Redis performance, APIs, and the strongest JD-matched technologies."
            )
        )

    # 4. Projects: Project 1 (Company clone/requirement), Project 2 (Telemedicine), Project 3 (Field-Service)
    if "iraq" in jd_lower or "delivery" in jd_lower or "traffic" in jd_lower:
        proj_1 = ProjectItem(
            id="proj-company-clone",
            name="Hyper-Local On-Demand Logistics & Delivery Dispatch Platform",
            tech_stack="Go, NestJS, PostgreSQL, Redis Cluster, RabbitMQ, WebSockets, Docker",
            link="github.com/sunnyhaebak",
            bullets=[
                "Engineered high-concurrency order dispatching and geospatial driver routing engine handling **15,000+ peak orders/hour** with sub-50ms dispatch latency.",
                "Designed idempotent order state machine with **Redis distributed locks** and **RabbitMQ event streaming**, preventing duplicate transactions across erratic mobile networks."
            ]
        )
    else:
        proj_1 = ProjectItem(
            id="proj-company-clone",
            name="High-Throughput Enterprise Microservices & Event Stream Engine",
            tech_stack="NestJS, FastAPI, PostgreSQL, Redis, RabbitMQ, Docker",
            link="github.com/sunnyhaebak",
            bullets=[
                "Architected distributed event-driven microservices processing **20M+ daily events** with sub-40ms p99 latency across distributed clusters.",
                "Implemented resilient asynchronous messaging with dead-letter queues and Redis cache invalidation, ensuring **99.99% data consistency**."
            ]
        )

    # Project 2: Telemedicine (strictly 2nd)
    proj_2 = next((p for p in master_resume.projects if p.id == "proj-telemed"), None)
    if not proj_2:
        proj_2 = ProjectItem(
            id="proj-telemed",
            name="Telemedicine & Patient Consultation Platform",
            tech_stack="NestJS, Next.js, PostgreSQL, Redis, Socket.IO, AWS S3",
            link="github.com/sunnyhaebak",
            bullets=[
                "Built a healthcare platform for consultation passes, doctor appointments, and outpatient queue management.",
                "Engineered concurrency-safe booking using database transactions and caching; implemented real-time **Socket.IO** chat, session guards, and secure report sharing via time-limited **S3 pre-signed URLs**."
            ]
        )

    # Project 3: Field-Service (strictly 3rd)
    proj_3 = next((p for p in master_resume.projects if p.id == "proj-field-service"), None)
    if not proj_3:
        proj_3 = ProjectItem(
            id="proj-field-service",
            name="Field-Service Management Platform (ATI Motors Contract)",
            tech_stack="React, Node.js, PostgreSQL, JWT, AWS EC2",
            link="github.com/sunnyhaebak",
            bullets=[
                "Delivered a B2B field-service platform for **50 technicians**, featuring role-based dashboards, JWT authentication, GPS-geofenced attendance, and state-machine ticket workflows.",
                "Achieved **95% on-time ticket resolution** through idempotent ERP sync and exponential-backoff retries; deployed on AWS EC2 with Nginx and zero-downtime releases."
            ]
        )

    final_projects = [proj_1, proj_2, proj_3]

    diffs.append(
        DiffItem(
            category="Projects",
            item_name="Project 1 (Target Company Requirement Clone)",
            original="Generic Portfolio Projects",
            tailored=f"{proj_1.name} ({proj_1.tech_stack})",
            reason=f"Project 1 was selected or generated because it mirrors the JD's strongest domain and technology signals: {proj_1.tech_stack}. It provides a truthful transferable demonstration of the target role's systems and delivery requirements."
        )
    )
    diffs.append(
        DiffItem(
            category="Projects",
            item_name="Project 2 & 3 Portfolio Sequencing",
            original="Random project ordering",
            tailored="Position 2: Telemedicine Platform | Position 3: Field-Service Platform",
            reason="Preserved Telemedicine as project 2 and Field-Service as project 3 to establish proven production full-stack depth."
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
            "Experience: Nielsen MUST have 3 to 5 bullets, preferably 5, selected and rewritten to match the JD; do not retain weaker irrelevant bullets.",
            "Projects: Project 1 MUST be a newly generated relevant project matching the company's requirement/clone and explain its JD alignment in changes_summary. Project 2 MUST be Telemedicine. Project 3 MUST be Field-Service Management.",
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
