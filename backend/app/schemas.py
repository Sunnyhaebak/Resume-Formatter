from typing import List, Optional, Union
from pydantic import BaseModel, Field


class Basics(BaseModel):
    name: str = Field(description="Full name of the candidate")
    title: Optional[str] = Field(
        default="Software Engineer $\\bullet$ Backend \\& Full-Stack Systems",
        description="Professional title or headline"
    )
    phone: str = Field(description="Contact phone number")
    email: str = Field(description="Email address")
    linkedin: str = Field(description="LinkedIn profile link or username")
    github: str = Field(description="GitHub profile link or username")
    leetcode: Optional[str] = Field(
        default="leetcode.com/sunnyhaebak",
        description="LeetCode profile link or username"
    )
    location: Optional[str] = Field(default="Hyderabad, India", description="Location")


class Education(BaseModel):
    institution: str = Field(description="College or University name")
    degree: str = Field(description="Degree and major")
    gpa: Optional[str] = Field(default=None, description="GPA or CGPA if applicable")
    graduation_date: str = Field(description="Graduation date or expected date")
    location: Optional[str] = Field(default="", description="City, State or Country")
    coursework: Optional[str] = Field(default=None, description="Relevant coursework")


class Skills(BaseModel):
    backend_ai: List[str] = Field(
        default_factory=list,
        description="Backend, AI, and microservices technologies"
    )
    frontend: List[str] = Field(
        default_factory=list,
        description="Frontend technologies and frameworks"
    )
    languages: List[str] = Field(
        default_factory=list,
        description="Programming languages ordered by relevance to the JD"
    )
    cloud_data: List[str] = Field(
        default_factory=list,
        description="Cloud platforms, containers, and database systems"
    )
    practices: List[str] = Field(
        default_factory=list,
        description="Architectural practices, system design, and engineering methodologies"
    )


class ExperienceItem(BaseModel):
    id: str = Field(description="Unique identifier of the experience role")
    company: str = Field(description="Company name")
    role: str = Field(description="Candidate's job title")
    duration: str = Field(description="Start and end dates")
    location: str = Field(description="Job location")
    bullets: List[str] = Field(
        description="Reframed, truthful bullet points emphasizing JD concepts with metrics. Keep concise to fit 1 page."
    )


class ProjectItem(BaseModel):
    id: str = Field(description="Unique identifier of the project")
    name: str = Field(description="Project name")
    tech_stack: str = Field(description="Technologies used in this project")
    link: Optional[str] = Field(default="", description="Repository or demo link")
    bullets: List[str] = Field(
        description="Reframed bullet points highlighting impact and transferable skills."
    )


class MasterResume(BaseModel):
    basics: Basics
    summary: Optional[str] = Field(
        default=None,
        description="Brief professional summary"
    )
    skills: Skills
    experience: List[ExperienceItem]
    projects: List[ProjectItem]
    achievements: Optional[List[str]] = Field(
        default_factory=list,
        description="Achievements and certifications"
    )
    education: List[Education]


class DiffItem(BaseModel):
    category: str = Field(description="Section category: Skills, Experience, Projects, or Summary")
    item_name: str = Field(description="Title or identifier of the changed section or item")
    original: Union[str, List[str]] = Field(description="Original bullet(s) or skill ordering from master resume")
    tailored: Union[str, List[str]] = Field(description="Tailored bullet(s) or skill ordering matching JD")
    reason: str = Field(description="Explanation of why this was reframed or reordered based on JD keywords")


class TailoredResume(BaseModel):
    basics: Basics
    summary: Optional[str] = Field(default=None, description="Tailored professional summary")
    skills: Skills
    experience: List[ExperienceItem]
    projects: List[ProjectItem] = Field(
        description="Top 2-3 most relevant projects only to keep resume within 1 page"
    )
    achievements: Optional[List[str]] = Field(default_factory=list)
    education: List[Education]


class TailoredResumeResponse(BaseModel):
    tailored_resume: TailoredResume
    changes_summary: List[DiffItem] = Field(
        description="Detailed list of differences and rationale for bullet rewrites and ordering"
    )


class TailorRequest(BaseModel):
    job_description: str = Field(default="", description="Raw text or URL of the target Job Description")
    job_url: Optional[str] = Field(default=None, description="Optional public job-post URL to read")
    custom_instructions: Optional[str] = Field(
        default=None,
        description="Optional user guidance (e.g., 'Emphasize Spring Boot, microservices, and RAG architectures')"
    )
    master_resume: Optional[MasterResume] = Field(
        default=None,
        description="Optional custom master resume override. Defaults to master_resume.json if omitted."
    )


class TailorResponse(BaseModel):
    pdf_base64: str = Field(description="Base64-encoded PDF compiled from LaTeX")
    download_filename: str = Field(default="Sunny_Patel_Tailored_Resume.pdf", description="Suggested download filename")
    page_count: int = Field(description="Strict page count of compiled PDF (must be 1)")
    changes_summary: List[DiffItem] = Field(description="List of what was changed and why")
    tailored_data: TailoredResume = Field(description="The tailored structured resume payload")
    latex_source: Optional[str] = Field(default=None, description="The rendered LaTeX source code")
