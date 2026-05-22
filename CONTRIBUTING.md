# Contributing

Thank you for improving Job Finder Bot. This project is structured for clear reviews and safe public collaboration.

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/job_finder_bot.git
cd job_finder_bot
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
# Edit .env — add your BOT_TOKEN from @BotFather (never commit .env)
mkdir -p logs data data/resumes
```

## Run locally

```bash
make run
# or: python3 bot.py
```

## Tests

```bash
make test
```

Tests use in-memory SQLite and a fake `BOT_TOKEN`. They do not call Telegram or Remotive.

## Lint & format

```bash
make lint
make format
```

[Ruff](https://docs.astral.sh/ruff/) is configured in `pyproject.toml` (line length 100).

## Branch naming

| Prefix | Use for |
|--------|---------|
| `feature/` | New functionality (e.g. `feature/resume-parser`) |
| `fix/` | Bug fixes |
| `docs/` | README, CONTRIBUTING, screenshots |
| `chore/` | Tooling, CI, dependencies |

## Pull request checklist

- [ ] `make test` passes
- [ ] `make lint` passes
- [ ] No secrets in the diff (no `.env`, tokens, or real user data)
- [ ] Handlers stay thin — business logic in `services/`
- [ ] New behavior has tests when practical
- [ ] README updated if commands or env vars change

## Architecture reminder

```
handlers/  →  services/  →  repositories/  →  models/
```

Do not put SQL or parsing logic directly in handlers.

## Questions

Open a GitHub issue for bugs or feature ideas. For security concerns, do not post tokens in issues.
