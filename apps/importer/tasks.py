"""Celery tasks for automated tour import."""

import logging

from celery import shared_task
from django.core.management import call_command

logger = logging.getLogger(__name__)

SOURCES = [
    {"source": "zego"},
    {"source": "go365"},
    {"source": "realjourney"},
]


@shared_task(name="importer.sync_all_tours")
def sync_all_tours():
    """Run all tour scrapers sequentially. Scheduled daily at 15:00 ICT."""
    logger.info("Starting daily tour sync for all sources")
    results = {}

    for src in SOURCES:
        source_name = src["source"]
        try:
            logger.info("Syncing %s...", source_name)
            call_command("scrape_tours", source=source_name, publish=True, verbosity=1)
            results[source_name] = "ok"
            logger.info("Finished %s", source_name)
        except Exception as e:
            results[source_name] = f"error: {e}"
            logger.exception("Failed to sync %s", source_name)

    logger.info("Daily tour sync complete: %s", results)
    return results
