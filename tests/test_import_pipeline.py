"""Import pipeline integration tests — upsert idempotency, field mapping."""

import pytest

from apps.importer.models import ImportJob
from apps.importer.parsers.csv_parser import CsvParser
from apps.importer.pipeline import ImportPipeline
from apps.tours.models import Tour

from .factories import ImportJobFactory


@pytest.mark.django_db
class TestUpsertIdempotency:
    """The same product_code imported twice should update, not duplicate."""

    def test_second_import_updates_not_duplicates(self):
        import_job = ImportJobFactory()
        pipeline = ImportPipeline(import_job)

        mapping = {"name": "title", "code": "product_code", "desc": "description"}

        # First import
        row1 = {"name": "Japan Spring", "code": "JP-SPRING-01", "desc": "v1"}
        mapped1 = pipeline.mapper.map_row(row1, mapping)
        tour1, action1 = pipeline._upsert_tour(mapped1, row1)
        assert action1 == "created"

        # Second import with same product_code
        row2 = {"name": "Japan Spring Updated", "code": "JP-SPRING-01", "desc": "v2"}
        mapped2 = pipeline.mapper.map_row(row2, mapping)
        tour2, action2 = pipeline._upsert_tour(mapped2, row2)
        assert action2 == "updated"

        # Should be the same Tour object
        assert tour1.pk == tour2.pk
        assert Tour.objects.filter(product_code="JP-SPRING-01").count() == 1

        # Description should be updated
        tour2.refresh_from_db()
        assert tour2.description == "v2"

    def test_csv_import_end_to_end(self, tmp_path):
        import_job = ImportJobFactory()
        csv_content = (
            "tour_name,product_code,price,duration_days,destination\n"
            "Japan Cherry,CHERRY-01,35900,7,Japan\n"
            "Korea Autumn,KOREA-01,22900,4,Korea\n"
        )
        csv_file = tmp_path / "tours.csv"
        csv_file.write_text(csv_content)

        parser = CsvParser()
        result = parser.parse_file(str(csv_file))
        pipeline = ImportPipeline(import_job)
        mapping = pipeline.mapper.get_effective_mapping(result.headers)

        import_job.status = ImportJob.Status.IMPORTING
        import_job.save()

        for row_num, row_data in enumerate(result.rows, start=1):
            pipeline._process_row(row_num, row_data, mapping)

        assert pipeline.stats["created"] == 2
        assert Tour.objects.filter(product_code="CHERRY-01").exists()
        assert Tour.objects.filter(product_code="KOREA-01").exists()

    def test_skips_row_without_title_or_product_code(self):
        import_job = ImportJobFactory()
        pipeline = ImportPipeline(import_job)
        mapping = {"col": "description"}

        pipeline._process_row(1, {"col": "only description"}, mapping)
        assert pipeline.stats["skipped"] == 1
        assert pipeline.stats["created"] == 0
