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
def sync_all_tours(sources=None):
    """Run tour scrapers sequentially. Scheduled twice daily.

    Args:
        sources: list of source names to sync (default: all sources)
    """
    targets = [s for s in SOURCES if sources is None or s["source"] in sources]
    logger.info("Starting tour sync for sources: %s", [s["source"] for s in targets])
    results = {}

    for src in targets:
        source_name = src["source"]
        try:
            logger.info("Syncing %s...", source_name)
            call_command("scrape_tours", source=source_name, publish=True, verbosity=1)
            results[source_name] = "ok"
            logger.info("Finished %s", source_name)
        except Exception as e:
            results[source_name] = f"error: {e}"
            logger.exception("Failed to sync %s", source_name)

    logger.info("Tour sync complete: %s", results)
    return results
