from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass

import httpx

from core.constants import (
    DEMO_API_UNREACHABLE_MESSAGE,
    DEMO_PAD_MESSAGE,
    DESCRIPTION_MAX_LEN,
    JOB_SOURCE_DEMO,
    JOB_SOURCE_REMOTIVE,
    MAX_JOB_MATCHES,
    MIN_JOB_RESULTS_SOFT,
    PYTHON_DEVELOPER_MIN_SCORE,
    REMOTIVE_API_URL,
    REMOTIVE_HTTP_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)

# Re-export for health checks and other modules.
API_URL = REMOTIVE_API_URL
SOURCE_REMOTIVE = JOB_SOURCE_REMOTIVE
SOURCE_DEMO = JOB_SOURCE_DEMO
MAX_MATCHES = MAX_JOB_MATCHES

# At least one must match in title OR plain-text description (gate before scoring).
_IMPORTANT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bpython\b", re.I),
    re.compile(r"\bbackend\b|back\s*[- ]end", re.I),
    re.compile(r"\bdeveloper\b", re.I),
    re.compile(r"\bengineer\b", re.I),
    re.compile(r"\bsoftware\b", re.I),
    re.compile(r"\bapi\b", re.I),
    re.compile(r"\bdjango\b", re.I),
    re.compile(r"\bflask\b", re.I),
    re.compile(r"\bfastapi\b", re.I),
)

# Strong stack signals (title_points, description_points) — beginner Python/backend focus.
_PRIMARY_STACK: tuple[tuple[re.Pattern[str], int, int], ...] = (
    (re.compile(r"\bpython\b", re.I), 160, 58),
    (re.compile(r"\bbackend\b|back\s*[- ]end", re.I), 150, 52),
    (re.compile(r"\bfastapi\b", re.I), 145, 50),
    (re.compile(r"\bdjango\b", re.I), 145, 50),
    (re.compile(r"\bflask\b", re.I), 140, 48),
    (re.compile(r"\bapi\b", re.I), 75, 28),
)

_SECONDARY_GENERIC: tuple[tuple[re.Pattern[str], int, int], ...] = (
    (re.compile(r"\bdeveloper\b", re.I), 38, 12),
    (re.compile(r"\bengineer\b", re.I), 38, 12),
    (re.compile(r"\bsoftware\b", re.I), 32, 10),
)
_SECONDARY_GENERIC_CAP = 48

_JUNIOR_FRIENDLY: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bjunior\b", re.I),
    re.compile(r"\bentry[\s-]level\b", re.I),
    re.compile(r"\bintern(?:ship)?\b", re.I),
    re.compile(r"\btrainee\b", re.I),
    re.compile(r"\bgraduate\b", re.I),
)
_JUNIOR_TITLE_BONUS = 52
_JUNIOR_DESC_BONUS = 24

# Penalize but do not block — used in scoring and deferred until better matches fill top 5.
_ESCALATION_TERMS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bsenior\b", re.I),
    re.compile(r"\blead\b", re.I),
    re.compile(r"\bstaff\b", re.I),
    re.compile(r"\bprincipal\b", re.I),
    re.compile(r"\bmanager\b", re.I),
)
_ESCALATION_TITLE_HIT = 55
_ESCALATION_DESC_HIT = 28
_ESCALATION_PENALTY_CAP = 150

_STACK_NOISE_TERMS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bios\b", re.I),
    re.compile(r"\breact\b", re.I),
    re.compile(r"\brails\b|ruby\s+on\s+rails", re.I),
    re.compile(r"\bdevops\b", re.I),
)
_STACK_NOISE_TITLE = 62
_STACK_NOISE_DESC = 30
_STACK_NOISE_CAP = 140

# When the user searches "backend", down-rank obvious frontend / mobile / platform roles.
_BACKEND_MISMATCH: tuple[re.Pattern[str], ...] = (
    re.compile(r"\breact\b", re.I),
    re.compile(r"\bvue\.?js\b|\bvue\b", re.I),
    re.compile(r"\bangular\b", re.I),
    re.compile(r"\bsvelte\b", re.I),
    re.compile(r"\bnext\.?js\b|\bnuxt\b", re.I),
    re.compile(r"\bfrontend\b|front[\s-]end", re.I),
    re.compile(r"\bios\b|\bswift\b", re.I),
    re.compile(r"\bandroid\b|\bkotlin\b", re.I),
    re.compile(r"\bflutter\b|\breact\s+native\b", re.I),
    re.compile(r"\bmobile\b", re.I),
    re.compile(r"\brails\b|ruby\s+on\s+rails", re.I),
    re.compile(r"\bdevops\b|\bsre\b", re.I),
    re.compile(r"\bkubernetes\b|\bk8s\b", re.I),
    re.compile(r"\bterraform\b|\bansible\b|\bjenkins\b", re.I),
)
_BACKEND_MISMATCH_PENALTY = 95

# Obvious non-tech roles to drop (title or description).
_BLOCK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bsales\b", re.I),
    re.compile(r"\bcopywriter\b", re.I),
    re.compile(r"\bwriter\b", re.I),
    re.compile(r"\bmarketing\b", re.I),
    re.compile(r"customer\s+support", re.I),
)

# Hard drop: match against job title only (case-insensitive).
_TITLE_HARD_EXCLUDE: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"office\s+assistant", re.I), "hard_title:office_assistant"),
    (re.compile(r"online\s+data\s+analyst", re.I), "hard_title:online_data_analyst"),
    (re.compile(r"data\s+analyst", re.I), "hard_title:data_analyst"),
    (re.compile(r"\bios\b", re.I), "hard_title:ios"),
    (re.compile(r"\bdevops\b", re.I), "hard_title:devops"),
    (re.compile(r"\bsales\b", re.I), "hard_title:sales"),
    (re.compile(r"\bwriter\b", re.I), "hard_title:writer"),
    (re.compile(r"\bcopywriter\b", re.I), "hard_title:copywriter"),
    (re.compile(r"\bmarketing\b", re.I), "hard_title:marketing"),
    (re.compile(r"customer\s+support", re.I), "hard_title:customer_support"),
    (re.compile(r"product\s+manager", re.I), "hard_title:product_manager"),
    (re.compile(r"\bdesigner\b", re.I), "hard_title:designer"),
    (re.compile(r"\brecruiter\b", re.I), "hard_title:recruiter"),
    (re.compile(r"\bvirtual\s+assistant\b", re.I), "hard_title:virtual_assistant"),
    (re.compile(r"\bva\b", re.I), "hard_title:va"),
)

# Remotive category / job URL must not contain these segments (lowercased haystack).
_BAD_CATEGORY_OR_URL_FRAGMENTS: tuple[str, ...] = (
    "marketing",
    "sales",
    "writing",
    "all-others",
    "customer-support",
)

# If keyword contains "developer", title must look like a software role (not only description).
_DEV_TITLE_ROLE_RE = re.compile(
    r"\b(developer|engineer|programmer)\b|"
    r"\bsoftware\s+(engineer|developer)\b|"
    r"\bbackend\b|"
    r"\bfull[\s-]?stack\b|"
    r"\bdjango\b|\bflask\b|\bfastapi\b|\bpython\b",
    re.I,
)

# "Python developer" searches: title-only gate (no description-only matches).
_PYTHON_DEV_STRONG_TITLE_RE = re.compile(
    r"\bpython\b|"
    r"\bbackend\b|back\s*[- ]end|"
    r"\bapi\b|"
    r"\bdjango\b|\bflask\b|\bfastapi\b|"
    r"\bdeveloper\b|"
    r"\bsoftware\s+engineer\b|"
    r"\bsoftware\s+developer\b",
    re.I,
)

# Generic AI/ML/data titles excluded for Python developer searches.
_PYTHON_DEV_WEAK_TITLE_EXCLUDE: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bai\s+engineer\b", re.I), "python_developer:ai_engineer_title"),
    (re.compile(r"\bml\s+engineer\b", re.I), "python_developer:ml_engineer_title"),
    (
        re.compile(r"\bmachine\s+learning\s+engineer\b", re.I),
        "python_developer:machine_learning_engineer_title",
    ),
    (re.compile(r"\bdata\s+engineer\b", re.I), "python_developer:data_engineer_title"),
    (re.compile(r"\bdata\s+scientist\b", re.I), "python_developer:data_scientist_title"),
)

_PYTHON_KEYWORD_NO_PYTHON_MULT = 0.22
_PYTHON_KEYWORD_EXTRA_PENALTY = 70

_PRIMARY_TITLE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(p for p, _, _ in _PRIMARY_STACK)

_BACKEND_ROLE_ANCHOR_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bdjango\b", re.I),
    re.compile(r"\bflask\b", re.I),
    re.compile(r"\bfastapi\b", re.I),
    re.compile(r"\bpython\b", re.I),
)
_BACKEND_WORD_RE = re.compile(r"\bbackend\b|back\s*[- ]end", re.I)


def _has_backend_role_signal(title: str, plain: str) -> bool:
    blob = f"{title}\n{plain}"
    if _BACKEND_WORD_RE.search(blob):
        return True
    return any(p.search(blob) for p in _BACKEND_ROLE_ANCHOR_PATTERNS)


@dataclass
class Vacancy:
    """One job card shown in Telegram (normalized from Remotive or demo data)."""

    title: str
    company: str
    location: str
    salary: str | None
    link: str
    source: str
    description: str
    match_score: int | None = None
    matched_skills: tuple[str, ...] = ()


def _mock_vacancies() -> list[Vacancy]:
    """Shown when the Remotive API cannot be reached."""
    return _goal_demo_vacancies(
        description=DEMO_API_UNREACHABLE_MESSAGE,
    )


def _goal_demo_vacancies(*, description: str) -> list[Vacancy]:
    """Three goal-aligned sample roles (titles fixed; description depends on context)."""
    return [
        Vacancy(
            title="Junior Python Backend Developer",
            company="Northwind Analytics (demo)",
            location="Remote · Global",
            salary=None,
            link="https://example.com/demo/junior-python-backend",
            source=SOURCE_DEMO,
            description=description,
        ),
        Vacancy(
            title="Python API Developer",
            company="Skyline FinTech (demo)",
            location="Remote",
            salary=None,
            link="https://example.com/demo/python-api",
            source=SOURCE_DEMO,
            description=description,
        ),
        Vacancy(
            title="Telegram Bot Developer",
            company="Pulse Messaging Ltd (demo)",
            location="Remote",
            salary=None,
            link="https://example.com/demo/telegram-bot",
            source=SOURCE_DEMO,
            description=description,
        ),
    ]


def _pad_goal_demoes(needed: int) -> list[Vacancy]:
    if needed <= 0:
        return []
    return _goal_demo_vacancies(description=DEMO_PAD_MESSAGE)[:needed]


def _normalize_salary(raw: object) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text in ("-", "—"):
        return None
    return text


def _plain_text(raw: str) -> str:
    """HTML-free text for matching (full description, not truncated)."""
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _clean_description(raw: str) -> str:
    """Strip HTML, decode entities, normalize whitespace, cap length for Telegram."""
    text = _plain_text(raw)
    if len(text) > DESCRIPTION_MAX_LEN:
        text = text[: DESCRIPTION_MAX_LEN - 1] + "…"
    return text


def _location_label(job: dict) -> str:
    """Human-readable place + remote hint (Remotive feed is remote-only)."""
    region = (job.get("candidate_required_location") or "").strip() or "Location not specified"
    return f"Remote · {region}"


def _filter_remote_only(jobs: list[dict]) -> list[dict]:
    """Keep rows that have a link."""
    return [job for job in jobs if job.get("url")]


def _filter_by_keyword_location(jobs: list[dict], user_location: str) -> list[dict]:
    """
    Prefer jobs whose allowed region text matches the user's saved location.
    If nothing matches, return the full keyword result list (still all remote).
    """
    needle = (user_location or "").strip().lower()
    if not needle:
        return jobs

    # User effectively wants any region — don't hide country-specific remote roles.
    if needle in {"worldwide", "world wide", "global", "anywhere", "remote", "any"}:
        return jobs

    tokens = [t for t in re.split(r"[\s,;/|]+", needle) if len(t) >= 2]
    if not tokens:
        return jobs

    def matches(job: dict) -> bool:
        hay = (job.get("candidate_required_location") or "").lower()
        if "worldwide" in hay or "world wide" in hay:
            return True
        return any(tok in hay for tok in tokens)

    filtered = [j for j in jobs if matches(j)]
    return filtered if filtered else jobs


def _log_title_snip(title: str, max_len: int = 120) -> str:
    t = (title or "").replace("\n", " ").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def _category_url_blob(job: dict) -> str:
    parts = (
        str(job.get("category") or ""),
        str(job.get("job_type") or ""),
        str(job.get("url") or ""),
    )
    return "\n".join(parts).lower()


def _bad_category_or_url_reason(job: dict) -> str | None:
    hay = _category_url_blob(job)
    for frag in _BAD_CATEGORY_OR_URL_FRAGMENTS:
        if frag in hay:
            safe = frag.replace("-", "_")
            return f"category_or_url_contains:{safe}"
    return None


def _hard_title_exclude_reason(title: str) -> str | None:
    for pat, code in _TITLE_HARD_EXCLUDE:
        if pat.search(title):
            return code
    return None


def _keyword_wants_developer(keyword: str) -> bool:
    return bool(re.search(r"\bdeveloper\b", keyword, re.I))


def _is_python_developer_search(keyword: str) -> bool:
    return _keyword_wants_python(keyword) and _keyword_wants_developer(keyword)


def _python_dev_strong_title(title: str) -> bool:
    return bool(_PYTHON_DEV_STRONG_TITLE_RE.search(title))


def _python_dev_weak_title_reason(title: str) -> str | None:
    for pat, code in _PYTHON_DEV_WEAK_TITLE_EXCLUDE:
        if pat.search(title):
            return code
    return None


def _has_important_match_in_title(title: str) -> bool:
    tl = title.lower()
    return any(p.search(tl) for p in _IMPORTANT_PATTERNS)


def _is_blocked(title: str, plain_desc: str) -> bool:
    blob = f"{title}\n{plain_desc}"
    return any(p.search(blob) for p in _BLOCK_PATTERNS)


def _has_important_match(title_lower: str, desc_lower: str) -> bool:
    """True if any core tech keyword appears in the title or description."""
    for pat in _IMPORTANT_PATTERNS:
        if pat.search(title_lower) or pat.search(desc_lower):
            return True
    return False


def _primary_stack_in_title(job: dict) -> bool:
    """True if a high-value Python/backend stack term appears in the title."""
    tl = (job.get("title") or "").lower()
    return any(p.search(tl) for p in _PRIMARY_TITLE_PATTERNS)


def _job_mentions_python(title: str, plain: str) -> bool:
    blob = f"{title}\n{plain}"
    return bool(re.search(r"\bpython\b", blob, re.I))


def _signals_escalation_role(title: str, plain: str) -> bool:
    blob = f"{title}\n{plain}"
    return any(p.search(blob) for p in _ESCALATION_TERMS)


def _stack_noise_penalty(title: str, plain: str) -> int:
    """Penalty sum for iOS / React / Rails / DevOps mentions (title weighted higher)."""
    tl, dl = title.lower(), plain.lower()
    pen = 0
    for pat in _STACK_NOISE_TERMS:
        if pat.search(tl):
            pen += _STACK_NOISE_TITLE
        elif pat.search(dl):
            pen += _STACK_NOISE_DESC
    return min(pen, _STACK_NOISE_CAP)


def _escalation_penalty(title: str, plain: str) -> int:
    tl, dl = title.lower(), plain.lower()
    pen = 0
    for pat in _ESCALATION_TERMS:
        if pat.search(tl):
            pen += _ESCALATION_TITLE_HIT
        elif pat.search(dl):
            pen += _ESCALATION_DESC_HIT
    return min(pen, _ESCALATION_PENALTY_CAP)


def _junior_bonus(title: str, plain: str) -> int:
    for pat in _JUNIOR_FRIENDLY:
        if pat.search(title):
            return _JUNIOR_TITLE_BONUS
    for pat in _JUNIOR_FRIENDLY:
        if pat.search(plain):
            return _JUNIOR_DESC_BONUS
    return 0


def _keyword_wants_python(keyword: str) -> bool:
    return bool(re.search(r"\bpython\b", keyword, re.I))


def _keyword_wants_backend(keyword: str) -> bool:
    return bool(re.search(r"\bbackend\b|back\s*[- ]end", keyword, re.I))


def _backend_mismatch_penalty(title: str, plain: str) -> int:
    blob = f"{title}\n{plain}"
    return _BACKEND_MISMATCH_PENALTY if any(p.search(blob) for p in _BACKEND_MISMATCH) else 0


def _final_relevance_score(job: dict, keyword: str, plain_desc: str) -> int:
    """
    Higher is better. Strong stack terms in the title dominate; junior-friendly roles get a boost;
    senior / off-stack roles are penalized (but never hard-dropped here).
    """
    title = str(job.get("title") or "")
    tl = title.lower()
    dl = plain_desc.lower()
    kw = (keyword or "").strip().lower()

    score = 0
    for pat, tp, dp in _PRIMARY_STACK:
        if pat.search(tl):
            score += tp
        elif pat.search(dl):
            score += dp

    secondary = 0
    for pat, tp, dp in _SECONDARY_GENERIC:
        if pat.search(tl):
            secondary += tp
        elif pat.search(dl):
            secondary += dp
    score += min(secondary, _SECONDARY_GENERIC_CAP)

    score += _junior_bonus(title, plain_desc)

    if kw.strip() and kw.strip() in tl:
        score += 22

    score -= _escalation_penalty(title, plain_desc)
    score -= _stack_noise_penalty(title, plain_desc)

    if _keyword_wants_python(kw):
        if not _job_mentions_python(title, plain_desc):
            score = int(score * _PYTHON_KEYWORD_NO_PYTHON_MULT) - _PYTHON_KEYWORD_EXTRA_PENALTY

    if _keyword_wants_backend(kw):
        if not _has_backend_role_signal(title, plain_desc):
            score -= _backend_mismatch_penalty(title, plain_desc)

    return max(0, score)


def _sort_key(pair: tuple[dict, int]) -> tuple[int, str]:
    job, sc = pair
    return (-sc, (job.get("title") or "").lower())


def _defer_escalation_top(
    scored: list[tuple[dict, int]],
    *,
    limit: int,
) -> list[tuple[dict, int]]:
    """
    Prefer roles without Senior/Lead/Staff/Principal/Manager signals until slots are filled,
    then backfill from the rest (still sorted by score within each group).
    """
    ordered = sorted(scored, key=_sort_key)
    plain_cache: dict[int, str] = {}

    def plain_for(j: dict) -> str:
        jid = id(j)
        if jid not in plain_cache:
            plain_cache[jid] = _plain_text(str(j.get("description") or ""))
        return plain_cache[jid]

    non_esc = [
        p
        for p in ordered
        if not _signals_escalation_role(str(p[0].get("title") or ""), plain_for(p[0]))
    ]
    esc = [
        p
        for p in ordered
        if _signals_escalation_role(str(p[0].get("title") or ""), plain_for(p[0]))
    ]
    out = non_esc[:limit]
    if len(out) < limit:
        out.extend(esc[: limit - len(out)])
    return out


def _rank_jobs(jobs: list[dict], keyword: str) -> list[tuple[dict, int]]:
    """Return up to MAX_MATCHES (job, final_score) pairs, best-first, with strict filters."""
    kw = (keyword or "").strip()
    scored: list[tuple[dict, int]] = []
    for job in jobs:
        raw_desc = str(job.get("description") or "")
        plain = _plain_text(raw_desc)
        title_str = str(job.get("title") or "")

        if r := _hard_title_exclude_reason(title_str):
            logger.info(
                "Remotive excluded | title=%s | reason=%s",
                _log_title_snip(title_str),
                r,
            )
            continue
        if r := _bad_category_or_url_reason(job):
            logger.info(
                "Remotive excluded | title=%s | reason=%s",
                _log_title_snip(title_str),
                r,
            )
            continue

        if _is_python_developer_search(kw):
            if r := _python_dev_weak_title_reason(title_str):
                logger.info(
                    "Remotive excluded | title=%s | reason=%s",
                    _log_title_snip(title_str),
                    r,
                )
                continue
            if not _python_dev_strong_title(title_str):
                logger.info(
                    "Remotive excluded | title=%s | reason=%s",
                    _log_title_snip(title_str),
                    "python_developer:title_missing_strong_stack_terms",
                )
                continue
            if not _has_important_match_in_title(title_str):
                logger.info(
                    "Remotive excluded | title=%s | reason=%s",
                    _log_title_snip(title_str),
                    "python_developer:no_title_tech_match",
                )
                continue
        else:
            if _keyword_wants_python(kw) and not _job_mentions_python(title_str, plain):
                logger.info(
                    "Remotive excluded | title=%s | reason=%s",
                    _log_title_snip(title_str),
                    "keyword_requires_python_in_title_or_description",
                )
                continue
            if _keyword_wants_developer(kw) and not _DEV_TITLE_ROLE_RE.search(title_str):
                logger.info(
                    "Remotive excluded | title=%s | reason=%s",
                    _log_title_snip(title_str),
                    "developer_keyword:title_missing_dev_role_terms",
                )
                continue
            title_lower = title_str.lower()
            desc_lower = plain.lower()
            if not _has_important_match(title_lower, desc_lower):
                logger.info(
                    "Remotive excluded | title=%s | reason=%s",
                    _log_title_snip(title_str),
                    "no_important_tech_match",
                )
                continue

        if _is_blocked(title_str, plain):
            logger.info(
                "Remotive excluded | title=%s | reason=%s",
                _log_title_snip(title_str),
                "blocked_role_keywords_in_title_or_description",
            )
            continue

        score = _final_relevance_score(job, keyword, plain)
        if _is_python_developer_search(kw) and score < PYTHON_DEVELOPER_MIN_SCORE:
            logger.info(
                "Remotive excluded | title=%s | reason=%s",
                _log_title_snip(title_str),
                f"below_min_score_python_developer_search(score={score},min={PYTHON_DEVELOPER_MIN_SCORE})",
            )
            continue

        scored.append((job, score))

    scored.sort(key=_sort_key)

    if _is_python_developer_search(kw):
        # Title gate already applied; do not admit description-only weak titles.
        pool = scored
    else:
        primary_title_hits = [pair for pair in scored if _primary_stack_in_title(pair[0])]
        pool = primary_title_hits if primary_title_hits else scored

    return _defer_escalation_top(pool, limit=MAX_MATCHES)


def _job_to_vacancy(job: dict) -> Vacancy:
    title = str(job.get("title") or "Untitled role")
    company = str(job.get("company_name") or "Unknown company")
    desc = _clean_description(str(job.get("description") or ""))
    return Vacancy(
        title=title,
        company=company,
        location=_location_label(job),
        salary=_normalize_salary(job.get("salary")),
        link=str(job.get("url") or ""),
        source=SOURCE_REMOTIVE,
        description=desc,
    )


class RemotiveAPI:
    """
    Fetches remote jobs from Remotive's public JSON API.

    Docs: https://remotive.com/api-documentation
    """

    async def search_jobs(
        self,
        keyword: str,
        location: str,
        work_type: str = "Any",
    ) -> list[Vacancy]:
        """
        Search by keyword (user preference). Results are remote-only.

        If the HTTP request fails, returns demo vacancies.
        For "Python developer" searches: if no real jobs pass filters, returns exactly three
        demo listings (no partial padding). Other keywords may pad up to three with demos.

        work_type is accepted for compatibility with saved preferences; the public
        Remotive endpoint does not filter by it yet.
        """
        _ = work_type  # reserved for a future filter when we map prefs → Remotive categories
        kw = (keyword or "software").strip()

        try:
            params = {"search": kw}
            async with httpx.AsyncClient(timeout=REMOTIVE_HTTP_TIMEOUT_SECONDS) as client:
                resp = await client.get(REMOTIVE_API_URL, params=params)
            if resp.status_code != 200:
                logger.warning(
                    "Remotive API returned status %s; using demo listings",
                    resp.status_code,
                )
                return list(_mock_vacancies())
            data = resp.json()
        except Exception as exc:
            logger.warning("Remotive API request failed; using demo listings: %s", exc)
            return list(_mock_vacancies())

        api_jobs: list[dict] = data.get("jobs") or []
        logger.info("Remotive: fetched %d jobs from API", len(api_jobs))

        raw_jobs = _filter_remote_only(api_jobs)
        raw_jobs = _filter_by_keyword_location(raw_jobs, location)

        ranked = _rank_jobs(raw_jobs, kw)
        logger.info("Remotive: %d jobs selected after strict filtering", len(ranked))

        if _is_python_developer_search(kw) and not ranked:
            logger.info(
                "Remotive: no real jobs for Python developer search; returning 3 demo listings",
            )
            demos = list(_pad_goal_demoes(MIN_JOB_RESULTS_SOFT))
            for demo in demos:
                logger.info(
                    "Remotive selected (demo_only) | title=%s | note=%s",
                    _log_title_snip(demo.title),
                    "python_developer_no_matching_real_jobs",
                )
            return demos

        vacancies: list[Vacancy] = []
        for job, score in ranked:
            logger.info(
                "Remotive selected | score=%s | title=%s",
                score,
                _log_title_snip(str(job.get("title") or "")),
            )
            vacancies.append(_job_to_vacancy(job))

        if not _is_python_developer_search(kw) and len(vacancies) < MIN_JOB_RESULTS_SOFT:
            need = MIN_JOB_RESULTS_SOFT - len(vacancies)
            for pad in _pad_goal_demoes(need):
                logger.info(
                    "Remotive selected (demo_pad) | title=%s | note=%s",
                    _log_title_snip(pad.title),
                    "demo_slot_no_matching_real_job",
                )
                vacancies.append(pad)

        return vacancies
