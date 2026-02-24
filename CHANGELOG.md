# Changelog

All notable changes to **Smile Memory** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.0.0]: https://github.com/belavarga1117/smile-memory/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/belavarga1117/smile-memory/releases/tag/v0.9.0
