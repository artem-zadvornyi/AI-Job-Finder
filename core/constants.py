from __future__ import annotations

from typing import Final

# --- Bot metadata (version lives in core.config.BOT_VERSION) ---
JOB_SOURCE: Final[str] = "Remotive"

# --- Telegram commands ---
CMD_START: Final[str] = "start"
CMD_JOBS: Final[str] = "jobs"
CMD_SETTINGS: Final[str] = "settings"
CMD_SAVED: Final[str] = "saved"
CMD_ALERTS_ON: Final[str] = "alerts_on"
CMD_ALERTS_OFF: Final[str] = "alerts_off"
CMD_HEALTH: Final[str] = "health"
CMD_VERSION: Final[str] = "version"
CMD_STATS: Final[str] = "stats"
CMD_PING: Final[str] = "ping"
CMD_HELP: Final[str] = "help"
CMD_ABOUT: Final[str] = "about"
CMD_RESUME: Final[str] = "resume"
CMD_MY_RESUME: Final[str] = "my_resume"
CMD_DELETE_RESUME: Final[str] = "delete_resume"

COMMAND_DESCRIPTIONS: Final[tuple[tuple[str, str], ...]] = (
    (CMD_START, "Set up your job search profile"),
    (CMD_JOBS, "Search remote jobs with pagination"),
    (CMD_SAVED, "View your saved vacancies"),
    (CMD_SETTINGS, "View your search preferences"),
    (CMD_ALERTS_ON, "Enable automatic job alerts"),
    (CMD_ALERTS_OFF, "Disable automatic job alerts"),
    (CMD_HELP, "Show all commands and tips"),
    (CMD_ABOUT, "About this bot and tech stack"),
    (CMD_HEALTH, "Check bot and service health"),
    (CMD_VERSION, "Bot version and runtime info"),
    (CMD_PING, "Quick liveness check"),
    (CMD_STATS, "Admin: usage statistics"),
    (CMD_RESUME, "Upload or replace your resume"),
    (CMD_MY_RESUME, "View resume profile and skills"),
    (CMD_DELETE_RESUME, "Delete stored resume"),
)

# --- Alerts scheduler ---
DEFAULT_ALERTS_INTERVAL_SECONDS: Final[int] = 1800
MIN_ALERTS_INTERVAL_SECONDS: Final[int] = 30
ALERTS_SCHEDULER_FIRST_DELAY_SECONDS: Final[int] = 15
ALERTS_JOB_NAME: Final[str] = "vacancy_alerts"
ALERT_HEADER: Final[str] = "🚨 New vacancy match\n\n"

# --- Remotive API / job matching ---
REMOTIVE_API_URL: Final[str] = "https://remotive.com/api/remote-jobs"
JOB_SOURCE_REMOTIVE: Final[str] = "Remotive"
JOB_SOURCE_DEMO: Final[str] = "Demo listings"
DESCRIPTION_MAX_LEN: Final[int] = 300
DESCRIPTION_PREVIEW_CHARS: Final[int] = 320
MAX_JOB_MATCHES: Final[int] = 5
MIN_JOB_RESULTS_SOFT: Final[int] = 3
PYTHON_DEVELOPER_MIN_SCORE: Final[int] = 88
REMOTIVE_HTTP_TIMEOUT_SECONDS: Final[float] = 30.0
HEALTH_CHECK_HTTP_TIMEOUT_SECONDS: Final[float] = 10.0

# --- Demo listings ---
DEMO_PAD_MESSAGE: Final[str] = "Demo listing — no real job found for this slot."
DEMO_API_UNREACHABLE_MESSAGE: Final[str] = "Demo listing — Remotive API unreachable."

# --- Callback data & session cache ---
SAVE_CALLBACK_PREFIX: Final[str] = "save:"
DELETE_SAVED_CALLBACK_PREFIX: Final[str] = "del_saved:"
JOBS_CALLBACK_PREFIX: Final[str] = "jobs:"
ALERT_SAVE_CALLBACK_PREFIX: Final[str] = "asv:"
VACANCY_CACHE_KEY: Final[str] = "vacancy_cache"  # legacy / saved list
JOBS_RESULTS_KEY: Final[str] = "jobs_results"
JOBS_PAGE_INDEX_KEY: Final[str] = "jobs_page_index"
ALERT_VACANCY_CACHE_KEY: Final[str] = "alert_vacancy_cache"
PROCESSED_CALLBACKS_KEY: Final[str] = "_processed_callback_ids"
SESSION_SAVED_LINKS_KEY: Final[str] = "_session_saved_links"
RESUME_AWAITING_UPLOAD_KEY: Final[str] = "awaiting_resume_upload"

# --- Resume upload ---
RESUME_STORAGE_DIR: Final[str] = "data/resumes"
RESUME_ALLOWED_EXTENSIONS: Final[frozenset[str]] = frozenset({"pdf", "docx"})
RESUME_MAX_BYTES: Final[int] = 5 * 1024 * 1024
RESUME_MAX_MATCHED_SKILLS_DISPLAY: Final[int] = 5

# --- Work types ---
WORK_TYPES: Final[tuple[str, ...]] = ("Any", "Remote", "Office", "Hybrid")
DEFAULT_WORK_TYPE: Final[str] = "Any"

# --- User-facing messages ---
MSG_USER_ERROR: Final[str] = "⚠️ Something went wrong. Please try again later."
MSG_SAVED: Final[str] = "✅ Vacancy saved."
MSG_ALREADY_SAVED: Final[str] = "⚠️ Vacancy already saved."
MSG_NO_SAVED: Final[str] = "You have no saved jobs yet."
MSG_DELETED: Final[str] = "🗑 Vacancy deleted."
MSG_ALREADY_DELETED: Final[str] = "This vacancy was already deleted."
MSG_LISTING_EXPIRED: Final[str] = "This listing expired. Run /jobs again."
MSG_ACTION_UNAVAILABLE: Final[str] = "This action is no longer available."
MSG_JOBS_BOUNDARY_FIRST: Final[str] = "You're on the first vacancy."
MSG_JOBS_BOUNDARY_LAST: Final[str] = "You're on the last vacancy."
MSG_ALERTS_ON: Final[str] = "✅ Automatic job alerts enabled."
MSG_ALERTS_OFF: Final[str] = "🔕 Automatic job alerts disabled."
MSG_NO_PREFS: Final[str] = (
    "Set your job preferences first.\nUse /start to choose keyword, location, and work type."
)
MSG_ADMIN_ONLY: Final[str] = "⛔ This command is for the bot admin only."
MSG_ADMIN_NOT_CONFIGURED: Final[str] = "⛔ Admin is not configured. Set ADMIN_USER_ID in .env."
MSG_HEALTH_RUNNING: Final[str] = "✅ Bot is running."
MSG_PONG: Final[str] = "Pong! Bot is alive."
MSG_JOBS_SEARCHING: Final[str] = "🔍 Searching for remote jobs..."
MSG_JOBS_FAILED: Final[str] = (
    "⚠️ Job search failed.\n\nPlease try again in a moment or use /health to check status."
)
MSG_JOBS_EMPTY: Final[str] = (
    "😕 No matching vacancies right now.\n\n"
    "Try updating your keyword in /settings or search for:\n"
    "{suggestions}\n\n"
    "Tip: broader titles like “Backend developer” usually return more results."
)
JOB_SEARCH_SUGGESTIONS: Final[tuple[str, ...]] = (
    "Python developer",
    "Backend developer",
    "FastAPI developer",
)
MSG_PREFS_NOT_SET: Final[str] = (
    "Your preferences are not set yet.\nUse /start to set: keyword, location, and work type."
)
MSG_RESUME_UPLOAD_PROMPT: Final[str] = (
    "📄 Send your resume as a **PDF** or **DOCX** file (max 5 MB).\n\n"
    "I'll extract skills and use them to rank job matches.\n"
    "Use /my_resume to view your profile or /delete_resume to remove it."
)
MSG_RESUME_SAVED: Final[str] = (
    "✅ Resume saved and analyzed.\n\n"
    "Detected skills: {skills}\n\n"
    "Run /jobs to see AI-ranked vacancies."
)
MSG_RESUME_NO_SKILLS: Final[str] = (
    "✅ Resume saved, but few recognizable tech keywords were found.\n"
    "Try a clearer skills section, then run /jobs again."
)
MSG_RESUME_INVALID_FILE: Final[str] = (
    "⚠️ Invalid resume file.\n\nPlease upload a PDF or DOCX under 5 MB."
)
MSG_RESUME_NONE: Final[str] = (
    "You have not uploaded a resume yet.\nUse /resume to upload PDF or DOCX."
)
MSG_RESUME_DELETED: Final[str] = "🗑 Resume and parsed data deleted."
MSG_RESUME_REPLACE_HINT: Final[str] = "Sending a new file will replace your current resume."

# --- Logging files ---
LOG_DIR_NAME: Final[str] = "logs"
LOG_FILE_NAME: Final[str] = "app.log"
LOG_MAX_BYTES: Final[int] = 1 * 1024 * 1024
LOG_BACKUP_COUNT: Final[int] = 3

# --- Environment ---
ENV_DEVELOPMENT: Final[str] = "development"
ENV_PRODUCTION: Final[str] = "production"
