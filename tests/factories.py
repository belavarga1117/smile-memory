"""Shared test factories for Smile Memory project."""

import factory
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


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@test.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    is_active = True


class AdminUserFactory(UserFactory):
    username = "admin_factory"
    is_staff = True
    is_superuser = True


class StaffUserFactory(UserFactory):
    username = factory.Sequence(lambda n: f"staff{n}")
    is_staff = True


class DestinationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Destination
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Destination {n}")
    name_th = factory.LazyAttribute(lambda o: f"จุดหมาย {o.name}")
    slug = factory.Sequence(lambda n: f"dest-{n}")
    country_code_iso2 = "JP"


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Category {n}")
    name_th = factory.LazyAttribute(lambda o: f"หมวดหมู่ {o.name}")
    slug = factory.Sequence(lambda n: f"cat-{n}")


class AirlineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Airline
        django_get_or_create = ("code",)

    code = factory.Sequence(lambda n: f"A{n:02d}")
    name = factory.Sequence(lambda n: f"Airline {n}")
    name_th = factory.LazyAttribute(lambda o: f"สายการบิน {o.name}")


class TourFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tour

    title = factory.Sequence(lambda n: f"Tour {n}")
    title_th = factory.LazyAttribute(lambda o: f"ทัวร์ {o.title}")
    slug = factory.Sequence(lambda n: f"tour-{n}")
    product_code = factory.Sequence(lambda n: f"PROD-{n:04d}")
    description = "Test tour description"
    description_th = "รายละเอียดทัวร์ทดสอบ"
    short_description = "Short desc"
    status = Tour.Status.PUBLISHED
    airline = factory.SubFactory(AirlineFactory)
    price_from = Decimal("29900.00")
    duration_days = 5
    duration_nights = 4
    hotel_stars_min = 4
    hotel_stars_max = 4
    total_meals = 10
    is_featured = False

    @factory.post_generation
    def destinations(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for dest in extracted:
                self.destinations.add(dest)

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for cat in extracted:
                self.categories.add(cat)

    @factory.post_generation
    def with_departure(self, create, extracted, **kwargs):
        """Auto-create one available departure so tour passes the sold-out filter."""
        if not create:
            return
        # extracted=False disables auto-creation (for tests that control departures)
        if extracted is False:
            return
        TourDeparture.objects.create(
            tour=self,
            departure_date=date.today() + timedelta(days=30),
            return_date=date.today() + timedelta(days=34),
            price_adult=Decimal("29900.00"),
            price_child=Decimal("25900.00"),
            status=TourDeparture.PeriodStatus.AVAILABLE,
        )


class TourDepartureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TourDeparture

    tour = factory.SubFactory(TourFactory)
    departure_date = factory.LazyFunction(lambda: date.today() + timedelta(days=30))
    return_date = factory.LazyFunction(lambda: date.today() + timedelta(days=34))
    price_adult = Decimal("29900.00")
    price_child = Decimal("25900.00")
    status = TourDeparture.PeriodStatus.AVAILABLE


class ItineraryDayFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ItineraryDay

    tour = factory.SubFactory(TourFactory)
    day_number = factory.Sequence(lambda n: n + 1)
    title = factory.LazyAttribute(lambda o: f"Day {o.day_number}")
    title_th = factory.LazyAttribute(lambda o: f"วัน {o.day_number}")
    description = "Day description"
    breakfast = "Y"
    lunch = "Y"
    dinner = "Y"
    hotel_name = "Test Hotel"
    hotel_stars = 4


class TourImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TourImage

    tour = factory.SubFactory(TourFactory)
    image_url = factory.Sequence(lambda n: f"https://example.com/img{n}.jpg")
    caption = factory.Sequence(lambda n: f"Caption {n}")
    sort_order = factory.Sequence(lambda n: n)


class PriceOptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PriceOption

    tour = factory.SubFactory(TourFactory)
    name = "Adult Double"
    name_th = "ผู้ใหญ่ห้องคู่"
    price = Decimal("29900.00")


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"customer{n}@test.com")
    first_name = "Test"
    last_name = "Customer"
    phone = "+66812345678"
    marketing_opt_in = True
    tags = ""


class InquiryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Inquiry

    customer = factory.SubFactory(CustomerFactory)
    tour = factory.SubFactory(TourFactory)
    num_adults = 2
    num_children = 1
    contact_name = "Test Customer"
    contact_email = factory.LazyAttribute(lambda o: o.customer.email)
    contact_phone = "+66812345678"
    status = Inquiry.Status.NEW


class EmailTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmailTemplate

    name = factory.Sequence(lambda n: f"Template {n}")
    subject = "Test Subject"
    body_html = "<h1>Hello {{ customer.first_name }}</h1>"
    body_text = "Hello {{ customer.first_name }}"


class CampaignFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Campaign

    name = factory.Sequence(lambda n: f"Campaign {n}")
    template = factory.SubFactory(EmailTemplateFactory)
    status = Campaign.Status.DRAFT


class SubscriberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subscriber

    email = factory.Sequence(lambda n: f"subscriber{n}@test.com")
    is_active = True
    source = "footer"


class HeroSlideFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HeroSlide

    title = "Discover Japan"
    title_th = "ค้นพบญี่ปุ่น"
    subtitle = "Explore the land of the rising sun"
    is_active = True


class TestimonialFactory(factory.django.DjangoModelFactory):
    __test__ = False  # Prevent pytest from collecting this as a test class

    class Meta:
        model = Testimonial

    name = "Somchai"
    quote = "Amazing trip!"
    rating = 5
    is_active = True


class TrustBadgeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TrustBadge

    icon = "star"
    value = "10,000+"
    label = "Happy Customers"


class FAQFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FAQ

    question = "How do I book?"
    question_th = "จองอย่างไร?"
    answer = "Submit an inquiry form on any tour page."
    answer_th = "ส่งแบบฟอร์มสอบถามในหน้าทัวร์"
    is_active = True


class BlogCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BlogCategory
        django_get_or_create = ("slug",)

    name = "Travel Tips"
    slug = factory.Sequence(lambda n: f"blog-cat-{n}")


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Tag {n}")
    slug = factory.Sequence(lambda n: f"tag-{n}")


class BlogPostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BlogPost

    title = factory.Sequence(lambda n: f"Blog Post {n}")
    title_th = factory.LazyAttribute(lambda o: f"บทความ {o.title}")
    slug = factory.Sequence(lambda n: f"blog-post-{n}")
    excerpt = "Test excerpt"
    body = "Full article body here..."
    body_th = "เนื้อหาบทความ..."
    category = factory.SubFactory(BlogCategoryFactory)
    status = BlogPost.Status.PUBLISHED
    published_at = factory.LazyFunction(
        lambda: __import__("django.utils.timezone", fromlist=["now"]).now()
    )


class ImportJobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ImportJob

    name = factory.Sequence(lambda n: f"Import Job {n}")
    source = ImportJob.Source.ZEGO
    file_format = ImportJob.FileFormat.CSV
    imported_by = factory.SubFactory(AdminUserFactory)
