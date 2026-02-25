"""Tests for scraper data quality: HTML cleaning, junk removal, image sync."""

import pytest


class TestHTMLToText:
    """Tests for ZegoScraper._html_to_text()."""

    def _scraper(self):
        from apps.importer.scrapers.zego import ZegoScraper

        return ZegoScraper()

    def test_strips_html_tags(self):
        s = self._scraper()
        assert s._html_to_text("<p>Hello world</p>") == "Hello world"

    def test_strips_class_attributes(self):
        s = self._scraper()
        result = s._html_to_text(
            '<div class="ql-editor"><p class="ql-align">Text</p></div>'
        )
        assert "ql-editor" not in result
        assert "ql-align" not in result
        assert "Text" in result

    def test_br_becomes_newline(self):
        s = self._scraper()
        result = s._html_to_text("Line1<br>Line2<br/>Line3")
        assert "\n" in result

    def test_decodes_html_entities(self):
        s = self._scraper()
        assert s._html_to_text("&amp; &lt; &gt;") == "& < >"

    def test_decodes_double_encoded(self):
        """Double-encoded HTML (&lt;p&gt;) is decoded to text."""
        s = self._scraper()
        result = s._html_to_text("&lt;p&gt;text&lt;/p&gt;")
        assert "<p>" not in result
        assert "text" in result

    def test_removes_zego_modal_junk(self):
        s = self._scraper()
        html = "<p>ไฮไลท์ทัวร์</p><div>× ส่งโปรแกรมทัวร์ Email ผู้รับ Close Send</div>"
        result = s._html_to_text(html)
        assert "ส่งโปรแกรมทัวร์" not in result
        assert "ไฮไลท์ทัวร์" in result

    def test_removes_email_close_send_junk(self):
        s = self._scraper()
        result = s._html_to_text("real content\nEmail ผู้รับ blah blah Close Send")
        assert "Close Send" not in result
        assert "real content" in result

    def test_empty_string_returns_empty(self):
        s = self._scraper()
        assert s._html_to_text("") == ""

    def test_none_returns_empty(self):
        s = self._scraper()
        assert s._html_to_text(None) == ""

    def test_plain_text_unchanged(self):
        s = self._scraper()
        result = s._html_to_text("วันที่ 1 กรุงเทพ - โตเกียว")
        assert result == "วันที่ 1 กรุงเทพ - โตเกียว"

    def test_collapses_blank_lines(self):
        s = self._scraper()
        result = s._html_to_text("<p>Line 1</p><p></p><p></p><p>Line 2</p>")
        assert "\n\n\n" not in result


class TestSanitizeTourData:
    """Tests for scrape_tours._sanitize_tour_data()."""

    def _get_command(self):
        from apps.importer.management.commands.scrape_tours import Command

        cmd = Command()
        cmd.stdout = type("obj", (object,), {"write": lambda self, x: None})()
        return cmd

    def _get_scraper(self):
        from apps.importer.scrapers.zego import ZegoScraper

        return ZegoScraper()

    def test_cleans_highlight_html(self):
        cmd = self._get_command()
        scraper = self._get_scraper()
        data = {
            "highlight": "<p>Great tour highlights</p>",
            "highlight_th": "<p>จุดเด่นทัวร์ยอดเยี่ยม</p>",
            "_itinerary": [],
        }
        result = cmd._sanitize_tour_data(data, scraper)
        assert "<p>" not in result["highlight"]
        assert "Great tour highlights" in result["highlight"]

    def test_cleans_itinerary_descriptions(self):
        cmd = self._get_command()
        scraper = self._get_scraper()
        data = {
            "highlight": "",
            "_itinerary": [
                {
                    "description": '<div class="ql-editor">Day 1 Bangkok</div>',
                    "description_th": "<p>วันที่ 1 กรุงเทพ</p>",
                }
            ],
        }
        result = cmd._sanitize_tour_data(data, scraper)
        day = result["_itinerary"][0]
        assert "<div" not in day["description"]
        assert "Day 1 Bangkok" in day["description"]

    def test_removes_junk_from_highlight(self):
        cmd = self._get_command()
        scraper = self._get_scraper()
        data = {
            "highlight": "ไฮไลท์ดี × ส่งโปรแกรมทัวร์ Email ผู้รับ Close Send",
            "_itinerary": [],
        }
        result = cmd._sanitize_tour_data(data, scraper)
        assert "ส่งโปรแกรมทัวร์" not in result["highlight"]
        assert "ไฮไลท์ดี" in result["highlight"]

    def test_empty_fields_unchanged(self):
        cmd = self._get_command()
        scraper = self._get_scraper()
        data = {
            "highlight": "",
            "description": None,
            "_itinerary": [],
        }
        result = cmd._sanitize_tour_data(data, scraper)
        assert result["highlight"] == ""
        assert result["description"] is None


@pytest.mark.django_db
class TestImageSync:
    """Tests for _upsert_images() syncing (add new, remove stale)."""

    def _get_command(self):
        from apps.importer.management.commands.scrape_tours import Command

        cmd = Command()
        cmd.stdout = type("obj", (object,), {"write": lambda self, x: None})()
        return cmd

    def test_adds_new_images(self, tour):
        cmd = self._get_command()
        cmd._upsert_images(tour, ["https://example.com/img1.jpg"])
        assert tour.images.count() == 1

    def test_removes_stale_images(self, tour):
        from apps.tours.models import TourImage

        # Add initial image
        TourImage.objects.create(
            tour=tour, image_url="https://old.com/old.jpg", sort_order=0
        )
        assert tour.images.count() == 1

        # Sync with different images
        cmd = self._get_command()
        cmd._upsert_images(tour, ["https://new.com/new.jpg"])

        assert tour.images.count() == 1
        assert tour.images.first().image_url == "https://new.com/new.jpg"

    def test_no_duplicates_on_same_url(self, tour):
        """Syncing same URL twice does not create duplicates."""
        cmd = self._get_command()
        cmd._upsert_images(tour, ["https://example.com/img.jpg"])
        cmd._upsert_images(tour, ["https://example.com/img.jpg"])
        assert tour.images.count() == 1

    def test_empty_url_filtered(self, tour):
        """Empty strings are ignored."""
        cmd = self._get_command()
        cmd._upsert_images(tour, ["", "https://example.com/img.jpg", ""])
        assert tour.images.count() == 1

    def test_sort_order_updated(self, tour):
        from apps.tours.models import TourImage

        TourImage.objects.create(
            tour=tour, image_url="https://example.com/img.jpg", sort_order=5
        )
        cmd = self._get_command()
        cmd._upsert_images(tour, ["https://example.com/img.jpg"])
        assert tour.images.first().sort_order == 0
