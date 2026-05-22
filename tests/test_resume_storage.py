from __future__ import annotations

import pytest

from services.resume_storage import (
    delete_user_resume_files,
    sanitize_filename,
    save_resume_file,
    validate_resume_upload,
)


def test_sanitize_filename_strips_path_traversal() -> None:
    assert sanitize_filename("../../etc/passwd.pdf") == "passwd.pdf"
    assert sanitize_filename("..\\evil.docx") == "__evil.docx"


def test_validate_resume_upload_rejects_txt() -> None:
    with pytest.raises(ValueError, match="PDF and DOCX"):
        validate_resume_upload(filename="resume.txt", file_size=100, mime_type="text/plain")


def test_validate_resume_upload_rejects_oversized_file() -> None:
    from core.constants import RESUME_MAX_BYTES

    with pytest.raises(ValueError, match="too large"):
        validate_resume_upload(
            filename="big.pdf",
            file_size=RESUME_MAX_BYTES + 1,
            mime_type="application/pdf",
        )


def test_save_and_delete_resume_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("services.resume_storage.resume_base_dir", lambda: tmp_path)
    data = b"%PDF-1.4 minimal"
    path = save_resume_file(42, data, "my resume.pdf")
    assert path.exists()
    assert path.parent.name == "42"
    delete_user_resume_files(42)
    assert not path.exists()
