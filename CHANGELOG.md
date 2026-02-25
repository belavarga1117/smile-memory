# Changelog

All notable changes to **Smile Memory** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-02-25

### Added
- Rose-bézsz luxury color palette (replaced brown/earth-tone theme)
- `brand-blush` color token for hero sections (#EDCFCC)
- Gallery lightbox with Alpine.js (click-to-zoom, arrow navigation, keyboard support)
- Automated daily tour sync via Celery Beat (15:00 ICT, all 3 API sources)
- `sync_all_tours` Celery task in `apps/importer/tasks.py`
- Blog post markdown rendering with `|markdown` template filter
- `@tailwindcss/typography` plugin for prose content styling
- Destination ordering by tour count on homepage
- "All Tours" card with airplane image on homepage destinations grid
- SVG trust badge icons (replaced emoji)

### Changed
- Full color palette: cocoa→dark mauve, rose→dusty rose, clay→deep rose, taupe→rosewood, gold→rose gold
- Hero sections use `bg-brand-blush` (was hardcoded `#fdb0aa`)
- Footer background: `bg-brand-text` (dark charcoal-rose)
- Navbar background: dark mauve (#6B4F54)
- Removed category filter from tours page (unused by API scrapers)

### Fixed
- HTML tags in hotel names from Zego API (861 records cleaned, star counts extracted)
- Blog headings not rendering due to Tailwind v4 preflight specificity issue
- N+1 query on homepage destination tour counts (annotated queryset)

## [1.2.0] - 2026-02-25

### Added
- API-based tour scrapers for three wholesalers:
  - **Go365 Travel**: CryptoJS AES-encrypted AJAX API client (274 tours)
  - **Real Journey**: TourProX WordPress AJAX API client (23 tours)
  - **Zego Travel**: Portal internal API client with session auth (239 tours)
- `scrape_tours` management command with --source, --country, --url, --dry-run options
- BaseScraper framework with rate limiting, retry logic, and cookie support
- Full pricing matrix import (adult/child/infant/promo/join-land/deposit/commission)
- Departure date sync with availability status and seat tracking
- ImportJob logging for every scrape run

### Changed
- Go365 scraper rewritten from HTML parsing to encrypted AJAX API (17 → 274 tours)
- Real Journey scraper rewritten from HTML parsing to AJAX API (730 → 316 lines)

## [1.1.0] - 2026-02-25

### Added
- Image optimization with `{% thumbnail %}` template tag (auto-resize via Pillow)
- Lazy loading on all tour card and blog images
- Responsive image sizing per context (cards: 400px, hero: 1200px, gallery: 800px)

### Changed
- Updated all templates to use optimized thumbnail URLs
- Seed data updated with proper image dimensions

## [1.0.0] - 2026-02-24

### Added
- Comprehensive test suite: 193 tests, 84% code coverage (Phase 9)
- pytest-cov integration with HTML coverage reports
- CI coverage reporting with artifact upload
- Missing `inquiry_success.html` template for booking confirmation flow

### Fixed
- CI build: added `libcairo2-dev` system dependency for xhtml2pdf/pycairo

## [0.9.0] - 2026-02-23

### Added
- Django 5.1 project with split settings (base/development/production)
- Custom User model (accounts app)
- Tour catalog: Tour, Destination, Category, Airline, TourDeparture, TourFlight, TourImage, ItineraryDay, PriceOption models
- Tour list view with filtering (destination, category, price, duration), search, and sorting
- Tour detail view with hero, itinerary accordion, gallery, pricing sidebar, related tours
- DRF API: TourViewSet, DestinationViewSet, CategoryViewSet (read-only)
- Homepage with hero carousel (Alpine.js), trust badges, featured tours, testimonials, FAQ accordion
- About, Contact, Payment Info pages
- Blog with categories, tags, search, pagination
- SEO: sitemap.xml, robots.txt, Open Graph meta tags
- Booking system: admin-approved inquiry workflow (NEW → CONTACTED → CONFIRMED/REJECTED)
- Customer CRM: email, phone, LINE ID, marketing opt-in, tags, segmentation
- Email notification system (inquiry confirmation, admin alerts, booking status)
- Marketing engine: newsletter campaigns, email templates, subscriber management
- PDPA/GDPR compliant unsubscribe flow
- Bilingual support: Thai + English with i18n_patterns URL routing
- Language switcher in navbar (desktop + mobile)
- 150+ Thai translations in .po files
- Import pipeline: Excel (openpyxl), CSV, PDF (pdfplumber), HTML (BeautifulSoup) parsers
- TourMapper with 20+ auto-detected column patterns (EN + Thai)
- Admin dashboard with Chart.js: KPI cards, inquiry charts, recent activity tables
- Tour PDF export (xhtml2pdf, A4 layout)
- Custom error pages (400, 403, 404, 500)
- Performance optimization: select_related/prefetch_related across all views
- Security hardening: SSL redirect, HSTS, secure cookies, CSRF, X-Frame-Options
- Tailwind CSS v4 design system (navy/aqua/gold palette)
- Responsive layout (mobile + tablet + desktop)
- LINE chat floating button
- Docker-compose configuration (PostgreSQL + Redis)
- Railway deployment config (Procfile, railway.toml, Dockerfile)
- GitHub Actions CI: ruff lint + pytest
- Seed data command: 8 airlines, 10 destinations, 7 categories, 10 tours

[1.3.0]: https://github.com/belavarga1117/smile-memory/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/belavarga1117/smile-memory/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/belavarga1117/smile-memory/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/belavarga1117/smile-memory/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/belavarga1117/smile-memory/releases/tag/v0.9.0
