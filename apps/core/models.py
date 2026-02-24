from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base providing created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SiteConfiguration(models.Model):
    """Singleton model for site-wide settings editable via admin."""

    site_name = models.CharField(max_length=200, default="Smile Memory")
    admin_email = models.EmailField(default="admin@smilememory.com")
    phone_number = models.CharField(max_length=50, blank=True)
    whatsapp_number = models.CharField(max_length=50, blank=True)
    line_id = models.CharField(max_length=100, blank=True, help_text="LINE @ ID")
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    address = models.TextField(blank=True)
    address_th = models.TextField(blank=True)
    meta_description = models.TextField(blank=True)
    meta_description_th = models.TextField(blank=True)

    # Payment info
    bank_account_info = models.TextField(blank=True, help_text="Bank transfer details")
    bank_account_info_th = models.TextField(blank=True)

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1  # Enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
