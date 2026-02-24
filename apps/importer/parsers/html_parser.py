"""HTML parser — extracts tables from HTML files or web pages."""

import logging

from .base import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class HtmlParser(BaseParser):
    """Parse HTML content, extracting tables into structured row data."""

    def parse_file(self, file_path_or_buffer) -> ParseResult:
        """Parse an HTML file."""
        try:
            if isinstance(file_path_or_buffer, (str,)):
                # File path
                with open(file_path_or_buffer, "r", encoding="utf-8") as f:
                    html_content = f.read()
            else:
                # File-like object
                raw = file_path_or_buffer.read()
                if isinstance(raw, bytes):
                    html_content = raw.decode("utf-8")
                else:
                    html_content = raw

            return self._parse_html(html_content)
        except Exception as e:
            return ParseResult(errors=[f"Failed to parse HTML file: {e}"])

    def parse_url(self, url) -> ParseResult:
        """Fetch and parse an HTML page from a URL."""
        import urllib.request

        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "SmileMemory-Importer/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                html_content = response.read().decode("utf-8")
            return self._parse_html(html_content, source_url=url)
        except Exception as e:
            return ParseResult(errors=[f"Failed to fetch URL {url}: {e}"])

    def _parse_html(self, html_content, source_url="") -> ParseResult:
        """Extract tables from HTML content using BeautifulSoup."""
        from bs4 import BeautifulSoup

        errors = []
        all_rows = []
        headers = []

        soup = BeautifulSoup(html_content, "lxml")
        tables = soup.find_all("table")

        if not tables:
            errors.append("No <table> elements found in HTML.")
            return ParseResult(headers=headers, rows=all_rows, errors=errors)

        # Use the largest table (most rows)
        best_table = max(tables, key=lambda t: len(t.find_all("tr")))

        rows = best_table.find_all("tr")
        for row_idx, tr in enumerate(rows):
            cells = tr.find_all(["th", "td"])
            values = [self._clean_value(cell.get_text()) for cell in cells]

            if row_idx == 0 and not headers:
                # First row = headers
                headers = [self._clean_header(v) for v in values]
                continue

            # Skip empty rows
            if all(not v for v in values):
                continue

            row_dict = {}
            for j, value in enumerate(values):
                if j < len(headers) and headers[j]:
                    row_dict[headers[j]] = value
            all_rows.append(row_dict)

        metadata = {"format": "html", "tables_found": len(tables)}
        if source_url:
            metadata["source_url"] = source_url

        logger.info("HTML parsed: %d headers, %d rows", len(headers), len(all_rows))
        return ParseResult(
            headers=headers,
            rows=all_rows,
            errors=errors,
            metadata=metadata,
        )
