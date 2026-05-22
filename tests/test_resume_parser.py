from __future__ import annotations

import io
import json

import pytest
from docx import Document

from services.resume_parser import (
    ParsedResume,
    extract_resume_fields,
    parse_resume_bytes,
)


def test_extract_resume_fields_python_fastapi_docker() -> None:
    text = """
    John Doe
    Python developer with FastAPI and Docker experience.
    Backend engineer, Bachelor in Computer Science.
    """
    parsed = extract_resume_fields(text)
    assert "Python" in parsed.skills
    assert "FastAPI" in parsed.skills
    assert "Docker" in parsed.skills
    assert "Backend" in parsed.experience_keywords
    assert "Computer Science" in parsed.education_keywords


def test_parse_docx_bytes() -> None:
    buffer = io.BytesIO()
    doc = Document()
    doc.add_paragraph("Senior Python developer. Skills: FastAPI, PostgreSQL, Docker.")
    doc.save(buffer)
    parsed = parse_resume_bytes(buffer.getvalue(), "docx")
    assert "Python" in parsed.skills
    assert "FastAPI" in parsed.skills


def test_parse_resume_bytes_rejects_invalid_extension() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        parse_resume_bytes(b"text", "txt")


def test_parsed_resume_json_roundtrip() -> None:
    profile = ParsedResume(
        skills=("Python",),
        technologies=("Docker",),
        experience_keywords=("Backend",),
        education_keywords=("Bachelor",),
    )
    restored = ParsedResume.from_json(profile.to_json())
    assert restored is not None
    assert restored.skills == ("Python",)
    assert json.loads(profile.to_json())["technologies"] == ["Docker"]
