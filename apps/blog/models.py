from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from apps.core.models import TimeStampedModel


class BlogCategory(TimeStampedModel):
    """Blog post category (e.g. Travel Tips, Destination Guides)."""

    name = models.CharField(max_length=100)
    name_th = models.CharField(max_length=100, blank=True)
    slug = models.SlugField(unique=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Blog Categories"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(TimeStampedModel):
    """Blog tag for flexible tagging."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogPost(TimeStampedModel):
    """Blog post / travel tip article."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=300)
    title_th = models.CharField(max_length=300, blank=True)
    slug = models.SlugField(unique=True, max_length=350)
    excerpt = models.TextField(blank=True, help_text="Short summary for listing pages")
    excerpt_th = models.TextField(blank=True)
    body = models.TextField()
    body_th = models.TextField(blank=True)

    # Classification
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    # Media
    featured_image = models.ImageField(upload_to="blog/", blank=True)
    featured_image_url = models.URLField(blank=True)

    # Author
    author_name = models.CharField(
        max_length=200, blank=True, default="Smile Memory Team"
    )

    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    # Dates
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["status", "category"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def featured_img(self):
        if self.featured_image:
            return self.featured_image.url
        return self.featured_image_url
