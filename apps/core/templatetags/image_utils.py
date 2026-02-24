"""Template tags for image optimization: thumbnail generation + WebP conversion."""

import hashlib
import logging
import os

from PIL import Image

from django import template
from django.conf import settings

logger = logging.getLogger(__name__)
register = template.Library()

CACHE_DIR = "cache"


@register.simple_tag
def thumbnail(image_field, width=0):
    """Generate a WebP thumbnail from a Django ImageField.

    Usage:
        {% load image_utils %}
        <img src="{% thumbnail tour.hero_image 600 %}" alt="...">

    Returns the URL of the cached WebP thumbnail.
    Falls back to the original image URL on error.
    """
    if not image_field:
        return ""

    # Get source file path
    try:
        source_path = image_field.path
    except (ValueError, AttributeError):
        return ""

    if not os.path.exists(source_path):
        try:
            return image_field.url
        except ValueError:
            return ""

    # Build cache path
    width = int(width)
    cache_key = hashlib.md5(f"{source_path}:{width}".encode()).hexdigest()[:12]
    suffix = f"_w{width}" if width else ""
    cache_filename = f"{cache_key}{suffix}.webp"
    cache_dir = os.path.join(settings.MEDIA_ROOT, CACHE_DIR)
    cache_path = os.path.join(cache_dir, cache_filename)
    cache_url = f"{settings.MEDIA_URL}{CACHE_DIR}/{cache_filename}"

    # Return cached version if it exists
    if os.path.exists(cache_path):
        return cache_url

    # Generate the thumbnail
    try:
        os.makedirs(cache_dir, exist_ok=True)
        with Image.open(source_path) as img:
            # Convert to RGB if necessary (e.g. RGBA PNGs)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Resize if width specified and image is larger
            if width and img.width > width:
                ratio = width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((width, new_height), Image.LANCZOS)

            img.save(cache_path, "WEBP", quality=80)
    except Exception:
        logger.exception("Failed to generate thumbnail for %s", source_path)
        try:
            return image_field.url
        except ValueError:
            return ""

    return cache_url
