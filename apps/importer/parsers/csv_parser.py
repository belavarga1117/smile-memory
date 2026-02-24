"""CSV file parser using Python's built-in csv module."""

import csv
import io
import logging

from .base import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class CsvParser(BaseParser):
    """Parse CSV files into structured row data."""

    def parse_file(
        self, file_path_or_buffer, encoding="utf-8", delimiter=None
    ) -> ParseResult:
        errors = []

        try:
            # Handle both file paths and file-like objects
            if isinstance(file_path_or_buffer, (str, bytes)):
                if isinstance(file_path_or_buffer, bytes):
                    text = file_path_or_buffer.decode(encoding)
                else:
                    with open(file_path_or_buffer, "r", encoding=encoding) as f:
                        text = f.read()
            else:
                # File-like object (e.g., Django UploadedFile)
                raw = file_path_or_buffer.read()
                if isinstance(raw, bytes):
                    text = raw.decode(encoding)
                else:
                    text = raw

            # Auto-detect delimiter if not specified
            if delimiter is None:
                sniffer = csv.Sniffer()
                try:
                    dialect = sniffer.sniff(text[:2048])
                    delimiter = dialect.delimiter
                except csv.Error:
                    delimiter = ","

            reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
            headers = [self._clean_header(h) for h in (reader.fieldnames or [])]

            rows_data = []
            for i, row in enumerate(reader):
                # Re-key with cleaned headers
                cleaned = {}
                for orig_key, clean_key in zip(reader.fieldnames or [], headers):
                    if clean_key:
                        cleaned[clean_key] = self._clean_value(row.get(orig_key))
                rows_data.append(cleaned)

        except UnicodeDecodeError:
            # Retry with latin-1 if UTF-8 fails
            if encoding == "utf-8":
                logger.warning("UTF-8 decode failed, retrying with latin-1")
                return self.parse_file(
                    file_path_or_buffer, encoding="latin-1", delimiter=delimiter
                )
            return ParseResult(
                errors=[f"Failed to decode CSV with encoding {encoding}"]
            )
        except Exception as e:
            return ParseResult(errors=[f"Failed to parse CSV: {e}"])

        logger.info("CSV parsed: %d headers, %d rows", len(headers), len(rows_data))
        return ParseResult(
            headers=headers,
            rows=rows_data,
            errors=errors,
            metadata={"delimiter": delimiter, "encoding": encoding, "format": "csv"},
        )
