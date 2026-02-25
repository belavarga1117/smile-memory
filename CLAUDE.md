# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Smile Memory** — Thai travel agency website. Resells tour packages from wholesalers (Zego Travel, GS25 Travel, Go365 Travel). Bilingual (Thai + English), responsive (mobile + desktop), professional quality.

**NOT e-commerce** — customers submit inquiries, admin confirms bookings, then automated emails are sent. No online payments.

## Tech Stack

- **Backend**: Django 5.1 + Django REST Framework
- **Frontend**: Django Templates + Tailwind CSS v4 + Alpine.js
- **Database**: PostgreSQL 16 (dev + prod) — Homebrew local / Railway prod
- **Task Queue**: Celery + Redis
- **Search**: PostgreSQL Full-Text Search
- **Hosting**: Railway (nixpacks, git push = auto-deploy)
- **Static Files**: WhiteNoise `CompressedStaticFilesStorage` (prod)
- **Email**: Brevo REST API (transactional) + Brevo bulk (campaigns) — `apps/core/email_backends.BrevoEmailBackend`
- **CI/CD**: GitHub Actions
- **Production URL**: https://web-production-86e1f.up.railway.app

## Common Commands

```bash
# ── Local dev stack (PostgreSQL + Redis + Celery + Django + Tailwind) ──────────
./scripts/dev.sh                    # start everything in one command
./scripts/dev.sh --no-css           # skip Tailwind watch (when not changing styles)

# ── Individual services (manual) ──────────────────────────────────────────────
source venv/bin/activate
brew services start postgresql@16   # start PostgreSQL (auto-starts at login)
brew services start redis           # start Redis (auto-starts at login)
python manage.py runserver          # Django dev server only
celery -A config worker -l info     # Celery worker (needs Redis)
celery -A config beat -l info       # Celery beat scheduler
npm run css:watch                   # Tailwind CSS watch
npm run css:build                   # Tailwind CSS production build

# ── Database ───────────────────────────────────────────────────────────────────
python manage.py makemigrations
python manage.py migrate
python manage.py seed_tours         # seed 10 tours + fixtures
python manage.py createsuperuser

# ── Tests ──────────────────────────────────────────────────────────────────────
pytest                              # full suite (272 tests, PostgreSQL)
pytest -x -q                        # stop on first failure, quiet

# ── Code quality ───────────────────────────────────────────────────────────────
ruff check .
ruff check --fix .
ruff format .
./scripts/qa.sh                     # full QA pipeline (lint + test + coverage)

# ── Django checks ──────────────────────────────────────────────────────────────
python manage.py check
python manage.py check --deploy     # production checklist

# ── Static files (production only) ────────────────────────────────────────────
python manage.py collectstatic --noinput

# ── Translations ───────────────────────────────────────────────────────────────
python manage.py makemessages -l th
python manage.py compilemessages
```

## Project Structure

```
travel-agency/
├── config/                     # Django project config
│   ├── settings/
│   │   ├── base.py            # Shared settings (all envs)
│   │   ├── development.py     # Dev: DEBUG=True, SQLite, console email
│   │   └── production.py      # Prod: Railway, WhiteNoise, Brevo, Sentry
│   ├── celery.py              # Celery app init
│   ├── urls.py                # Root URL routing
│   └── wsgi.py / asgi.py
├── apps/
│   ├── core/                  # Shared base models, template tags, utils
│   ├── accounts/              # Custom User model, admin auth
│   ├── tours/                 # Tour catalog (central domain)
│   ├── bookings/              # Inquiry system (admin-approved workflow)
│   ├── customers/             # Customer CRM, opt-in, segmentation
│   ├── marketing/             # Newsletter, email campaigns
│   ├── importer/              # Tour data import pipeline
│   │   ├── parsers/           # Excel, PDF, scrape parsers
│   │   ├── mappers/           # Field mapping per wholesaler
│   │   └── pipeline.py        # Import orchestrator
│   ├── pages/                 # Static pages (home, about, contact)
│   └── blog/                  # Blog / Travel Tips (SEO)
├── templates/
│   ├── base.html              # Master template (rose-bézsz luxury design)
│   ├── components/            # _navbar.html, _footer.html, etc.
│   └── emails/                # Email templates
├── static/
│   ├── src/input.css          # Tailwind v4 entry point
│   ├── css/output.css         # Compiled (committed for prod)
│   ├── images/                # Static images (about-team.jpg)
│   └── media/                 # Seed data images (heroes, testimonials, destinations, blog)
├── tests/                      # Integration + cross-app tests (factory-boy)
│   ├── factories.py           # 25 factory-boy factories
│   ├── conftest → root conftest.py (shared fixtures)
│   └── test_*.py              # API, security, performance, etc.
├── scripts/
│   ├── dev.sh                 # Local full-stack launcher (PG + Redis + Celery + Django + Tailwind)
│   └── qa.sh                  # QA pipeline (lint + test + coverage)
├── locale/{th,en}/            # Translation .po files
├── requirements/{base,dev,prod}.txt
├── nixpacks.toml              # Nixpacks build config (Python + libcairo2-dev)
├── Procfile                   # Railway process definitions
└── railway.toml               # Railway deploy config (build + start commands)
```

## Architecture

### Django Apps (9)

| App | Purpose | Key Models |
|-----|---------|------------|
| `core` | Base classes, template tags, context processors | `TimeStampedModel` (abstract), `SiteConfiguration` (singleton) |
| `accounts` | Auth, custom user | `User` (extends AbstractUser) |
| `tours` | Tour catalog, search, filtering | `Tour`, `Destination`, `Category`, `Airline`, `TourDeparture`, `TourFlight`, `TourImage`, `ItineraryDay`, `PriceOption` |
| `bookings` | Inquiry workflow (admin-approved) | `Inquiry`, `InquiryNote` |
| `customers` | Customer database, marketing opt-in | `Customer` (email, phone, tags, opt-in) |
| `marketing` | Newsletters, campaigns | `Campaign`, `EmailTemplate`, `CampaignRecipient` |
| `importer` | Tour data import | `ImportSource`, `ImportJob`, `ImportLog` |
| `pages` | Homepage, about, contact | `HeroSlide`, `Testimonial`, `TrustBadge`, `FAQ` |
| `blog` | Travel blog | `BlogPost`, `BlogCategory`, `Tag` |

### Booking Workflow (Key Business Logic)

```
Customer submits inquiry form (+ marketing opt-in checkbox)
  → Inquiry created (status: NEW)
  → Customer record created/updated
  → Immediate email to customer: "Thank you, we'll respond soon"
  → Immediate email to admin: "New inquiry received"
  → Admin reviews in admin panel
  → Admin CONFIRMS → auto email: booking confirmation + payment info
  → OR Admin REJECTS → optional email: unavailable / alternative suggestion
```

### Import Pipeline

Wholesalers (Zego, GS25, Go365) are login-gated portals. Zego has REST API (v1.5) at zegoapi.com.

**Zego API → Django Model Mapping:**
- `ProgramTour` → `Tour` (title, product_code, locations, hotel_stars, meals, includes/excludes)
- `Period` → `TourDeparture` (departure_date, full pricing matrix: adult/child/infant/visa/room supplements, deposit, commission, promo pricing)
- `Flights` → `TourFlight` (airline, flight_number, route, times)
- `Itinerarys` → `ItineraryDay` (day_number, meals B/L/D with Y/N/P/C flags, hotel info)

Supported import methods:
1. **Zego API** — portal internal API with session auth (239+ tours, full itinerary + PDF)
2. **Go365 API** — encrypted AJAX API with CryptoJS AES (275 tours, PDF fixed)
3. **Real Journey API** — TourProX WordPress AJAX (23 tours)
4. **GS25 HTML scraper** — session auth, BeautifulSoup, ~87 tours in prod (production only, not run locally)
5. **Excel upload** — admin exports from portal, uploads in admin
6. **PDF upload** — parsed with pdfplumber
7. **Manual entry** — Django admin CRUD

Pipeline: `Trigger → Parser → Field Mapper → Validator → Upsert Tour → Log`

**Automated sync**: Celery Beat runs `sync_all_tours` daily at 15:00 ICT — imports from all 4 sources (Zego, Go365, Real Journey, GS25).

**Data validation**: `python manage.py validate_scrapers` — samples tours from DB, re-fetches live, compares title/duration/price/departures/PDF. Use `--source` and `--sample` flags.

### Bilingual Strategy (Thai + English)

- **Static UI strings**: Django `{% trans %}` + `.po` files
- **Dynamic content**: Dual fields on models (`title` + `title_th`)
- **Template tag**: `{% trans_field tour "title" %}` — returns Thai or English based on active language
- **URL routing**: `i18n_patterns` → `/en/tours/`, `/th/tours/`

### Design System

- **Colors**: Rose-bézsz luxury palette — brand-cocoa (#6B4F54, dark mauve nav), brand-rose (#B25E68, dusty rose CTA), brand-clay (#964D57, deep rose hover), brand-blush (#EDCFCC, soft mauve-blush hero sections), brand-bg (#F3EAE6, blush cream background), brand-surface (#FDF9F7, near-white cards), brand-taupe (#C4ADA8, rosewood borders), brand-text (#3A2D31, charcoal-rose), brand-muted (#756469, rose-gray), brand-hint (#A08E93, light rose-gray), brand-gold (#D4A494, rose gold accent). On dark backgrounds use text-white/70 or text-white/60 instead of brand-hint.
- **Fonts**: Inter (Latin) + Noto Sans Thai — loaded from Google Fonts
- **Layout**: Mobile-first responsive with Tailwind CSS
- **Components**: Alpine.js for interactivity (dropdowns, modals, form handling)

## Settings

- Dev settings: `config.settings.development` (PostgreSQL via DATABASE_URL, console email, DEBUG=True)
- Prod settings: `config.settings.production` (PostgreSQL, Brevo REST API, WhiteNoise, Sentry, logging to stdout)
- Settings module controlled by `DJANGO_SETTINGS_MODULE` env var
- All secrets in `.env` file (never committed)

## Deployment (Railway)

- **Project**: perpetual-vibrancy | **Service**: web | **DB**: PostgreSQL
- **Builder**: nixpacks (Python provider) — auto-deploy on git push to main
- **Build**: `collectstatic` | **Start**: `migrate && gunicorn`
- **Static**: WhiteNoise serves from `staticfiles/`, seed images in `static/media/`
- **Media**: Ephemeral filesystem — seed images committed as static, tour images are external URLs
- **Admin**: https://web-production-86e1f.up.railway.app/admin/ (credentials in .env / Railway variables)
- **Railway CLI**: `railway logs`, `railway variables`, `railway status`
- **Key env vars**: DJANGO_SETTINGS_MODULE, SECRET_KEY, DATABASE_URL, ALLOWED_HOSTS, PIP_ONLY_BINARY=pycairo

## Conventions

- All apps in `apps/` directory, referenced as `apps.tours`, `apps.bookings`, etc.
- All models inherit from `core.TimeStampedModel` (provides `created_at`, `updated_at`)
- Bilingual fields use `_th` suffix: `title` (English) + `title_th` (Thai)
- Custom User model: `apps.accounts.User` (`AUTH_USER_MODEL = "accounts.User"`)
- Template partials prefixed with underscore: `_tour_card.html`, `_navbar.html`
- Admin credentials: stored in `.env` (dev) and Railway variables (prod) — never commit to repo
- Seed images served from `static/media/` via `thumbnail` tag fallback (ephemeral media/ on Railway)

## Development Workflow

### Branch Strategy (GitHub Flow)

- **`main`** = production (protected, auto-deploys to Railway)
- **Feature branches** (`feat/...`, `fix/...`, `refactor/...`) for all work
- **Pull Requests** required to merge into `main` — CI must pass
- **Railway PR Previews** — each PR gets a temporary preview URL for testing
- **NEVER push directly to `main`** — always create a PR

### Workflow Steps

1. Create feature branch: `git checkout -b feat/my-feature`
2. Start local dev stack: `./scripts/dev.sh` — starts PostgreSQL + Redis + Celery + Django + Tailwind
3. Admin panel: http://localhost:8000/admin/ (admin / admin123)
4. After model changes: `python manage.py makemigrations && python manage.py migrate`
5. Write + run tests locally: `pytest -x -q` — catches real PostgreSQL errors before deploy
6. Before commit: `./scripts/qa.sh` (or at minimum: `ruff check . && ruff format .`)
7. Push branch & create PR: `git push -u origin feat/my-feature && gh pr create`
8. **Only push when feature is ready** — every push = Railway deploy (~10 min); iterate locally
9. Merge PR → auto-deploy to production

### Local vs Production Split

| What | Local (Homebrew PG) | Production (Railway) |
|---|---|---|
| Admin, templates, forms | ✅ Full testing | ✅ Final verify |
| PostgreSQL migrations | ✅ Real behavior | ✅ Apply on deploy |
| Celery tasks | ✅ Test logic | ✅ Real workers |
| **Scrapers** | ❌ No real data | ✅ 537+ tours, run here |
| **Wholesaler API calls** | ❌ Local only | ✅ Production only |

**Rule**: Scrapers (scrape_tours, validate_scrapers) ONLY run on production via Celery worker or admin panel. Local has only seed data (10 tours).

### Branch Naming

- `feat/...` — new features
- `fix/...` — bug fixes
- `refactor/...` — code refactoring
- `docs/...` — documentation changes
- `chore/...` — maintenance, dependencies

## API Endpoints

- **Tours list**: `GET /api/v1/tours/` (filterable: destination, category, status, min/max price, search)
- **Tour detail**: `GET /api/v1/tours/{id}/` (includes departures, flights, itinerary, images)
- **Destinations**: `GET /api/v1/destinations/`
- **Categories**: `GET /api/v1/categories/`
- **Tour pages**: `/tours/` (list), `/tours/<slug>/` (detail)

## Seed Data

```bash
python manage.py seed_tours    # 8 airlines, 10 destinations, 7 categories, 10 tours with departures + itineraries
```
