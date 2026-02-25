#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# dev.sh — Local development stack launcher
#
# Starts all services needed for full local development:
#   • PostgreSQL 16  (brew service — already running at login)
#   • Redis          (brew service — already running at login)
#   • Django dev server
#   • Celery worker  (in background, logs → /tmp/celery_worker.log)
#   • Celery beat    (in background, logs → /tmp/celery_beat.log)
#   • Tailwind CSS   (watch mode, auto-rebuild on change)
#
# Usage:
#   ./scripts/dev.sh          — start everything
#   ./scripts/dev.sh --no-css — skip Tailwind (when not changing styles)
#
# Stop: Ctrl+C stops Django; Celery processes are killed automatically.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$PROJECT_DIR/venv/bin/activate"
PG_BIN="/opt/homebrew/opt/postgresql@16/bin"

NO_CSS=false
for arg in "$@"; do
  [[ "$arg" == "--no-css" ]] && NO_CSS=true
done

# ── Colour helpers ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${CYAN}[dev]${NC} $*"; }
ok()   { echo -e "${GREEN}[dev]${NC} $*"; }
warn() { echo -e "${YELLOW}[dev]${NC} $*"; }
err()  { echo -e "${RED}[dev]${NC} $*"; }

# ── Cleanup on exit ─────────────────────────────────────────────────────────
PIDS=()
cleanup() {
  log "Leállítás..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  ok "Minden leállt."
}
trap cleanup EXIT INT TERM

# ── Virtual environment ──────────────────────────────────────────────────────
if [[ ! -f "$VENV" ]]; then
  err "Nincs venv: $VENV — futtasd: python -m venv venv && pip install -r requirements/dev.txt"
  exit 1
fi
# shellcheck disable=SC1090
source "$VENV"

# ── Add PostgreSQL 16 to PATH ────────────────────────────────────────────────
export PATH="$PG_BIN:$PATH"

# ── Check PostgreSQL ─────────────────────────────────────────────────────────
if ! brew services list | grep -q "postgresql@16.*started"; then
  log "PostgreSQL nem fut — indítás..."
  brew services start postgresql@16
  sleep 2
fi
ok "PostgreSQL: fut"

# ── Check Redis ──────────────────────────────────────────────────────────────
if ! brew services list | grep -q "redis.*started"; then
  log "Redis nem fut — indítás..."
  brew services start redis
  sleep 1
fi
ok "Redis: fut"

# ── Pending migrations check ─────────────────────────────────────────────────
cd "$PROJECT_DIR"
PENDING=$(python manage.py showmigrations --plan 2>/dev/null | grep -c "\[ \]" || true)
if [[ "$PENDING" -gt 0 ]]; then
  warn "$PENDING pending migration — futtatom: manage.py migrate"
  python manage.py migrate
fi

# ── Celery worker ─────────────────────────────────────────────────────────────
log "Celery worker indítása (log: /tmp/celery_worker.log)..."
celery -A config worker -l info --concurrency=2 > /tmp/celery_worker.log 2>&1 &
PIDS+=($!)
ok "Celery worker: PID ${PIDS[-1]}"

# ── Celery beat ───────────────────────────────────────────────────────────────
log "Celery beat indítása (log: /tmp/celery_beat.log)..."
celery -A config beat -l info > /tmp/celery_beat.log 2>&1 &
PIDS+=($!)
ok "Celery beat: PID ${PIDS[-1]}"

# ── Tailwind CSS watcher ──────────────────────────────────────────────────────
if [[ "$NO_CSS" == false ]]; then
  if command -v npm &>/dev/null && [[ -f "$PROJECT_DIR/package.json" ]]; then
    log "Tailwind CSS watch indítása..."
    npm --prefix "$PROJECT_DIR" run css:watch > /tmp/tailwind.log 2>&1 &
    PIDS+=($!)
    ok "Tailwind: PID ${PIDS[-1]}"
  else
    warn "npm nem elérhető — Tailwind kihagyva (--no-css-sel is indítható)"
  fi
fi

# ── Django dev server ─────────────────────────────────────────────────────────
echo ""
ok "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ok "  Smile Memory dev stack fut!"
ok "  URL:           http://localhost:8000"
ok "  Admin:         http://localhost:8000/admin/"
ok "  Celery worker: tail -f /tmp/celery_worker.log"
ok "  Celery beat:   tail -f /tmp/celery_beat.log"
ok "  Leállítás:     Ctrl+C"
ok "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python manage.py runserver
