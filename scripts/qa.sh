#!/usr/bin/env bash
# ──────────────────────────────────────────────────
# Smile Memory — QA Pipeline
# Runs: lint → format check → Django checks → tests + coverage
# Usage: ./scripts/qa.sh
# ──────────────────────────────────────────────────
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

step() {
    echo ""
    echo -e "${YELLOW}━━━ $1 ━━━${NC}"
}

pass() {
    echo -e "${GREEN}✓ $1${NC}"
    PASS=$((PASS + 1))
}

fail() {
    echo -e "${RED}✗ $1${NC}"
    FAIL=$((FAIL + 1))
}

# ── 1. Ruff lint ──
step "1/6  Ruff lint"
if ruff check . --quiet; then
    pass "Ruff lint: no issues"
else
    fail "Ruff lint: issues found"
fi

# ── 2. Ruff format check ──
step "2/6  Ruff format check"
if ruff format --check . --quiet 2>/dev/null; then
    pass "Ruff format: consistent"
else
    fail "Ruff format: inconsistencies found (run: ruff format .)"
fi

# ── 3. Django system check (dev) ──
step "3/6  Django system check"
if python manage.py check --verbosity=0 2>/dev/null; then
    pass "Django check: passed"
else
    fail "Django check: issues found"
fi

# ── 4. Django deploy check (prod settings) ──
step "4/6  Django deploy check (production)"
export DJANGO_SETTINGS_MODULE=config.settings.production
export SECRET_KEY="${SECRET_KEY:-qa-pipeline-secret-key-minimum-fifty-characters-for-django-check-deploy-abcdef}"
export ALLOWED_HOSTS="${ALLOWED_HOSTS:-*}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///db.sqlite3}"

DEPLOY_OUTPUT=$(python manage.py check --deploy 2>&1 || true)
DEPLOY_WARNINGS=$(echo "$DEPLOY_OUTPUT" | grep -c "WARNING" || true)
unset DJANGO_SETTINGS_MODULE  # Reset to dev

if [ "$DEPLOY_WARNINGS" -eq 0 ]; then
    pass "Deploy check: no warnings"
else
    echo "$DEPLOY_OUTPUT" | grep "WARNING" | head -5
    fail "Deploy check: $DEPLOY_WARNINGS warning(s)"
fi

# Reset settings
export DJANGO_SETTINGS_MODULE=config.settings.development

# ── 5. Pytest with coverage ──
step "5/6  Pytest + coverage"
if pytest --cov=apps --cov=tests --cov-report=term-missing --cov-report=html -v --tb=short "$@"; then
    pass "Tests: all passed"
else
    fail "Tests: failures detected"
fi

# ── 6. Migration check ──
step "6/6  Migration sanity"
if python manage.py makemigrations --check --dry-run --verbosity=0 2>/dev/null; then
    pass "Migrations: up to date"
else
    fail "Migrations: unmigrated model changes detected"
fi

# ── Summary ──
echo ""
echo -e "${YELLOW}━━━ QA Summary ━━━${NC}"
echo -e "${GREEN}Passed: $PASS${NC}"
if [ "$FAIL" -gt 0 ]; then
    echo -e "${RED}Failed: $FAIL${NC}"
    exit 1
else
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
fi
