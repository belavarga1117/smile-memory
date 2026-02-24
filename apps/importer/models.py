"""Import pipeline models — tracks file uploads and import job results."""

import uuid

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class ImportJob(TimeStampedModel):
    """Represents a single import operation (file upload or API sync)."""

    class Source(models.TextChoices):
        ZEGO = "zego", "Zego Travel"
        GS25 = "gs25", "GS25 Travel"
        GO365 = "go365", "Go365 Travel"
        REALJOURNEY = "realjourney", "Real Journey"
        MANUAL = "manual", "Manual Upload"
        OTHER = "other", "Other"

    class FileFormat(models.TextChoices):
        EXCEL = "excel", "Excel (.xlsx/.xls)"
        CSV = "csv", "CSV (.csv)"
        PDF = "pdf", "PDF (.pdf)"
        HTML = "html", "HTML (web page)"
        API = "api", "API"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PARSING = "parsing", "Parsing File"
        MAPPING = "mapping", "Mapping Fields"
        IMPORTING = "importing", "Importing Data"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        PARTIAL = "partial", "Partially Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=300, help_text="Descriptive name for this import"
    )
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.MANUAL
    )
    file_format = models.CharField(max_length=10, choices=FileFormat.choices)

    # File upload
    uploaded_file = models.FileField(upload_to="imports/%Y/%m/", blank=True)
    source_url = models.URLField(blank=True, help_text="URL for HTML/API imports")

    # Field mapping configuration (JSON)
    field_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text="Column/field mapping: {source_field: django_field}",
    )

    # Results
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    total_rows = models.PositiveIntegerField(default=0)
    rows_created = models.PositiveIntegerField(default=0)
    rows_updated = models.PositiveIntegerField(default=0)
    rows_skipped = models.PositiveIntegerField(default=0)
    rows_failed = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

    # Parsed data preview (first N rows as JSON for admin review before import)
    parsed_preview = models.JSONField(default=list, blank=True)
    parsed_headers = models.JSONField(default=list, blank=True)

    # Who ran the import
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_jobs",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.name} ({self.get_source_display()}) — {self.get_status_display()}"
        )

    @property
    def success_rate(self):
        total = self.rows_created + self.rows_updated + self.rows_failed
        if total == 0:
            return 0
        return round((self.rows_created + self.rows_updated) / total * 100, 1)


class ImportLog(TimeStampedModel):
    """Per-row log entry for import jobs — tracks success/failure for each record."""

    class Level(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"
        SUCCESS = "success", "Success"

    job = models.ForeignKey(ImportJob, on_delete=models.CASCADE, related_name="logs")
    row_number = models.PositiveIntegerField(null=True, blank=True)
    level = models.CharField(max_length=10, choices=Level.choices, default=Level.INFO)
    message = models.TextField()
    raw_data = models.JSONField(default=dict, blank=True, help_text="Original row data")

    class Meta:
        ordering = ["row_number", "created_at"]

    def __str__(self):
        return f"Row {self.row_number}: [{self.level}] {self.message[:80]}"
