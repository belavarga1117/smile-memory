"""Root conftest — shared fixtures for all tests."""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from apps.accounts.models import User
from apps.blog.models import BlogCategory, BlogPost, Tag
from apps.bookings.models import Inquiry
from apps.customers.models import Customer
from apps.importer.models import ImportJob
from apps.marketing.models import Campaign, EmailTemplate, Subscriber
from apps.pages.models import FAQ, HeroSlide, Testimonial, TrustBadge
from apps.tours.models import (
    Airline,
    Category,
    Destination,
    ItineraryDay,
    PriceOption,
    Tour,
    TourDeparture,
    TourImage,
)


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin", email="admin@test.com", password="testpass123"
    )


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="staff", email="staff@test.com", password="testpass123", is_staff=True
    )


@pytest.fixture
def destination(db):
    return Destination.objects.create(
        name="Japan", name_th="ญี่ปุ่น", slug="japan", country_code_iso2="JP"
    )


@pytest.fixture
def category(db):
    return Category.objects.create(name="Beach", name_th="ชายหาด", slug="beach")


@pytest.fixture
def airline(db):
    return Airline.objects.create(code="TG", name="Thai Airways", name_th="การบินไทย")


@pytest.fixture
def tour(db, destination, category, airline):
    t = Tour.objects.create(
        title="Tokyo Explorer",
        title_th="สำรวจโตเกียว",
        slug="tokyo-explorer",
        product_code="ZGTYO-001",
        description="Explore Tokyo and Osaka",
        description_th="สำรวจโตเกียวและโอซาก้า",
        short_description="5-day Japan tour",
        status=Tour.Status.PUBLISHED,
        airline=airline,
        price_from=Decimal("29900.00"),
        duration_days=5,
        duration_nights=4,
        hotel_stars_min=4,
        hotel_stars_max=4,
        total_meals=10,
        is_featured=True,
    )
    t.destinations.add(destination)
    t.categories.add(category)
    # Ensure tour has an available departure so it passes the sold-out filter
    TourDeparture.objects.create(
        tour=t,
        departure_date=date.today() + timedelta(days=30),
        return_date=date.today() + timedelta(days=34),
        price_adult=Decimal("29900.00"),
        price_child=Decimal("25900.00"),
        status=TourDeparture.PeriodStatus.AVAILABLE,
    )
    return t


@pytest.fixture
def draft_tour(db):
    return Tour.objects.create(
        title="Draft Tour",
        slug="draft-tour",
        status=Tour.Status.DRAFT,
        price_from=Decimal("19900.00"),
        duration_days=3,
    )


@pytest.fixture
def departure(db, tour):
    return TourDeparture.objects.create(
        tour=tour,
        departure_date=date.today() + timedelta(days=30),
        return_date=date.today() + timedelta(days=34),
        price_adult=Decimal("29900.00"),
        price_child=Decimal("25900.00"),
        status=TourDeparture.PeriodStatus.AVAILABLE,
    )


@pytest.fixture
def itinerary_day(db, tour):
    return ItineraryDay.objects.create(
        tour=tour,
        day_number=1,
        title="Bangkok to Tokyo",
        title_th="กรุงเทพ - โตเกียว",
        description="Fly from Bangkok to Tokyo Narita.",
        breakfast="P",
        lunch="Y",
        dinner="Y",
        hotel_name="Tokyo Hilton",
        hotel_stars=4,
    )


@pytest.fixture
def tour_image(db, tour):
    return TourImage.objects.create(
        tour=tour,
        image_url="https://example.com/tokyo.jpg",
        caption="Tokyo Tower",
        sort_order=0,
    )


@pytest.fixture
def price_option(db, tour):
    return PriceOption.objects.create(
        tour=tour,
        name="Adult Double",
        name_th="ผู้ใหญ่ห้องคู่",
        price=Decimal("29900.00"),
    )


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        email="customer@test.com",
        first_name="John",
        last_name="Doe",
        phone="+66812345678",
        marketing_opt_in=True,
        tags="japan-interest,repeat-customer",
    )


@pytest.fixture
def inquiry(db, customer, tour, departure):
    return Inquiry.objects.create(
        customer=customer,
        tour=tour,
        departure=departure,
        num_adults=2,
        num_children=1,
        contact_name="John Doe",
        contact_email="customer@test.com",
        contact_phone="+66812345678",
        status=Inquiry.Status.NEW,
    )


@pytest.fixture
def email_template(db):
    return EmailTemplate.objects.create(
        name="Monthly Newsletter",
        subject="Latest Tours This Month",
        body_html="<h1>Hello {{ customer.first_name }}</h1>",
        body_text="Hello {{ customer.first_name }}",
    )


@pytest.fixture
def campaign(db, email_template):
    return Campaign.objects.create(
        name="January Newsletter",
        template=email_template,
        status=Campaign.Status.DRAFT,
    )


@pytest.fixture
def subscriber(db, customer):
    return Subscriber.objects.create(
        email="customer@test.com",
        is_active=True,
        customer=customer,
        source="footer",
    )


@pytest.fixture
def import_job(db, admin_user):
    return ImportJob.objects.create(
        name="Test Import",
        source=ImportJob.Source.ZEGO,
        file_format=ImportJob.FileFormat.CSV,
        imported_by=admin_user,
    )


@pytest.fixture
def hero_slide(db):
    return HeroSlide.objects.create(
        title="Discover Japan",
        title_th="ค้นพบญี่ปุ่น",
        subtitle="Explore the land of the rising sun",
        is_active=True,
    )


@pytest.fixture
def testimonial(db):
    return Testimonial.objects.create(
        name="Somchai",
        quote="Amazing trip!",
        rating=5,
        is_active=True,
    )


@pytest.fixture
def trust_badge(db):
    return TrustBadge.objects.create(
        icon="star", value="10,000+", label="Happy Customers"
    )


@pytest.fixture
def faq(db):
    return FAQ.objects.create(
        question="How do I book?",
        question_th="จองอย่างไร?",
        answer="Submit an inquiry form on any tour page.",
        answer_th="ส่งแบบฟอร์มสอบถามในหน้าทัวร์",
        is_active=True,
    )


@pytest.fixture
def blog_category(db):
    return BlogCategory.objects.create(name="Travel Tips", slug="travel-tips")


@pytest.fixture
def blog_tag(db):
    return Tag.objects.create(name="Japan", slug="japan")


@pytest.fixture
def blog_post(db, blog_category, blog_tag):
    from django.utils import timezone

    post = BlogPost.objects.create(
        title="Top 10 Tokyo Tips",
        slug="top-10-tokyo-tips",
        excerpt="Best things to do in Tokyo",
        body="Full article body here...",
        category=blog_category,
        status=BlogPost.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    post.tags.add(blog_tag)
    return post
