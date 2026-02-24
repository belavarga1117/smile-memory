"""Base parser interface for all import formats."""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ParseResult:
    """Container for parsed data from any source."""

    def __init__(self, headers=None, rows=None, errors=None, metadata=None):
        self.headers = headers or []
        self.rows = rows or []  # List of dicts
        self.errors = errors or []
        self.metadata = metadata or {}

    @property
    def total_rows(self):
        return len(self.rows)

    @property
    def preview(self, max_rows=10):
        """Return first N rows for admin preview."""
        return self.rows[:max_rows]


class BaseParser(ABC):
    """Abstract base for all file format parsers."""

    @abstractmethod
    def parse_file(self, file_path_or_buffer) -> ParseResult:
        """Parse a file and return structured data.

        Args:
            file_path_or_buffer: File path string or file-like object.

        Returns:
            ParseResult with headers, rows (list of dicts), and any errors.
        """
        ...

    def parse_url(self, url) -> ParseResult:
        """Parse content from a URL. Override in subclasses that support it."""
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support URL parsing"
        )

    def _clean_value(self, value):
        """Clean a cell value — strip strings, normalize None."""
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return value

    def _clean_header(self, header):
        """Normalize a header name for mapping."""
        if not header:
            return ""
        return str(header).strip().lower().replace(" ", "_").replace("-", "_")
