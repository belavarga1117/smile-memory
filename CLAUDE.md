# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Smile Memory** — Thai travel agency website. Resells tour packages from wholesalers (Zego Travel, GS25 Travel, Go365 Travel). Bilingual (Thai + English), responsive (mobile + desktop), professional quality.

**NOT e-commerce** — customers submit inquiries, admin confirms bookings, then automated emails are sent. No online payments.

## Tech Stack

- **Backend**: Django 5.1 + Django REST Framework
- **Frontend**: Django Templates + Tailwind CSS v4 + Alpine.js
- **Database**: SQLite (dev) / PostgreSQL 16 (prod)
- **Task Queue**: Celery + Redis
- **Search**: PostgreSQL Full-Text Search
- **Hosting**: Railway (nixpacks, git push = auto-deploy)
- **Static Files**: WhiteNoise `CompressedStaticFilesStorage` (prod)
- **Email**: Brevo REST API (transactional) + Brevo bulk (campaigns) — `apps/core/email_backends.BrevoEmailBackend`
- **CI/CD**: GitHub Actions
- **Production URL**: https://web-production-86e1f.up.railway.app

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run development server
python manage.py runserver

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test
pytest                              # with pytest-django

# Run single app tests
python manage.py test apps.tours
pytest apps/tours/tests/

# Lint
ruff check .
ruff check --fix .

# Format
ruff format .

# Tailwind CSS
npm run css:watch                   # development (auto-rebuild)
npm run css:build                   # production (minified)

# Celery worker (requires Redis)
celery -A config worker -l info

# Celery beat (scheduled tasks)
celery -A config beat -l info

# Django system check
python manage.py check
python manage.py check --deploy     # production checklist

# Collect static files (production)
python manage.py collectstatic --noinput

# Generate translation files
python manage.py makemessages -l th
python manage.py compilemessages

# QA pipeline (all checks: lint, format, Django check, tests, coverage)
./scripts/qa.sh
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
│   └── qa.sh                  # QA pipeline (lint + test + coverage)
├── locale/{th,en}/            # Translation .po files
├── requirements/{base,dev,prod}.txt
├── docker-compose.yml         # PostgreSQL + Redis (when Docker available)
├── nixpacks.toml              # Nixpacks build config (Python + libcairo2-dev)
├── Procfile                   # Railway process definitions
├── railway.toml               # Railway deploy config (build + start commands)
└── Dockerfile.local           # Local Docker build (not used by Railway)
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
1. **Zego API** — portal internal API with session auth (239 tours)
2. **Go365 API** — encrypted AJAX API with CryptoJS AES (274 tours)
3. **Real Journey API** — TourProX WordPress AJAX (23 tours)
4. **Excel upload** — admin exports from portal, uploads in admin
5. **PDF upload** — parsed with pdfplumber
6. **Manual entry** — Django admin CRUD

Pipeline: `Trigger → Parser → Field Mapper → Validator → Upsert Tour → Log`

**Automated sync**: Celery Beat runs `sync_all_tours` daily at 15:00 ICT — imports from all 3 API sources.

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

- Dev settings: `config.settings.development` (SQLite, console email, DEBUG=True)
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
2. Activate venv: `source venv/bin/activate`
3. Start Tailwind watcher: `npm run css:watch` (separate terminal)
4. Run dev server: `python manage.py runserver`
5. Admin panel: http://localhost:8000/admin/
6. After model changes: `python manage.py makemigrations && python manage.py migrate`
7. Before commit: `./scripts/qa.sh` (or at minimum: `ruff check . && ruff format .`)
8. Push branch & create PR: `git push -u origin feat/my-feature && gh pr create`
9. Wait for CI + review Railway preview URL
10. Merge PR → auto-deploy to production

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
