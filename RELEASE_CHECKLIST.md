# Release checklist

Use this list before publishing the repository on GitHub or deploying to production.

## Code quality

- [ ] `make test` — all tests pass
- [ ] `make lint` — Ruff reports no errors
- [ ] `make docker-build` — Docker image builds successfully

## Secrets & sensitive data

- [ ] `.env` is **not** committed (`git status` must not list `.env`)
- [ ] No real `BOT_TOKEN` in tracked files (search: `git grep -i "BOT_TOKEN="` should only hit `.env.example` with placeholder text)
- [ ] No API keys, passwords, or Railway/Render URLs in source or docs
- [ ] `*.db` / `data/*.db` are not committed
- [ ] `logs/` and `data/resumes/` are not committed

## Documentation

- [ ] README screenshots section links to files under `docs/screenshots/`
- [ ] Screenshot PNGs added (or placeholders documented until you capture them)
- [ ] CI badge URL updated (`YOUR_USERNAME` → your GitHub username)
- [ ] `.env.example` contains placeholders only

## Deployment (Railway / Render / VPS)

- [ ] `BOT_TOKEN` set in platform environment variables (not in repo)
- [ ] `ENVIRONMENT=production` on hosted deploy
- [ ] `DATABASE_URL` set if using PostgreSQL (optional)
- [ ] `ADMIN_USER_ID` set if using `/stats`
- [ ] Health check URL responds: `GET /health` → `{"status":"ok",...}`

## Final git check

```bash
git status
git check-ignore -v .env logs/ data/job_finder_bot.db
git grep -E "[0-9]{8,}:[A-Za-z0-9_-]{20,}" -- ':!.env.example' ':!venv' ':!.venv'
```

If the last command finds matches outside test fixtures, **rotate your bot token** via [@BotFather](https://t.me/BotFather) before pushing.
