from __future__ import annotations

from services.job_search import format_empty_results_message


def test_empty_results_message_includes_suggestions() -> None:
    text = format_empty_results_message()
    assert "Python developer" in text
    assert "Backend developer" in text
    assert "FastAPI developer" in text
