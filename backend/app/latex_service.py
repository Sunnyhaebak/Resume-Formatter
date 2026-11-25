import os
import re
import io
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import jinja2
from pypdf import PdfReader, PdfWriter

from app.schemas import TailoredResume
from app.reportlab_renderer import generate_reportlab_pdf

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATE_PATH = DATA_DIR / "resume_template.tex"
logger = logging.getLogger(__name__)


def escape_latex(text: str) -> str:
    """
    Recursively escape special LaTeX characters in strings while preserving
    bold formatting (**text** and \\textbf{text}).
    Characters: &, %, $, #, _, {, }, ~, ^, \\
    """
    if not isinstance(text, str):
        return text

    res = text

    # Extract/protect existing \\textbf{...} and markdown **...**
    tb_map = {}
    counter = 0

    def replace_bold(match):
        nonlocal counter
        ph = f"@@BOLDPH{counter}@@"
        tb_map[ph] = match.group(1)
        counter += 1
        return ph

    # Match \textbf{...}
    res = re.sub(r'\\textbf\{([^}]+)\}', replace_bold, res)
    # Match **...**
    res = re.sub(r'\*\*([^*]+)\*\*', replace_bold, res)

    # Escape backslash first (for any non-protected backslashes)
    res = res.replace('\\', r'\textbackslash{}')

    # Standard LaTeX character escaping
    replacements = [
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\textasciitilde{}'),
        ('^', r'\textasciicircum{}'),
    ]
    for char, escaped in replacements:
        res = res.replace(char, escaped)

    # Restore bold placeholders with escaped inner text
    for ph, inner in tb_map.items():
        escaped_inner = escape_latex(inner)
        res = res.replace(ph, f"\\textbf{{{escaped_inner}}}")

    return res


def sanitize_for_latex(obj: Any) -> Any:
    """
    Recursively sanitize dictionaries, lists, and strings for LaTeX rendering.
    """
    if isinstance(obj, str):
        return escape_latex(obj)
    elif isinstance(obj, list):
        return [sanitize_for_latex(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: sanitize_for_latex(val) for key, val in obj.items()}
    elif hasattr(obj, "model_dump"):
        return sanitize_for_latex(obj.model_dump())
    return obj


def get_jinja_env() -> jinja2.Environment:
    """
    Configure Jinja2 with custom non-colliding delimiters for LaTeX.
    Delimiters:
      block: <% %>
      variable: << >>
      comment: <# #>
    """
    return jinja2.Environment(
        block_start_string='<%',
        block_end_string='%>',
        variable_start_string='<<',
        variable_end_string='>>',
        comment_start_string='<#',
        comment_end_string='#>',
        autoescape=False,
        loader=jinja2.FileSystemLoader(str(DATA_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_latex(tailored_resume: TailoredResume) -> str:
    """
    Sanitize tailored resume data and render into resume_template.tex.
    """
    env = get_jinja_env()
    template = env.get_template("resume_template.tex")
    sanitized_data = sanitize_for_latex(tailored_resume)
    rendered = template.render(**sanitized_data)
    return rendered


def compile_latex_to_pdf(rendered_tex: str, tailored_resume: Optional[TailoredResume] = None) -> bytes:
    """
    Compiles rendered LaTeX into a PDF.
    1. Checks if pdflatex is available in the environment (e.g. inside Docker container).
     2. If pdflatex is not on the host, uses ReportLab to approximate the template's
         layout and typography in a 1-page PDF.
    """
    pdflatex_bin = shutil.which("pdflatex")
    if not pdflatex_bin and os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            miktex_executable = (
                Path(local_app_data)
                / "Programs"
                / "MiKTeX"
                / "miktex"
                / "bin"
                / "x64"
                / "pdflatex.exe"
            )
            if miktex_executable.is_file():
                pdflatex_bin = str(miktex_executable)

    if pdflatex_bin:
        logger.info("Compiling resume with pdflatex at %s.", pdflatex_bin)
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_file = os.path.join(tmpdir, "resume.tex")
            pdf_file = os.path.join(tmpdir, "resume.pdf")
            log_file = os.path.join(tmpdir, "resume.log")

            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(rendered_tex)

            try:
                proc = subprocess.run(
                    [
                        pdflatex_bin,
                        "-interaction=nonstopmode",
                        "-halt-on-error",
                        "resume.tex",
                    ],
                    cwd=tmpdir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30,
                    text=True,
                )

                if proc.returncode != 0 or not os.path.exists(pdf_file):
                    log_content = ""
                    if os.path.exists(log_file):
                        with open(log_file, "r", encoding="utf-8", errors="ignore") as lf:
                            log_content = lf.read()
                    err_msg = (
                        f"pdflatex compilation failed with code {proc.returncode}.\n"
                        f"Log excerpt:\n{log_content[-1500:]}"
                    )
                    raise RuntimeError(err_msg)

                with open(pdf_file, "rb") as pf:
                    return pf.read()

            except subprocess.TimeoutExpired:
                raise RuntimeError("pdflatex compilation timed out after 30 seconds.")

    # High-quality fallback rendering with ReportLab
    if tailored_resume:
        logger.warning(
            "pdflatex is unavailable; using the ReportLab fallback renderer, which approximates resume_template.tex."
        )
        return generate_reportlab_pdf(tailored_resume)

    # Emergency fallback
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def verify_page_count(pdf_bytes: bytes) -> int:
    """
    Validates page count using pypdf.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return len(reader.pages)
