import io
import re
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.schemas import TailoredResume

# Color palette matching Sunny Patel's LaTeX template
NAVY_DARK = colors.HexColor("#0F2442")
ROYAL_BLUE = colors.HexColor("#1D4E89")
BODY_DARK = colors.HexColor("#1A1A1A")
SUB_ITALIC = colors.HexColor("#2D3748")
TECH_GRAY = colors.HexColor("#374151")
PIPE_GRAY = colors.HexColor("#666666")


def clean_latex_markup_for_reportlab(text: str) -> str:
    """
    Converts LaTeX and markdown bold tags to ReportLab <b>...</b> tags
    and escapes ampersands/angles.
    """
    if not text:
        return ""
    res = text
    # Convert \textbf{...} -> <b>...</b>
    res = re.sub(r'\\textbf\{([^}]+)\}', r'<b>\1</b>', res)
    # Convert **...** -> <b>...</b>
    res = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', res)
    # Clean escaped LaTeX symbols
    res = res.replace(r'\%', '%')
    res = res.replace(r'\&', '&amp;')
    res = res.replace(r'\$', '$')
    res = res.replace(r'\#', '#')
    res = res.replace(r'\_', '_')
    # Unescaped & that isn't &amp; or &bull;
    res = re.sub(r'&(?!(amp|bull|lt|gt|quot);)', '&amp;', res)
    return res


def generate_reportlab_pdf(tailored_resume: TailoredResume) -> bytes:
    """
    Generates a crisp, pixel-perfect 1-page PDF using ReportLab
    faithfully matching Sunny Patel's LaTeX styling.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=30.24,
        rightMargin=30.24,
        topMargin=19.44,
        bottomMargin=18,
    )

    styles = getSampleStyleSheet()

    # Typography styles
    name_style = ParagraphStyle(
        "ResumeName",
        fontName="Helvetica-Bold",
        fontSize=17.6,
        leading=19.2,
        textColor=NAVY_DARK,
    )
    title_style = ParagraphStyle(
        "ResumeTitle",
        fontName="Helvetica",
        fontSize=9.5,
        leading=11,
        textColor=ROYAL_BLUE,
    )
    contact_style = ParagraphStyle(
        "ResumeContact",
        fontName="Helvetica",
        fontSize=8.5,
        leading=10,
        textColor=BODY_DARK,
    )
    sec_title_style = ParagraphStyle(
        "ResumeSecTitle",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=11,
        textColor=NAVY_DARK,
    )
    body_style = ParagraphStyle(
        "ResumeBody",
        fontName="Helvetica",
        fontSize=8.5,
        leading=9.9,
        textColor=BODY_DARK,
    )
    summary_style = ParagraphStyle(
        "ResumeSummary",
        parent=body_style,
        fontSize=8.7,
        leading=10.2,
    )
    experience_bullet_style = ParagraphStyle(
        "ResumeExperienceBullet",
        fontName="Helvetica",
        fontSize=8.7,
        leading=10.2,
        textColor=BODY_DARK,
        leftIndent=8,
        firstLineIndent=-8,
    )
    project_bullet_style = ParagraphStyle(
        "ResumeProjectBullet",
        parent=experience_bullet_style,
        fontSize=8.6,
        leading=10.1,
    )
    achievement_style = ParagraphStyle(
        "ResumeAchievement",
        parent=experience_bullet_style,
        fontSize=8.6,
        leading=10,
    )
    project_header_style = ParagraphStyle(
        "ResumeProjectHeader",
        parent=body_style,
        fontSize=8.9,
        leading=10,
    )

    story = []

    # 1. Header
    b = tailored_resume.basics
    story.append(Paragraph(clean_latex_markup_for_reportlab(b.name), name_style))
    story.append(Spacer(1, 1.5))
    story.append(Paragraph(clean_latex_markup_for_reportlab(b.title or "Software Engineer • Backend & Full-Stack Systems"), title_style))
    story.append(Spacer(1, 1.5))

    contact_parts = [
        f'<font color="#1D4E89">{b.email}</font>',
        b.phone,
        f'<font color="#1D4E89">LinkedIn</font>',
        f'<font color="#1D4E89">GitHub</font>',
    ]
    if b.leetcode:
        contact_parts.append(f'<font color="#1D4E89">LeetCode</font>')
    contact_line = ' <font color="#666666">|</font> '.join(contact_parts)
    story.append(Paragraph(contact_line, contact_style))
    story.append(Spacer(1, 2))
    story.append(HRFlowable(width="100%", thickness=1.1, color=NAVY_DARK, spaceBefore=0, spaceAfter=2))

    def add_section(title: str):
        story.append(Paragraph(title, sec_title_style))
        story.append(HRFlowable(width="100%", thickness=0.7, color=NAVY_DARK, spaceBefore=0.5, spaceAfter=1.5))

    # 2. Summary
    if tailored_resume.summary:
        add_section("SUMMARY")
        story.append(Paragraph(clean_latex_markup_for_reportlab(tailored_resume.summary), summary_style))
        story.append(Spacer(1, 2))

    # 3. Technical Skills
    add_section("TECHNICAL SKILLS")
    sk = tailored_resume.skills
    skill_rows = [
        [Paragraph("<b>Backend &amp; AI:</b>", body_style), Paragraph(clean_latex_markup_for_reportlab(", ".join(sk.backend_ai)), body_style)],
        [Paragraph("<b>Frontend:</b>", body_style), Paragraph(clean_latex_markup_for_reportlab(", ".join(sk.frontend)), body_style)],
        [Paragraph("<b>Languages:</b>", body_style), Paragraph(clean_latex_markup_for_reportlab(", ".join(sk.languages)), body_style)],
        [Paragraph("<b>Cloud &amp; Data:</b>", body_style), Paragraph(clean_latex_markup_for_reportlab(", ".join(sk.cloud_data)), body_style)],
        [Paragraph("<b>Practices:</b>", body_style), Paragraph(clean_latex_markup_for_reportlab(", ".join(sk.practices)), body_style)],
    ]
    st = Table(skill_rows, colWidths=[75.6, 475.92])
    st.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(st)
    story.append(Spacer(1, 2))

    # 4. Experience (Nielsen - up to five JD-matched bullets)
    add_section("EXPERIENCE")
    for exp in tailored_resume.experience:
        exp_table = [
            [Paragraph(f"<b>{clean_latex_markup_for_reportlab(exp.company)}</b>", body_style),
             Paragraph(f"<b>{clean_latex_markup_for_reportlab(exp.location)}</b>", ParagraphStyle("ER", parent=body_style, alignment=2))],
            [Paragraph(f'<i><font color="#2D3748">{clean_latex_markup_for_reportlab(exp.role)}</font></i>', body_style),
             Paragraph(f'<i><font color="#2D3748">{clean_latex_markup_for_reportlab(exp.duration)}</font></i>', ParagraphStyle("EDR", parent=body_style, alignment=2))]
        ]
        et = Table(exp_table, colWidths=[296, 255.52])
        et.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(et)
        story.append(Spacer(1, 1))

        # Enforce a concise five-bullet maximum
        for bullet in exp.bullets[:5]:
            clean_b = clean_latex_markup_for_reportlab(bullet)
            story.append(Paragraph(f'<font color="#1D4E89">&bull;</font> {clean_b}', experience_bullet_style))
            story.append(Spacer(1, 0.4))
    story.append(Spacer(1, 1.5))

    # 5. Projects (Top 3: Company Requirement top, Telemedicine 2nd, Field-Service 3rd)
    add_section("PROJECTS")
    for proj in tailored_resume.projects[:3]:
        p_name = clean_latex_markup_for_reportlab(proj.name)
        p_stack = clean_latex_markup_for_reportlab(proj.tech_stack)
        proj_hdr = Paragraph(f'<b>{p_name}</b> <font color="#666666">|</font> <i><font color="#374151">{p_stack}</font></i>', project_header_style)
        story.append(proj_hdr)
        story.append(Spacer(1, 0.4))
        for bullet in proj.bullets:
            clean_b = clean_latex_markup_for_reportlab(bullet)
            story.append(Paragraph(f'<font color="#1D4E89">&bull;</font> {clean_b}', project_bullet_style))
            story.append(Spacer(1, 0.4))
        story.append(Spacer(1, 1))

    # 6. Achievements & Certifications
    if tailored_resume.achievements:
        add_section("ACHIEVEMENTS &amp; CERTIFICATIONS")
        for ach in tailored_resume.achievements[:4]:
            clean_a = clean_latex_markup_for_reportlab(ach)
            story.append(Paragraph(f'<font color="#1D4E89">&bull;</font> {clean_a}', achievement_style))
            story.append(Spacer(1, 0.4))
        story.append(Spacer(1, 1.5))

    # 7. Education
    add_section("EDUCATION")
    for edu in tailored_resume.education:
        edu_table = [
            [Paragraph(f"<b>{clean_latex_markup_for_reportlab(edu.institution)}</b>", body_style),
             Paragraph(f"<b>{clean_latex_markup_for_reportlab(edu.location or 'Punjab, India')}</b>", ParagraphStyle("ER", parent=body_style, alignment=2))],
            [Paragraph(f'<i><font color="#2D3748">{clean_latex_markup_for_reportlab(edu.degree)}</font></i>', body_style),
             Paragraph(f'<i><font color="#2D3748">{clean_latex_markup_for_reportlab(edu.graduation_date)}</font></i>', ParagraphStyle("EDR", parent=body_style, alignment=2))]
        ]
        et = Table(edu_table, colWidths=[374, 177.52])
        et.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(et)
        if edu.coursework:
            story.append(Spacer(1, 0.5))
            cw = clean_latex_markup_for_reportlab(edu.coursework)
            story.append(Paragraph(f'<i><font color="#374151">Relevant Coursework: {cw}</font></i>', ParagraphStyle("CW", parent=body_style, fontSize=8.3, leading=9.7)))

    doc.build(story)
    return buffer.getvalue()
