"""Spam protection utilities: honeypot field + session-based rate limiting."""

import time

from django import forms
from django.http import HttpResponseForbidden


# --- Honeypot Field ---


class HoneypotField(forms.CharField):
    """Hidden field that must remain empty. Bots that auto-fill all fields get caught."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("label", "")
        kwargs.setdefault(
            "widget",
            forms.TextInput(
                attrs={
                    "tabindex": "-1",
                    "autocomplete": "off",
                    "style": "position:absolute;left:-9999px;",
                }
            ),
        )
        super().__init__(*args, **kwargs)


class HoneypotFormMixin:
    """Add to any Form class to enable honeypot protection.

    Usage:
        class ContactForm(HoneypotFormMixin, forms.ModelForm):
            ...
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add field at runtime so Django's metaclass registers it as a BoundField
        self.fields["website_url"] = HoneypotField()

    def clean_website_url(self):
        value = self.cleaned_data.get("website_url", "")
        if value:
            raise forms.ValidationError("Spam detected.")
        return value


# --- Session-based Rate Limiting ---

# Default: max 5 submissions per 300 seconds (5 minutes)
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 300  # seconds


def check_rate_limit(
    request, key="form_submissions", max_count=RATE_LIMIT_MAX, window=RATE_LIMIT_WINDOW
):
    """Check if the request is within rate limits. Returns True if allowed."""
    now = time.time()
    timestamps = request.session.get(key, [])

    # Remove expired timestamps
    timestamps = [t for t in timestamps if now - t < window]

    if len(timestamps) >= max_count:
        return False

    timestamps.append(now)
    request.session[key] = timestamps
    return True


def rate_limit_response():
    """Return a 429-like response for rate-limited requests."""
    return HttpResponseForbidden(
        "Too many submissions. Please wait a few minutes and try again."
    )
