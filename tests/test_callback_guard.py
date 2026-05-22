from __future__ import annotations

from services.callback_guard import (
    is_link_saved_in_session,
    mark_link_saved_in_session,
    try_claim_callback,
)


def test_try_claim_callback_prevents_duplicates() -> None:
    user_data: dict = {}
    assert try_claim_callback(user_data, "cq-1") is True
    assert try_claim_callback(user_data, "cq-1") is False
    assert try_claim_callback(user_data, "cq-2") is True


def test_session_saved_links_tracking() -> None:
    user_data: dict = {}
    link = "https://example.com/job/99"
    assert is_link_saved_in_session(user_data, link) is False
    mark_link_saved_in_session(user_data, link)
    assert is_link_saved_in_session(user_data, link) is True
