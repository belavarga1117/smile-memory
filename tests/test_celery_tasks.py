"""Celery task tests — run in EAGER mode (no broker needed)."""

from unittest.mock import patch

import pytest

from apps.importer.tasks import sync_all_tours, SOURCES


@pytest.mark.django_db
class TestSyncAllToursTask:
    """Test the daily sync task that runs all 4 scrapers."""

    @patch("apps.importer.tasks.call_command")
    def test_calls_all_sources(self, mock_call_command):
        result = sync_all_tours()

        assert mock_call_command.call_count == len(SOURCES)
        # Verify call_command is called with scrape_tours for each source
        for call in mock_call_command.call_args_list:
            assert call.args[0] == "scrape_tours"

        assert result == {
            "zego": "ok",
            "go365": "ok",
            "realjourney": "ok",
            "gs25": "ok",
        }

    @patch("apps.importer.tasks.call_command")
    def test_partial_failure_continues(self, mock_call_command):
        """If one scraper fails, others should still run."""

        def side_effect(*args, **kwargs):
            if kwargs.get("source") == "go365":
                raise ConnectionError("API timeout")

        mock_call_command.side_effect = side_effect
        result = sync_all_tours()

        # All sources should be attempted
        assert mock_call_command.call_count == len(SOURCES)
        assert result["zego"] == "ok"
        assert "error" in result["go365"]
        assert result["realjourney"] == "ok"
        assert result["gs25"] == "ok"

    @patch("apps.importer.tasks.call_command")
    def test_all_failures_returns_errors(self, mock_call_command):
        mock_call_command.side_effect = Exception("DB down")
        result = sync_all_tours()

        assert all("error" in v for v in result.values())

    @patch("apps.importer.tasks.call_command")
    def test_publish_flag_passed(self, mock_call_command):
        """Verify publish=True is passed to scrape_tours."""
        sync_all_tours()

        for call in mock_call_command.call_args_list:
            assert call.kwargs.get("publish") is True

    def test_sources_list_complete(self):
        """Verify all expected sources are in SOURCES constant."""
        source_names = [s["source"] for s in SOURCES]
        assert "zego" in source_names
        assert "go365" in source_names
        assert "realjourney" in source_names
        assert "gs25" in source_names
