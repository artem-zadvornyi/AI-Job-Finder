# Job Finder Bot

**A production-style Telegram bot that helps developers find remote jobs** — with preference-based search, resume-aware ranking, saved vacancies, and scheduled alerts.

Built as a **portfolio backend project**: layered architecture, async SQLAlchemy, Docker, CI, and deploy paths for Railway, Render, and VPS.

![CI](https://img.shields.io/github/actions/workflow/status/YOUR_USERNAME/job_finder_bot/ci.yml?label=CI)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

> Replace `YOUR_USERNAME` in the CI badge after publishing to GitHub.

---

## Project pitch

Job Finder Bot connects to the [Remotive](https://remotive.com) public API, ranks vacancies for each user’s keyword and location, and delivers results inside Telegram with pagination and inline actions. Users can upload a **PDF/DOCX resume** for keyword-based “AI match” scoring (no paid AI APIs), bookmark roles, and enable background alerts for new listings.

The codebase demonstrates **real backend practices**: dependency injection, repository pattern, startup validation, structured logging, FastAPI health checks, PostgreSQL or SQLite, and automated tests in CI.

---

## Features

| Area | What you get |
|------|----------------|
| **Onboarding** | `/start` — keyword, location, work type |
| **Job search** | `/jobs` — one vacancy per page, instant cached paging |
| **Resume & matching** | `/resume`, `/my_resume`, `/delete_resume` — parse skills, show `🤖 AI Match: N%` on cards |
| **Bookmarks** | `/saved` — save, open, delete vacancies |
| **Alerts** | `/alerts_on` / `/alerts_off` — scheduler, duplicate prevention |
| **Ops** | `/health`, `/version`, `/ping`, admin `/stats` |
| **Platform** | Telegram command menu, global error handler, rotating logs |

---

## Architecture

```
                         ┌──────────────────┐
                         │   Telegram API   │
                         └────────┬─────────┘
                                  │
                       ┌──────────▼──────────┐
                       │       bot.py        │
                       │ handlers + lifecycle│
                       └──────────┬──────────┘
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
    handlers/               services/                  core/
    (thin commands)    Remotive, resume, alerts    config, DB, logging
          │                       │
          └───────────┬───────────┘
                      ▼
              repositories/  →  models/  →  SQLite / PostgreSQL
                      │
          ┌───────────┴────────────┐
          ▼                        ▼
   data/resumes/ (uploads)    logs/app.log
   FastAPI GET /health
```

**Rule:** handlers → services → repositories → models. No SQL or resume parsing in handlers.

---

## Technologies

| Layer | Stack |
|--------|--------|
| Language | Python 3.12+ |
| Bot | python-telegram-bot 22.x, APScheduler |
| HTTP | FastAPI + Uvicorn (`/health`) |
| Database | SQLAlchemy 2 async — SQLite (aiosqlite) or PostgreSQL (asyncpg) |
| Resume | PyPDF2, python-docx, local `data/resumes/` |
| Jobs API | Remotive REST |
| Quality | pytest, Ruff, GitHub Actions |
| Deploy | Docker, Docker Compose, Procfile |

---

## Screenshots

Add PNG captures under `docs/screenshots/` before sharing the repo publicly:

| File | Suggested capture |
|------|-------------------|
| [docs/screenshots/start.png](docs/screenshots/start.png) | `/start` onboarding flow |
| [docs/screenshots/jobs-ai-match.png](docs/screenshots/jobs-ai-match.png) | `/jobs` with AI match score and paging |
| [docs/screenshots/saved.png](docs/screenshots/saved.png) | `/saved` bookmarks |
| [docs/screenshots/resume.png](docs/screenshots/resume.png) | `/resume` upload and `/my_resume` |
| [docs/screenshots/health.png](docs/screenshots/health.png) | `/health` or `curl /health` JSON |
| [docs/screenshots/docker.png](docs/screenshots/docker.png) | `docker compose up` / healthy container |

```markdown
![Start flow](docs/screenshots/start.png)
![Jobs with AI match](docs/screenshots/jobs-ai-match.png)
![Saved jobs](docs/screenshots/saved.png)
![Resume profile](docs/screenshots/resume.png)
![Health check](docs/screenshots/health.png)
![Docker](docs/screenshots/docker.png)
```

---

## Quick start

```bash
git clone https://github.com/YOUR_USERNAME/job_finder_bot.git
cd job_finder_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set BOT_TOKEN from @BotFather
mkdir -p logs data data/resumes
python3 bot.py
```

Verify: `/ping` in Telegram · `curl http://localhost:8000/health`

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Telegram token from [@BotFather](https://t.me/BotFather) |
| `ENVIRONMENT` | No | `development` or `production` (default: `development`) |
| `PORT` | No | Health HTTP port (default `8000`) |
| `DATABASE_URL` | No | PostgreSQL — overrides SQLite when set |
| `SQLITE_URL` | No | SQLite URL if `DATABASE_URL` is empty |
| `ADMIN_USER_ID` | No | Telegram user id for `/stats` |
| `ALERTS_INTERVAL_SECONDS` | No | Alert interval (default `1800`, min `30`) |

See [.env.example](.env.example). **Never commit `.env`.**

---

## Docker

```bash
cp .env.example .env
mkdir -p logs data
docker compose build
docker compose up -d
docker compose logs -f
curl http://localhost:8000/health
```

`.env` is excluded from the image (see [.dockerignore](.dockerignore)). Mounts: `./logs`, `./data`.

---

## Tests

```bash
make install   # runtime + dev deps
make test      # pytest + coverage
make lint      # Ruff
```

Tests use in-memory SQLite and a fake token — no live Telegram or Remotive calls.

---

## Deployment

| Platform | Notes |
|----------|--------|
| **Railway** | `BOT_TOKEN`, `ENVIRONMENT=production`, optional PostgreSQL plugin → `DATABASE_URL` |
| **Render** | Web service, start `python bot.py`, health path `/health` |
| **VPS** | `docker compose up -d --build` |

Full steps: see [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Set preferences |
| `/jobs` | Search with pagination |
| `/resume` | Upload PDF/DOCX |
| `/my_resume` | View parsed profile |
| `/delete_resume` | Remove resume |
| `/saved` | Saved vacancies |
| `/alerts_on` / `/alerts_off` | Job alerts |
| `/help` / `/about` | Help and project info |
| `/health` / `/version` / `/ping` | Ops |

---

## Portfolio value

This repo is suitable to show recruiters and hiring managers:

- **Clean architecture** — handlers, services, repositories, models
- **Async I/O** — SQLAlchemy 2, httpx, telegram bot
- **Product features** — pagination UX, resume parsing, match scoring, alerts
- **Production habits** — config validation, health endpoint, Docker, CI, structured logs
- **Safety** — secrets in env only, gitignore for DB/logs/resumes

---

## Publishing to GitHub (safe git workflow)

**Before your first push**, confirm secrets are not tracked:

```bash
git status
git check-ignore -v .env logs/ data/
```

**Initial commit:**

```bash
git init
git add .
git status          # .env must NOT appear here
git commit -m "Initial public release: Job Finder Bot"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/job_finder_bot.git
git push -u origin main
```

**Never commit:**

- `.env` or any file with a real `BOT_TOKEN`
- `*.db`, `logs/`, `data/resumes/` uploads
- `__pycache__/`, `.venv/`

If a token was ever pushed, revoke it in [@BotFather](https://t.me/BotFather) and set a new one in your host’s environment variables only.

---

## Project layout

```
job_finder_bot/
├── bot.py
├── core/          config, database, constants, logging, startup
├── handlers/      Telegram command handlers
├── services/      business logic (Remotive, resume, alerts, health)
├── repositories/  database access
├── models/        SQLAlchemy entities
├── tests/
├── docs/screenshots/
├── data/          SQLite + resumes (gitignored contents)
└── logs/          app logs (gitignored)
```

---

## Contributing & release

- [CONTRIBUTING.md](CONTRIBUTING.md) — setup, tests, PR guidelines
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) — pre-publish verification
- [LICENSE](LICENSE) — MIT

---

## License

MIT License — see [LICENSE](LICENSE).
