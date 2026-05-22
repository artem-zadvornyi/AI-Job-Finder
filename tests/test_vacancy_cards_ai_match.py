from __future__ import annotations

from services.vacancy_cards import format_vacancy_from_dict


def test_vacancy_card_shows_ai_match_block() -> None:
    text = format_vacancy_from_dict(
        {
            "title": "Python Developer",
            "company": "Co",
            "location": "Remote",
            "salary": None,
            "link": "https://example.com",
            "source": "Remotive",
            "description": "Backend APIs",
            "match_score": "84",
            "matched_skills": "Python,FastAPI,Docker",
        },
        page_index=0,
        page_total=3,
    )
    assert "🤖 AI Match: 84%" in text
    assert "Python" in text
    assert "FastAPI" in text
