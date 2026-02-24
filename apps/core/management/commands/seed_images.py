"""Download curated Unsplash images and assign them to seed data models."""

import time
import urllib.request
from urllib.error import HTTPError, URLError

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.blog.models import BlogPost
from apps.pages.models import HeroSlide, Testimonial
from apps.tours.models import Destination, Tour

# Unsplash direct image URL (no API key required)
UNSPLASH_BASE = "https://images.unsplash.com/photo-{photo_id}"


def unsplash_url(photo_id, width=1200, quality=80, extra=""):
    """Build Unsplash direct download URL."""
    url = f"https://images.unsplash.com/{photo_id}?w={width}&q={quality}&fit=crop"
    if extra:
        url += f"&{extra}"
    return url


# ---------- Image mappings ----------

DESTINATION_IMAGES = {
    # slug → (unsplash_photo_id, description)
    "japan": ("photo-1490806843957-31f4c9a91c65", "Mt Fuji cherry blossoms"),
    "south-korea": ("photo-1538485399081-7191377e8241", "Hanbok at Gyeongbokgung"),
    "china": ("photo-1508804185872-d7badad00f7d", "Great Wall aerial"),
    "hong-kong": ("photo-1546636889-ba9fdd63583e", "Hong Kong skyline"),
    "vietnam": ("photo-1573790387438-4da905039392", "Ha Long Bay"),
    "taiwan": ("photo-1470004914212-05527e49370b", "Taipei 101"),
    "turkey": ("photo-1526048598645-62b31f82b8f5", "Cappadocia balloons"),
    "switzerland": ("photo-1527668752968-14dc70a27c95", "Mountain lake panorama"),
    "italy": ("photo-1516483638261-f4dbaf036963", "Cinque Terre colorful houses"),
    "france": ("photo-1502602898657-3e91760cbb34", "Paris Eiffel Tower golden"),
}

TOUR_IMAGES = {
    # slug → (unsplash_photo_id, description)
    "tokyo-osaka-classic": (
        "photo-1542051841857-5f90071e7989",
        "Shibuya neon night",
    ),
    "seoul-explorer": ("photo-1517154421773-0529f29ea451", "Seoul cityscape"),
    "hong-kong-macau": (
        "photo-1563789031959-4c02bcb41319",
        "Hong Kong harbour",
    ),
    "vietnam-hanoi-sapa": (
        "photo-1528181304800-259b08848526",
        "Golden rice terraces Sapa",
    ),
    "turkey-highlights": (
        "photo-1641128324972-af3212f0f6bd",
        "Cappadocia sunrise",
    ),
    "switzerland-classic": (
        "photo-1531366936337-7c912a4589a7",
        "Matterhorn",
    ),
    "taiwan-round-island": (
        "photo-1470004914212-05527e49370b",
        "Taipei temple streets",
    ),
    "italy-classic": (
        "photo-1514890547357-a9ee288728e0",
        "Venice canal gondola",
    ),
    "hokkaido-lavender": (
        "photo-1499002238440-d264edd596ec",
        "Purple lavender field mountain",
    ),
    "beijing-great-wall": (
        "photo-1547981609-4b6bfe67ca0b",
        "Great Wall close up",
    ),
}

HERO_SLIDE_IMAGES = {
    # title (partial match) → (unsplash_photo_id, description)
    "Cherry Blossoms": ("photo-1493976040374-85c8e12f0c0e", "Japan cherry blossom"),
    "China": ("photo-1608037521244-f1c6c7635194", "Great Wall winding green hills"),
    "Journey": ("photo-1476514525535-07fb3b4ae5f1", "Asia travel scenic wide"),
}

BLOG_IMAGES = {
    # slug → (unsplash_photo_id, description)
    "packing-tips-group-tours-asia": (
        "photo-1501594907352-04cda38ebc29",
        "Travel flat lay map passport",
    ),
    "first-timers-guide-japan": (
        "photo-1540959733332-eab4deabeeaf",
        "Tokyo street scene",
    ),
    "best-street-food-china": (
        "photo-1555939594-58d7cb561ad1",
        "Chinese street food",
    ),
    "group-tours-perfect-solo-travelers": (
        "photo-1539635278303-d4002c07eae3",
        "Happy group selfie",
    ),
    "photography-tips-asia-tour": (
        "photo-1502920917128-1aa500764cbd",
        "Camera mountain landscape",
    ),
}

# Static page images (not model-backed, saved to media/pages/)
STATIC_PAGE_IMAGES = {
    # filename → (unsplash_photo_id, description, width)
    "about-team.jpg": ("photo-1522199710521-72d69614c702", "Happy travelers", 1200),
}

TESTIMONIAL_IMAGES = {
    # name → (unsplash_photo_id, description)
    "Somchai P.": ("photo-1507003211169-0a1dd7228f2d", "Asian man portrait"),
    "Sarah L.": ("photo-1438761681033-6461ffad8d80", "Smiling woman portrait"),
    "Nattaya K.": ("photo-1494790108377-be9c29b29330", "Woman Bangkok portrait"),
    "Michael T.": ("photo-1500648767791-00dcc994a43e", "Man glasses portrait"),
    "Pranee S.": ("photo-1544005313-94ddf0286df2", "Thai woman portrait"),
    "David W.": ("photo-1506794778202-cad84cf45f1d", "Smiling man portrait"),
}


class Command(BaseCommand):
    help = "Download curated Unsplash images and assign to seed data models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing images",
        )

    def handle(self, *args, **options):
        force = options["force"]
        stats = {"ok": 0, "skip": 0, "fail": 0}

        self.stdout.write(self.style.MIGRATE_HEADING("Seeding images from Unsplash..."))
        self.stdout.write("")

        self._seed_destinations(stats, force)
        self._seed_tours(stats, force)
        self._seed_hero_slides(stats, force)
        self._seed_blog(stats, force)
        self._seed_testimonials(stats, force)
        self._seed_static_pages(stats, force)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Done! OK: {stats['ok']}, Skipped: {stats['skip']}, Failed: {stats['fail']}"
            )
        )

    def _download_image(self, photo_id, width=1200, extra=""):
        """Download image from Unsplash. Returns (bytes, filename) or (None, None)."""
        url = unsplash_url(photo_id, width=width, extra=extra)
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "SmileMemory/1.0 (seed-images)"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                # Determine extension from content-type
                content_type = resp.headers.get("Content-Type", "image/jpeg")
                ext = "jpg"
                if "png" in content_type:
                    ext = "png"
                elif "webp" in content_type:
                    ext = "webp"
                filename = f"{photo_id.replace('photo-', '')}.{ext}"
                return data, filename
        except (HTTPError, URLError, TimeoutError) as e:
            self.stderr.write(f"    Download failed: {e}")
            return None, None

    def _assign_image(self, instance, field_name, photo_id, label, stats, force, **dl_kwargs):
        """Download and assign image to model instance."""
        current = getattr(instance, field_name)
        if current and not force:
            self.stdout.write(f"  [SKIP] {label} — already has image")
            stats["skip"] += 1
            return

        data, filename = self._download_image(photo_id, **dl_kwargs)
        if data is None:
            self.stdout.write(self.style.ERROR(f"  [FAIL] {label}"))
            stats["fail"] += 1
            return

        getattr(instance, field_name).save(filename, ContentFile(data), save=True)
        size_kb = len(data) / 1024
        self.stdout.write(self.style.SUCCESS(f"  [OK] {label} ({size_kb:.0f} KB)"))
        stats["ok"] += 1
        time.sleep(0.3)  # Be polite to Unsplash

    def _seed_destinations(self, stats, force):
        self.stdout.write(self.style.MIGRATE_LABEL("Destinations:"))
        for slug, (photo_id, desc) in DESTINATION_IMAGES.items():
            try:
                dest = Destination.objects.get(slug=slug)
            except Destination.DoesNotExist:
                self.stdout.write(f"  [SKIP] {slug} — not in database")
                stats["skip"] += 1
                continue
            self._assign_image(
                dest, "image", photo_id, f"{dest.name} → {desc}", stats, force, width=1200
            )

    def _seed_tours(self, stats, force):
        self.stdout.write(self.style.MIGRATE_LABEL("Tour heroes:"))
        for slug, (photo_id, desc) in TOUR_IMAGES.items():
            try:
                tour = Tour.objects.get(slug=slug)
            except Tour.DoesNotExist:
                self.stdout.write(f"  [SKIP] {slug} — not in database")
                stats["skip"] += 1
                continue
            self._assign_image(
                tour, "hero_image", photo_id, f"{tour.title} → {desc}", stats, force, width=1400
            )

    def _seed_hero_slides(self, stats, force):
        self.stdout.write(self.style.MIGRATE_LABEL("Hero slides:"))
        for title_part, (photo_id, desc) in HERO_SLIDE_IMAGES.items():
            try:
                slide = HeroSlide.objects.get(title__icontains=title_part)
            except HeroSlide.DoesNotExist:
                self.stdout.write(f"  [SKIP] '{title_part}' — not in database")
                stats["skip"] += 1
                continue
            except HeroSlide.MultipleObjectsReturned:
                slide = HeroSlide.objects.filter(title__icontains=title_part).first()
            self._assign_image(
                slide, "image", photo_id, f"{slide.title} → {desc}", stats, force, width=1920
            )

    def _seed_blog(self, stats, force):
        self.stdout.write(self.style.MIGRATE_LABEL("Blog posts:"))
        for slug, (photo_id, desc) in BLOG_IMAGES.items():
            try:
                post = BlogPost.objects.get(slug=slug)
            except BlogPost.DoesNotExist:
                self.stdout.write(f"  [SKIP] {slug} — not in database")
                stats["skip"] += 1
                continue
            self._assign_image(
                post, "featured_image", photo_id, f"{post.title[:40]} → {desc}", stats, force, width=1200
            )

    def _seed_testimonials(self, stats, force):
        self.stdout.write(self.style.MIGRATE_LABEL("Testimonial avatars:"))
        for name, (photo_id, desc) in TESTIMONIAL_IMAGES.items():
            try:
                testimonial = Testimonial.objects.get(name=name)
            except Testimonial.DoesNotExist:
                self.stdout.write(f"  [SKIP] {name} — not in database")
                stats["skip"] += 1
                continue
            self._assign_image(
                testimonial,
                "avatar",
                photo_id,
                f"{name} → {desc}",
                stats,
                force,
                width=400,
                extra="crop=face",
            )

    def _seed_static_pages(self, stats, force):
        """Download images for static pages (not model-backed)."""
        import os

        from django.conf import settings

        self.stdout.write(self.style.MIGRATE_LABEL("Static pages:"))
        pages_dir = os.path.join(settings.MEDIA_ROOT, "pages")
        os.makedirs(pages_dir, exist_ok=True)

        for filename, (photo_id, desc, width) in STATIC_PAGE_IMAGES.items():
            filepath = os.path.join(pages_dir, filename)
            if os.path.exists(filepath) and not force:
                self.stdout.write(f"  [SKIP] {filename} — already exists")
                stats["skip"] += 1
                continue

            data, _ = self._download_image(photo_id, width=width)
            if data is None:
                self.stdout.write(self.style.ERROR(f"  [FAIL] {filename}"))
                stats["fail"] += 1
                continue

            with open(filepath, "wb") as f:
                f.write(data)
            size_kb = len(data) / 1024
            self.stdout.write(self.style.SUCCESS(f"  [OK] {filename} → {desc} ({size_kb:.0f} KB)"))
            stats["ok"] += 1
