"""Development settings."""

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Database: uses DATABASE_URL from .env
# Local: postgres://travel:travel_dev@localhost:5432/smile_memory  (brew postgresql@16)
# Fallback: SQLite (for CI / environments without PostgreSQL)
# DATABASES is already set in base.py via env.db("DATABASE_URL", default="sqlite:///db.sqlite3")

# Console email backend (prints emails to terminal)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CORS - allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# Debug toolbar (uncomment when installed)
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
# INTERNAL_IPS = ["127.0.0.1"]
