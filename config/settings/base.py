"""Base settings shared across all environments."""

import os
from pathlib import Path

import environ

# Build paths: BASE_DIR = travel-agency/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# App version — read from VERSION file (single source of truth)
_version_file = BASE_DIR / "VERSION"
APP_VERSION = _version_file.read_text().strip() if _version_file.exists() else "0.0.0"

# Environment variables
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Application definition
INSTALLED_APPS = [
    # Django built-in
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.postgres",
    # Third-party
    "rest_framework",
    "django_filters",
    "corsheaders",
    # Local apps
    "apps.core",
    "apps.accounts",
    "apps.tours",
    "apps.bookings",
    "apps.customers",
    "apps.marketing",
    "apps.importer",
    "apps.pages",
    "apps.blog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "apps.core.context_processors.site_config",
                "apps.core.context_processors.language_urls",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}

# Custom user model
AUTH_USER_MODEL = "accounts.User"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "th"
LANGUAGES = [
    ("th", "Thai"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Asia/Bangkok"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
}

# Celery
CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat — scheduled tasks
from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "sync-all-tours-morning": {
        "task": "importer.sync_all_tours",
        "schedule": crontab(hour=20, minute=0),  # 03:00 ICT = 20:00 UTC
    },
    "sync-all-tours-afternoon": {
        "task": "importer.sync_all_tours",
        "schedule": crontab(hour=8, minute=0),  # 15:00 ICT = 08:00 UTC
    },
}

# Email
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@smilememorytravel.com")
ADMIN_EMAIL = env("ADMIN_EMAIL", default="admin@smilememorytravel.com")

# Site configuration
SITE_NAME = "Smile Memory"
SITE_URL = env("SITE_URL", default="https://smilememorytravel.com")

# Google Analytics 4 — set GOOGLE_ANALYTICS_ID in Railway env vars (e.g. G-XXXXXXXXXX)
# If empty/unset, no tracking script is rendered.
GOOGLE_ANALYTICS_ID = env("GOOGLE_ANALYTICS_ID", default="")
