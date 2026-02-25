from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from apps.core.models import TimeStampedModel


class Destination(TimeStampedModel):
    """Geographic destination (country, region, or city)."""

    name = models.CharField(max_length=200)
    name_th = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(unique=True, max_length=250)
    country_code_iso2 = models.CharField(
        max_length=2, blank=True, help_text="ISO 3166-1 alpha-2"
    )
    country_code_iso3 = models.CharField(
        max_length=3, blank=True, help_text="ISO 3166-1 alpha-3"
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )
    description = models.TextField(blank=True)
    description_th = models.TextField(blank=True)
    image = models.ImageField(upload_to="destinations/", blank=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Category(TimeStampedModel):
    """Tour category (e.g., Beach, Cultural, Adventure, Luxury)."""

    name = models.CharField(max_length=100)
    name_th = models.CharField(max_length=100, blank=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True, help_text="CSS class or emoji")
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["sort_order"]

    def __str__(self):
        return self.name


class Airline(TimeStampedModel):
    """Airline information."""

    code = models.CharField(
        max_length=10, unique=True, help_text="IATA code e.g. TG, CX"
    )
    name = models.CharField(max_length=200)
    name_th = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(upload_to="airlines/", blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Tour(TimeStampedModel):
    """Central tour/package model — maps to Zego API ProgramTour."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    # Basic info
    title = models.CharField(max_length=300)
    title_th = models.CharField(max_length=300, blank=True)
    slug = models.SlugField(unique=True, max_length=350)
    product_code = models.CharField(
        max_length=50,
        blank=True,
        unique=True,
        null=True,
        help_text="Wholesaler tour code e.g. ZGHKG-2413CX",
    )
    highlight = models.TextField(blank=True, help_text="Tour highlights text")
    highlight_th = models.TextField(blank=True)
    description = models.TextField(blank=True)
    description_th = models.TextField(blank=True)
    short_description = models.CharField(max_length=500, blank=True)
    short_description_th = models.CharField(max_length=500, blank=True)

    # Classification
    destinations = models.ManyToManyField(Destination, related_name="tours")
    locations = models.JSONField(
        default=list,
        blank=True,
        help_text="City names visited e.g. ['Tokyo', 'Osaka', 'Kyoto']",
    )
    categories = models.ManyToManyField(Category, related_name="tours", blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    is_featured = models.BooleanField(default=False)

    # Airline
    airline = models.ForeignKey(
        Airline, on_delete=models.SET_NULL, null=True, blank=True, related_name="tours"
    )

    # Pricing (base — detailed pricing in TourDeparture)
    price_from = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Lowest adult double-occupancy price across departures",
    )
    currency = models.CharField(max_length=3, default="THB")

    # Tour details
    duration_days = models.PositiveIntegerField(null=True, blank=True)
    duration_nights = models.PositiveIntegerField(null=True, blank=True)
    hotel_stars_min = models.PositiveIntegerField(null=True, blank=True)
    hotel_stars_max = models.PositiveIntegerField(null=True, blank=True)
    plane_meals = models.BooleanField(
        default=False, help_text="In-flight meals included"
    )
    total_meals = models.PositiveIntegerField(
        null=True, blank=True, help_text="Total meals in tour"
    )
    includes = models.TextField(blank=True, help_text="What is included")
    includes_th = models.TextField(blank=True)
    excludes = models.TextField(blank=True, help_text="What is not included")
    excludes_th = models.TextField(blank=True)

    # Media
    hero_image = models.ImageField(upload_to="tours/heroes/", blank=True)
    hero_image_url = models.URLField(
        blank=True, help_text="External image URL from wholesaler"
    )
    thumbnail = models.ImageField(upload_to="tours/thumbnails/", blank=True)
    pdf_file = models.FileField(upload_to="tours/pdfs/", blank=True)
    pdf_url = models.URLField(blank=True, help_text="External PDF URL from wholesaler")
    word_url = models.URLField(
        blank=True, help_text="External Word doc URL from wholesaler"
    )

    # Source tracking (import pipeline)
    source = models.CharField(
        max_length=100, blank=True, help_text="Wholesaler name e.g. Zego"
    )
    external_id = models.CharField(
        max_length=200, blank=True, help_text="Product ID from source"
    )
    source_url = models.URLField(max_length=500, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-is_featured", "-created_at"]
        indexes = [
            models.Index(fields=["status", "is_featured"]),
            models.Index(fields=["status", "price_from"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["source", "external_id"]),
            models.Index(fields=["product_code"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("tours:detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title) or slugify(self.product_code or "tour")
        super().save(*args, **kwargs)

    @property
    def duration_display(self):
        if self.duration_days and self.duration_nights:
            return f"{self.duration_days}D/{self.duration_nights}N"
        if self.duration_days:
            return f"{self.duration_days} days"
        return ""

    @property
    def hotel_stars_display(self):
        if self.hotel_stars_min and self.hotel_stars_max:
            if self.hotel_stars_min == self.hotel_stars_max:
                return f"{self.hotel_stars_min}-star"
            return f"{self.hotel_stars_min}-{self.hotel_stars_max} star"
        return ""

    def update_price_from(self):
        """Recalculate price_from from available departures."""
        cheapest = (
            self.departures.filter(status=TourDeparture.PeriodStatus.AVAILABLE)
            .order_by("price_adult")
            .values_list("price_adult", flat=True)
            .first()
        )
        if cheapest:
            self.price_from = cheapest
            self.save(update_fields=["price_from"])


class TourDeparture(TimeStampedModel):
    """Specific departure date/group for a tour — maps to Zego API Period."""

    class PeriodStatus(models.TextChoices):
        AVAILABLE = "available", "Available"
        SOLDOUT = "soldout", "Sold Out"
        WAITLIST = "waitlist", "Waitlist"
        CLOSED = "closed", "Close Group"

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="departures")
    period_code = models.CharField(
        max_length=50, blank=True, help_text="Group code e.g. TFU-250320R-VZ"
    )
    bus = models.CharField(
        max_length=10, blank=True, help_text="Bus designation (A, B, C)"
    )

    # Dates
    departure_date = models.DateField()
    return_date = models.DateField()

    # Airline override (if different from tour default)
    airline = models.ForeignKey(
        Airline,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    departure_airport = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g. SUVARNABHUMI, DONMUEANG",
    )

    # Capacity
    group_size = models.PositiveIntegerField(null=True, blank=True)
    booked = models.PositiveIntegerField(default=0)
    seats_available = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=PeriodStatus.choices,
        default=PeriodStatus.AVAILABLE,
    )

    # Pricing — adult double occupancy (base price)
    price_adult = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Adult double occupancy"
    )
    price_child = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Child with bed",
    )
    price_child_no_bed = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    price_infant = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    price_join_land = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Land only, no flights",
    )

    # Room supplements
    price_single_supplement = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Extra for single room"
    )
    price_twin_upgrade = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    price_double_upgrade = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    price_triple_upgrade = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )

    # Visa pricing
    price_single_visa = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    price_group_visa = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    price_express_visa = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Deposit
    deposit = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    # Commission (internal, not shown to customers)
    commission_agent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    commission_sale = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Promotional pricing (_End fields from Zego = adjusted prices)
    price_adult_promo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Promotional price, 0 = no promo",
    )
    price_child_promo = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    # Source tracking
    external_period_id = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["departure_date"]
        indexes = [
            models.Index(fields=["departure_date", "status"]),
            models.Index(fields=["tour", "departure_date"]),
        ]

    def __str__(self):
        return (
            f"{self.tour.title} — {self.departure_date} ({self.get_status_display()})"
        )

    @property
    def effective_price(self):
        """Return promo price if set and lower than regular, otherwise regular price."""
        if (
            self.price_adult_promo
            and self.price_adult_promo > 0
            and self.price_adult
            and self.price_adult_promo < self.price_adult
        ):
            return self.price_adult_promo
        return self.price_adult

    @property
    def has_promo(self):
        return bool(
            self.price_adult_promo
            and self.price_adult_promo > 0
            and self.price_adult_promo < self.price_adult
        )


class TourFlight(TimeStampedModel):
    """Flight information for a departure — maps to Zego API Flights."""

    departure = models.ForeignKey(
        TourDeparture, on_delete=models.CASCADE, related_name="flights"
    )
    airline = models.ForeignKey(
        Airline, on_delete=models.SET_NULL, null=True, blank=True
    )
    flight_number = models.CharField(max_length=20)
    route = models.CharField(max_length=50, help_text="e.g. BKK-NRT")
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.flight_number} {self.route}"


class TourImage(TimeStampedModel):
    """Additional tour images."""

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="tours/gallery/", blank=True)
    image_url = models.URLField(blank=True, help_text="External image URL")
    caption = models.CharField(max_length=300, blank=True)
    caption_th = models.CharField(max_length=300, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.tour.title} — image {self.sort_order}"


class ItineraryDay(TimeStampedModel):
    """Day-by-day itinerary — maps to Zego API Itinerarys."""

    tour = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name="itinerary_days"
    )
    day_number = models.PositiveIntegerField()
    title = models.CharField(max_length=300)
    title_th = models.CharField(max_length=300, blank=True)
    description = models.TextField()
    description_th = models.TextField(blank=True)

    # Meals (Y/N/P=Plane/C=Check-in per Zego convention)
    breakfast = models.CharField(max_length=1, blank=True, help_text="Y/N/P/C")
    breakfast_description = models.CharField(max_length=300, blank=True)
    lunch = models.CharField(max_length=1, blank=True, help_text="Y/N/P/C")
    lunch_description = models.CharField(max_length=300, blank=True)
    dinner = models.CharField(max_length=1, blank=True, help_text="Y/N/P/C")
    dinner_description = models.CharField(max_length=300, blank=True)

    # Accommodation
    hotel_name = models.CharField(max_length=300, blank=True)
    hotel_stars = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["day_number"]
        unique_together = ["tour", "day_number"]

    def __str__(self):
        return f"Day {self.day_number}: {self.title}"

    @property
    def meals_display(self):
        """Return e.g. 'B, L, D' based on meal fields."""
        meals = []
        if self.breakfast in ("Y", "P"):
            meals.append("B")
        if self.lunch in ("Y", "P"):
            meals.append("L")
        if self.dinner in ("Y", "P"):
            meals.append("D")
        return ", ".join(meals)


class PriceOption(TimeStampedModel):
    """Static pricing tiers for manually-entered tours (not via API)."""

    tour = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name="price_options"
    )
    name = models.CharField(max_length=200)
    name_th = models.CharField(max_length=200, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="THB")
    description = models.CharField(max_length=500, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.name}: {self.price} {self.currency}"
