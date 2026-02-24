from .excel_parser import ExcelParser
from .csv_parser import CsvParser
from .pdf_parser import PdfParser
from .html_parser import HtmlParser

PARSERS = {
    "excel": ExcelParser,
    "csv": CsvParser,
    "pdf": PdfParser,
    "html": HtmlParser,
}


def get_parser(file_format):
    """Return the appropriate parser class for the given format."""
    parser_class = PARSERS.get(file_format)
    if not parser_class:
        raise ValueError(f"Unsupported file format: {file_format}")
    return parser_class()
