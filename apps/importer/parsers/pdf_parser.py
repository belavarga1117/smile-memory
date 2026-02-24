"""PDF file parser using pdfplumber — extracts tables from PDF tour documents."""

import logging

from .base import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class PdfParser(BaseParser):
    """Parse PDF files, extracting tables into structured row data."""

    def parse_file(self, file_path_or_buffer) -> ParseResult:
        import pdfplumber

        errors = []
        all_rows = []
        headers = []

        try:
            pdf = pdfplumber.open(file_path_or_buffer)
        except Exception as e:
            return ParseResult(errors=[f"Failed to open PDF: {e}"])

        try:
            for page_num, page in enumerate(pdf.pages, 1):
                tables = page.extract_tables()
                if not tables:
                    continue

                for table in tables:
                    if not table:
                        continue

                    for row_idx, row in enumerate(table):
                        # First row of first table = headers (if we don't have them yet)
                        if not headers and row_idx == 0:
                            headers = [self._clean_header(cell) for cell in row]
                            continue

                        # Skip if this row looks like a repeated header
                        cleaned_row = [self._clean_value(cell) for cell in row]
                        if cleaned_row == headers:
                            continue

                        # Skip empty rows
                        if all(not cell for cell in cleaned_row):
                            continue

                        row_dict = {}
                        for j, value in enumerate(cleaned_row):
                            if j < len(headers) and headers[j]:
                                row_dict[headers[j]] = value
                        all_rows.append(row_dict)

            # If no tables found, try extracting text as fallback
            if not all_rows:
                text_lines = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_lines.extend(text.strip().split("\n"))

                if text_lines:
                    errors.append("No tables found in PDF. Raw text extracted instead.")
                    headers = ["line_number", "text"]
                    for i, line in enumerate(text_lines, 1):
                        line = line.strip()
                        if line:
                            all_rows.append({"line_number": i, "text": line})
                else:
                    errors.append("No tables or text found in PDF.")

        finally:
            pdf.close()

        logger.info(
            "PDF parsed: %d headers, %d rows from PDF", len(headers), len(all_rows)
        )
        return ParseResult(
            headers=headers,
            rows=all_rows,
            errors=errors,
            metadata={
                "pages": len(pdf.pages) if hasattr(pdf, "pages") else 0,
                "format": "pdf",
            },
        )
