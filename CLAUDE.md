# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Smile Memory** — Thai travel agency website. Resells tour packages from wholesalers (Zego, GS25, Go365, Real Journey). Bilingual (Thai + English), responsive, professional quality.

**NOT e-commerce** — customers submit inquiries, admin confirms bookings, then automated emails are sent. No online payments.

## Tech Stack

- **Backend**: Django 5.1 + Django REST Framework
- **Frontend**: Django Templates + Tailwind CSS v4 + Alpine.js
- **Database**: PostgreSQL 16 (Homebrew local / Railway prod)
- **Task Queue**: Celery + Redis | **Search**: PostgreSQL Full-Text Search
- **Hosting**: Railway (nixpacks, git push = auto-deploy)
- **Static**: WhiteNoise `CompressedStaticFilesStorage` | **Email**: Brevo REST API
- **Production**: https://smilememorytravel.com

## NEVER (Critical Rules)

- **NEVER push directly to `main`** — always create a PR; CI must pass first
- **NEVER run GS25 scraper locally** — requires Railway credentials (GS25_USERNAME/PASSWORD)
- **NEVER commit `.env`, credentials, or API keys** to git
- **NEVER use SMTP on Railway** — it's blocked; use `BrevoEmailBackend` (Brevo REST API)
- **NEVER rebuild CSS on Railway** — commit `static/css/output.css` pre-built locally
- **NEVER set `STORAGES` without both `"default"` and `"staticfiles"` keys** (Django 5.1 requirement)
- **NEVER publish a blog post** with visa/entry/health facts without running the fact-check research agent first
- **NEVER guess** when best practice is unclear — spawn the research sub-agent

## Common Commands

```bash
# ── Local dev stack ─────────────────────────────────────────────────────────
./scripts/dev.sh                    # start everything (PG + Redis + Celery + Django + Tailwind)
./scripts/dev.sh --no-css           # skip Tailwind watch

# ── Database ────────────────────────────────────────────────────────────────
python manage.py makemigrations && python manage.py migrate
python manage.py seed_tours         # 10 tours + fixtures for local dev
python manage.py createsuperuser

# ── Tests & QA ──────────────────────────────────────────────────────────────
pytest                              # full suite (~460 tests, PostgreSQL)
pytest -x -q                        # stop on first failure
./scripts/qa.sh                     # full QA pipeline (lint + format + check + test + coverage)

# ── Code quality ────────────────────────────────────────────────────────────
ruff check . && ruff format .
python manage.py check
python manage.py check --deploy     # production checklist

# ── Data quality (production) ───────────────────────────────────────────────
python manage.py clean_tour_html [--source all]   # strip HTML from tour fields
python manage.py clean_tour_titles [--apply]      # strip junk from titles (dry-run default)
python manage.py validate_scrapers [--source zego] [--sample 5]
python manage.py find_duplicates [--fix]

# ── Translations ────────────────────────────────────────────────────────────
python manage.py makemessages -l th && python manage.py compilemessages

# ── Static files (prod only) ────────────────────────────────────────────────
npm run css:build                   # rebuild Tailwind CSS (commit output.css after)
python manage.py collectstatic --noinput
```

## Architecture

### Django Apps (9)

| App | Purpose | Key Models |
|-----|---------|------------|
| `core` | Base classes, template tags, context processors | `TimeStampedModel` (abstract), `SiteConfiguration` (singleton) |
| `accounts` | Auth, custom user | `User` (extends AbstractUser) |
| `tours` | Tour catalog, search, filtering | `Tour`, `Destination`, `Category`, `TourDeparture`, `TourFlight`, `ItineraryDay` |
| `bookings` | Inquiry workflow (admin-approved) | `Inquiry`, `InquiryNote` |
| `customers` | Customer CRM, marketing opt-in | `Customer` |
| `marketing` | Newsletters, campaigns | `Campaign`, `EmailTemplate` |
| `importer` | Tour data import pipeline | `ImportJob`, `ImportLog` |
| `pages` | Homepage, about, contact | `HeroSlide`, `Testimonial`, `FAQ` |
| `blog` | Travel blog | `BlogPost`, `BlogCategory`, `Tag` |

### Booking Workflow

```
Customer inquiry (+ marketing opt-in) → Inquiry (status=NEW)
  → Email to customer: "Thank you"  → Email to admin: "New inquiry"
  → Admin CONFIRMS → email: booking confirmation + payment info
  → Admin REJECTS → optional email: unavailable / suggestion
```

### Import Pipeline

4 wholesalers: **Zego** (246 tours, internal API + session auth), **Go365** (275 tours, CryptoJS encrypted AJAX), **Real Journey** (23 tours, WordPress AJAX — no auth), **GS25** (~90 tours, HTML scraper — production only).

Pipeline: `Trigger → Scraper → Field Mapper → _sanitize_tour_data() → _upsert_tour() → Log`

Automated: Celery Beat runs `sync_all_tours` daily at 15:00 ICT.

**PDF rule**: Tour only published (`status=PUBLISHED`) if `pdf_url` is non-empty.

### Bilingual Strategy

- Static UI strings: `{% trans %}` + `.po` locale files
- Dynamic content: dual model fields (`title` + `title_th`)
- Template tag: `{% trans_field tour "title" %}` — returns field based on active language
- URL routing: `i18n_patterns` → `/en/tours/`, `/th/tours/`

## Design System

Pink luxury palette. **See MEMORY.md for current color hex values** — do NOT use CLAUDE.md
palette (it's outdated). Key: `brand-rose` (CTA), `brand-cocoa` (footer), `brand-bg` (body).
Font: `font-brand` = Playfair Display (headings), `font-sans` = Inter + Noto Sans Thai.
Owner loves pink — NO brown/mauve tones. Layout: mobile-first Tailwind, Alpine.js interactivity.

## Settings & Conventions

- Dev: `config.settings.development` (DEBUG=True, console email) | Prod: `config.settings.production`
- All secrets in `.env` (never committed) — prod secrets in Railway env vars
- All models inherit from `core.TimeStampedModel` (`created_at`, `updated_at`)
- Bilingual: `_th` suffix — `title` (EN) + `title_th` (TH)
- Template partials: underscore prefix (`_tour_card.html`, `_navbar.html`)
- Custom User: `apps.accounts.User` (`AUTH_USER_MODEL = "accounts.User"`)

## Development Workflow

### Branch Strategy (GitHub Flow)

- `main` = production (protected) — **CI must pass, PR required**
- Feature branches: `feat/...`, `fix/...`, `refactor/...`, `docs/...`, `chore/...`
- Every push to main = Railway deploy (~10 min) — iterate locally, push when ready

### Workflow Steps

1. `git checkout -b feat/my-feature`
2. `./scripts/dev.sh` — full dev stack
3. Make changes + `pytest -x -q` locally
4. `./scripts/qa.sh` before committing
5. `git push -u origin feat/my-feature && gh pr create`
6. Merge PR → auto-deploy to production

**Local vs prod**: Zego/Go365/GS25 scrapers need Railway credentials — use production for real data.
**Production DB access**: `DATABASE_URL="$(railway variables --service Postgres --json | python3 -c "import json,sys; print(json.load(sys.stdin)['DATABASE_PUBLIC_URL'])")" python manage.py <command>`

### Multi-Agent Workflow (Automatic)

The parent agent MUST proactively spawn Task sub-agents — user never needs to ask.
Templates: `.claude/commands/{research,review,qa,vendor-research,write-scraper,write-blog}.md`

| When | Agent | Template |
|------|-------|----------|
| Feature >3 files complete | review → then qa | `review.md` → `qa.md` |
| Before creating a PR | review (if not done) | `review.md` |
| Blog post requested | fact-check research FIRST | `write-blog.md` Phase 1 |
| New wholesaler / scraper task | vendor-research BEFORE coding | `vendor-research.md` |
| Approach unclear | research sub-agent | `research.md` |

## API Endpoints

- `GET /api/v1/tours/` — filterable: destination, category, status, min/max price, search
- `GET /api/v1/tours/{id}/` — includes departures, flights, itinerary, images
- `GET /api/v1/destinations/` | `GET /api/v1/categories/`
- Tour pages: `/tours/` (list) | `/tours/<slug>/` (detail) — language-prefixed via i18n

## Seed Data

```bash
python manage.py seed_tours    # 8 airlines, 10 destinations, 7 categories, 10 tours
```
