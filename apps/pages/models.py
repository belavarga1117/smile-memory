from django.db import models

from apps.core.models import TimeStampedModel


class HeroSlide(TimeStampedModel):
    """Homepage hero carousel slide."""

    title = models.CharField(max_length=200)
    title_th = models.CharField(max_length=200, blank=True)
    subtitle = models.CharField(max_length=300, blank=True)
    subtitle_th = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to="heroes/", blank=True)
    image_url = models.URLField(blank=True, help_text="External image URL")
    cta_text = models.CharField(max_length=100, blank=True, default="Explore Tours")
    cta_text_th = models.CharField(max_length=100, blank=True)
    cta_url = models.CharField(max_length=300, default="/tours/")
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return self.title

    @property
    def bg_image(self):
        if self.image:
            return self.image.url
        return self.image_url


class Testimonial(TimeStampedModel):
    """Customer testimonial for homepage."""

    name = models.CharField(max_length=200)
    name_th = models.CharField(max_length=200, blank=True)
    location = models.CharField(
        max_length=200, blank=True, help_text="e.g. Bangkok, Thailand"
    )
    avatar = models.ImageField(upload_to="testimonials/", blank=True)
    quote = models.TextField()
    quote_th = models.TextField(blank=True)
    tour_name = models.CharField(
        max_length=300, blank=True, help_text="Tour they went on"
    )
    rating = models.PositiveIntegerField(default=5, help_text="1-5 stars")
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.name} — {self.rating} stars"


class TrustBadge(TimeStampedModel):
    """Trust/stats badges for homepage (e.g. 10,000+ customers, 500+ tours)."""

    icon = models.CharField(max_length=50, help_text="CSS class or emoji")
    value = models.CharField(max_length=50, help_text="e.g. 10,000+")
    label = models.CharField(max_length=100)
    label_th = models.CharField(max_length=100, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.value} {self.label}"


class FAQ(TimeStampedModel):
    """Frequently asked question — for homepage or standalone page."""

    question = models.CharField(max_length=500)
    question_th = models.CharField(max_length=500, blank=True)
    answer = models.TextField()
    answer_th = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class ContactMessage(TimeStampedModel):
    """Contact form submission."""

    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    subject = models.CharField(max_length=300)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.subject}"
