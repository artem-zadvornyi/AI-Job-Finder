from __future__ import annotations

import re
from pathlib import Path

from core.constants import RESUME_ALLOWED_EXTENSIONS, RESUME_MAX_BYTES, RESUME_STORAGE_DIR

_UNSAFE_NAME = re.compile(r"[^a-zA-Z0-9._-]+")


def resume_base_dir() -> Path:
    base = Path(RESUME_STORAGE_DIR)
    base.mkdir(parents=True, exist_ok=True)
    return base


def user_resume_dir(user_id: int) -> Path:
    directory = resume_base_dir() / str(user_id)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def sanitize_filename(original: str) -> str:
    """Strip path components and unsafe characters from user-provided names."""
    name = Path(original).name.strip()
    if not name:
        name = "resume"
    stem = Path(name).stem
    suffix = Path(name).suffix.lower().lstrip(".")
    safe_stem = _UNSAFE_NAME.sub("_", stem).replace("..", "_")[:80] or "resume"
    if suffix in RESUME_ALLOWED_EXTENSIONS:
        return f"{safe_stem}.{suffix}"
    return safe_stem


def validate_resume_upload(
    *,
    filename: str | None,
    file_size: int | None,
    mime_type: str | None,
) -> tuple[str, str]:
    """
    Validate upload metadata.

    Returns (safe_filename, extension) or raises ValueError.
    """
    safe_name = sanitize_filename(filename or "resume")
    ext = Path(safe_name).suffix.lower().lstrip(".")
    if ext not in RESUME_ALLOWED_EXTENSIONS:
        raise ValueError("Only PDF and DOCX files are supported.")

    if mime_type:
        allowed_mimes = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        if mime_type not in allowed_mimes:
            raise ValueError("Invalid file type. Upload a PDF or DOCX resume.")

    size = file_size or 0
    if size <= 0:
        raise ValueError("Empty file.")
    if size > RESUME_MAX_BYTES:
        raise ValueError(f"File too large. Maximum size is {RESUME_MAX_BYTES // (1024 * 1024)} MB.")

    return safe_name, ext


def resolve_resume_path(user_id: int, filename: str) -> Path:
    """Resolve a path under the user's resume directory (prevents traversal)."""
    user_dir = user_resume_dir(user_id).resolve()
    target = (user_dir / sanitize_filename(filename)).resolve()
    if not str(target).startswith(str(user_dir)):
        raise ValueError("Invalid file path.")
    return target


def save_resume_file(user_id: int, data: bytes, filename: str) -> Path:
    """Write resume bytes to data/resumes/<user_id>/<filename>."""
    safe_name, _ext = validate_resume_upload(
        filename=filename,
        file_size=len(data),
        mime_type=None,
    )
    path = resolve_resume_path(user_id, safe_name)
    path.write_bytes(data)
    return path


def delete_user_resume_files(user_id: int) -> None:
    """Remove all files in the user's resume directory."""
    user_dir = user_resume_dir(user_id)
    if not user_dir.exists():
        return
    for item in user_dir.iterdir():
        if item.is_file():
            item.unlink()
    try:
        user_dir.rmdir()
    except OSError:
        pass
