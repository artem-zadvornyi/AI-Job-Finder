from __future__ import annotations

import io
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from core.constants import RESUME_ALLOWED_EXTENSIONS

# Canonical skill/tech labels and word-boundary patterns (no external AI).
_SKILL_PATTERNS: tuple[tuple[str, str], ...] = (
    ("Python", r"\bpython\b"),
    ("FastAPI", r"\bfastapi\b"),
    ("Django", r"\bdjango\b"),
    ("Flask", r"\bflask\b"),
    ("JavaScript", r"\bjavascript\b|\bjs\b"),
    ("TypeScript", r"\btypescript\b|\bts\b"),
    ("React", r"\breact\b"),
    ("Vue", r"\bvue\.?js\b|\bvue\b"),
    ("Node.js", r"\bnode\.?js\b"),
    ("Go", r"\bgolang\b|\bgo\b"),
    ("Java", r"\bjava\b"),
    ("Kotlin", r"\bkotlin\b"),
    ("Rust", r"\brust\b"),
    ("C++", r"\bc\+\+\b"),
    ("SQL", r"\bsql\b"),
    ("PostgreSQL", r"\bpostgres(?:ql)?\b"),
    ("MySQL", r"\bmysql\b"),
    ("MongoDB", r"\bmongodb\b"),
    ("Redis", r"\bredis\b"),
    ("Docker", r"\bdocker\b"),
    ("Kubernetes", r"\bkubernetes\b|\bk8s\b"),
    ("AWS", r"\baws\b|amazon web services"),
    ("GCP", r"\bgcp\b|google cloud"),
    ("Azure", r"\bazure\b"),
    ("Linux", r"\blinux\b"),
    ("Git", r"\bgit\b"),
    ("CI/CD", r"\bci/?cd\b|continuous integration"),
    ("REST API", r"\brest\b|\brestful\b"),
    ("GraphQL", r"\bgraphql\b"),
    ("Microservices", r"\bmicroservices?\b"),
    ("Machine Learning", r"\bmachine learning\b|\bml\b"),
    ("Data Science", r"\bdata science\b"),
    ("Pytest", r"\bpytest\b"),
    ("Celery", r"\bcelery\b"),
    ("RabbitMQ", r"\brabbitmq\b"),
    ("Kafka", r"\bkafka\b"),
    ("Terraform", r"\bterraform\b"),
    ("Ansible", r"\bansible\b"),
)

_TECH_PATTERNS: tuple[tuple[str, str], ...] = _SKILL_PATTERNS

_EXPERIENCE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("Backend", r"\bbackend\b|back-end"),
    ("Frontend", r"\bfrontend\b|front-end"),
    ("Full Stack", r"\bfull[\s-]?stack\b"),
    ("Software Engineer", r"\bsoftware engineer\b"),
    ("Developer", r"\bdeveloper\b"),
    ("DevOps", r"\bdevops\b"),
    ("Team Lead", r"\bteam lead\b"),
    ("Senior", r"\bsenior\b"),
    ("Junior", r"\bjunior\b"),
    ("Internship", r"\bintern(?:ship)?\b"),
    ("Agile", r"\bagile\b|\bscrum\b"),
)

_EDUCATION_PATTERNS: tuple[tuple[str, str], ...] = (
    ("Bachelor", r"\bbachelor\b|\bb\.?sc\b"),
    ("Master", r"\bmaster\b|\bm\.?sc\b"),
    ("PhD", r"\bph\.?d\b|doctorate"),
    ("Computer Science", r"\bcomputer science\b|\bcs\b"),
    ("Mathematics", r"\bmathematics\b|\bmath\b"),
    ("Engineering", r"\bengineering\b"),
)


@dataclass(frozen=True)
class ParsedResume:
    skills: tuple[str, ...]
    technologies: tuple[str, ...]
    experience_keywords: tuple[str, ...]
    education_keywords: tuple[str, ...]

    def all_match_terms(self) -> tuple[str, ...]:
        seen: set[str] = set()
        ordered: list[str] = []
        for group in (self.skills, self.technologies, self.experience_keywords):
            for item in group:
                key = item.lower()
                if key not in seen:
                    seen.add(key)
                    ordered.append(item)
        return tuple(ordered)

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str) -> ParsedResume | None:
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return cls(
            skills=tuple(data.get("skills") or ()),
            technologies=tuple(data.get("technologies") or ()),
            experience_keywords=tuple(data.get("experience_keywords") or ()),
            education_keywords=tuple(data.get("education_keywords") or ()),
        )


def _extract_matches(text: str, patterns: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    blob = text.lower()
    found: list[str] = []
    seen: set[str] = set()
    for label, pattern in patterns:
        if re.search(pattern, blob, re.I) and label.lower() not in seen:
            seen.add(label.lower())
            found.append(label)
    return tuple(found)


def extract_resume_fields(text: str) -> ParsedResume:
    """Parse plain resume text into structured keyword groups."""
    cleaned = (text or "").strip()
    if not cleaned:
        return ParsedResume((), (), (), ())

    return ParsedResume(
        skills=_extract_matches(cleaned, _SKILL_PATTERNS),
        technologies=_extract_matches(cleaned, _TECH_PATTERNS),
        experience_keywords=_extract_matches(cleaned, _EXPERIENCE_PATTERNS),
        education_keywords=_extract_matches(cleaned, _EDUCATION_PATTERNS),
    )


def _read_pdf_bytes(data: bytes) -> str:
    from PyPDF2 import PdfReader

    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            parts.append(page_text)
    return "\n".join(parts)


def _read_docx_bytes(data: bytes) -> str:
    from docx import Document

    document = Document(io.BytesIO(data))
    return "\n".join(p.text for p in document.paragraphs if p.text)


def parse_resume_bytes(data: bytes, extension: str) -> ParsedResume:
    """Parse resume file bytes (pdf or docx) into structured fields."""
    ext = extension.lower().lstrip(".")
    if ext not in RESUME_ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported extension: {extension}")

    if ext == "pdf":
        text = _read_pdf_bytes(data)
    else:
        text = _read_docx_bytes(data)

    return extract_resume_fields(text)


def parse_resume_file(path: Path) -> ParsedResume:
    """Parse a resume file from disk."""
    ext = path.suffix.lower().lstrip(".")
    return parse_resume_bytes(path.read_bytes(), ext)
