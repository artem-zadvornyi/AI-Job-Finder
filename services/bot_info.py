from __future__ import annotations

from core.config import BOT_VERSION, __version__
from core.constants import (
    CMD_ABOUT,
    CMD_ALERTS_OFF,
    CMD_ALERTS_ON,
    CMD_DELETE_RESUME,
    CMD_HEALTH,
    CMD_HELP,
    CMD_JOBS,
    CMD_MY_RESUME,
    CMD_PING,
    CMD_RESUME,
    CMD_SAVED,
    CMD_SETTINGS,
    CMD_START,
    CMD_VERSION,
    JOB_SOURCE,
)


def build_help_message() -> str:
    return (
        "📖 Job Finder Bot — Help\n\n"
        "Find remote developer jobs tailored to your profile.\n\n"
        "🔹 Getting started\n"
        f"/{CMD_START} — set keyword, location, and work type\n"
        f"/{CMD_SETTINGS} — view your saved preferences\n\n"
        "🔹 Search & save\n"
        f"/{CMD_JOBS} — search jobs (one card at a time, use ⬅ ➡ to browse)\n"
        f"/{CMD_SAVED} — your bookmarked vacancies\n\n"
        "🔹 Resume & AI matching\n"
        f"/{CMD_RESUME} — upload PDF/DOCX resume for smarter ranking\n"
        f"/{CMD_MY_RESUME} — view detected skills and upload date\n"
        f"/{CMD_DELETE_RESUME} — remove stored resume\n\n"
        "🔹 Alerts\n"
        f"/{CMD_ALERTS_ON} — enable automatic new-job notifications\n"
        f"/{CMD_ALERTS_OFF} — disable notifications\n\n"
        "🔹 Tools\n"
        f"/{CMD_HEALTH} — bot and service health\n"
        f"/{CMD_VERSION} — version and runtime info\n"
        f"/{CMD_PING} — quick liveness check\n"
        f"/{CMD_HELP} — this message\n"
        f"/{CMD_ABOUT} — about the project\n\n"
        "💡 Tip: upload /resume then /jobs — vacancies show 🤖 AI Match scores."
    )


def build_about_message() -> str:
    return (
        "ℹ️ About Job Finder Bot\n\n"
        "A production-style Telegram assistant for discovering remote tech roles. "
        "Set your preferences once, browse ranked vacancies, save favorites, "
        "and receive alerts when new matches appear.\n\n"
        "🛠 Technologies\n"
        "• Python 3.12+\n"
        "• python-telegram-bot\n"
        "• SQLAlchemy (SQLite / PostgreSQL)\n"
        "• FastAPI health endpoint\n"
        "• Remotive public API\n"
        "• Docker & GitHub Actions CI\n\n"
        f"📦 Version: {__version__} (BOT_VERSION {BOT_VERSION})\n"
        f"📌 Job source: {JOB_SOURCE}\n\n"
        "Built as an open portfolio backend project — modular handlers, "
        "services, repositories, and automated tests."
    )
