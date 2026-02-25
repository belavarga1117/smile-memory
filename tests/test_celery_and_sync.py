"""Tests for Celery tasks: sync_all_tours, validate_scrapers."""

import pytest
from unittest.mock import patch


class TestSyncAllTours:
    """Tests for importer.sync_all_tours Celery task."""

    def test_sync_all_tours_calls_scrape_command_per_source(self):
        """sync_all_tours runs scrape_tours command for each configured source."""
        from apps.importer.tasks import sync_all_tours

        with patch("apps.importer.tasks.call_command") as mock_cmd:
            sync_all_tours()

        assert mock_cmd.call_count == 4  # zego, go365, realjourney, gs25
        sources_called = [call.kwargs.get("source") for call in mock_cmd.call_args_list]
        assert "zego" in sources_called
        assert "go365" in sources_called
        assert "realjourney" in sources_called
        assert "gs25" in sources_called

    def test_sync_all_tours_filtered_by_source(self):
        """sync_all_tours with sources=[...] only runs those sources."""
        from apps.importer.tasks import sync_all_tours

        with patch("apps.importer.tasks.call_command") as mock_cmd:
            sync_all_tours(sources=["zego"])

        assert mock_cmd.call_count == 1
        assert mock_cmd.call_args.kwargs["source"] == "zego"

    def test_sync_all_tours_returns_results_dict(self):
        """sync_all_tours returns a dict with per-source results."""
        from apps.importer.tasks import sync_all_tours

        with patch("apps.importer.tasks.call_command"):
            result = sync_all_tours(sources=["zego"])

        assert isinstance(result, dict)
        assert "zego" in result
        assert result["zego"] == "ok"

    def test_sync_all_tours_handles_command_exception(self):
        """If one source fails, sync continues and records the error."""
        from apps.importer.tasks import sync_all_tours

        def fail_on_zego(*args, **kwargs):
            if kwargs.get("source") == "zego":
                raise Exception("Network timeout")

        with patch("apps.importer.tasks.call_command", side_effect=fail_on_zego):
            result = sync_all_tours(sources=["zego", "go365"])

        assert "error" in result["zego"]
        assert result["go365"] == "ok"

    def test_sync_all_tours_empty_sources_skips_all(self):
        """sync_all_tours with sources=[] runs nothing."""
        from apps.importer.tasks import sync_all_tours

        with patch("apps.importer.tasks.call_command") as mock_cmd:
            result = sync_all_tours(sources=[])

        assert mock_cmd.call_count == 0
        assert result == {}


class TestValidateScrapers:
    """Tests for importer.validate_scrapers Celery task."""

    def test_validate_scrapers_runs_command(self):
        from apps.importer.tasks import validate_scrapers

        with patch("apps.importer.tasks.call_command") as mock_cmd:
            result = validate_scrapers()

        mock_cmd.assert_called_once()
        assert result == {"status": "ok"}

    def test_validate_scrapers_with_source_filter(self):
        from apps.importer.tasks import validate_scrapers

        with patch("apps.importer.tasks.call_command") as mock_cmd:
            validate_scrapers(source="zego", sample=3)

        call_kwargs = mock_cmd.call_args.kwargs
        assert call_kwargs.get("source") == "zego"
        assert call_kwargs.get("sample") == 3

    def test_validate_scrapers_handles_exception(self):
        from apps.importer.tasks import validate_scrapers

        with patch(
            "apps.importer.tasks.call_command",
            side_effect=Exception("Scraper error"),
        ):
            result = validate_scrapers()

        assert result["status"] == "error"
        assert "Scraper error" in result["error"]


@pytest.mark.django_db
class TestImporterAdminActions:
    """Test importer admin trigger buttons and actions."""

    def test_import_job_admin_list_accessible(self, admin_client):
        resp = admin_client.get("/admin/importer/importjob/")
        assert resp.status_code == 200

    def test_import_job_admin_has_sync_button(self, admin_client):
        resp = admin_client.get("/admin/importer/importjob/")
        content = resp.content.decode()
        # The custom admin has a "Sync Now" / trigger button
        assert "sync" in content.lower() or "scrape" in content.lower()
