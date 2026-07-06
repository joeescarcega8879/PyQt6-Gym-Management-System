"""
Tests for src/utils/pdf_exporter.py.

No mocking of reportlab — the only honest way to verify PDF generation is
to actually generate one and inspect the resulting file.
"""
from src.utils.pdf_exporter import export_table_report


class TestExportTableReport:
    def test_creates_a_valid_pdf_file(self, tmp_path):
        file_path = tmp_path / "report.pdf"

        export_table_report(
            file_path=str(file_path),
            title="Financial Report",
            summary_lines=["Total Revenue: $100.00", "Transactions: 2"],
            headers=["Member", "Amount"],
            rows=[["Jane Doe", "$50.00"], ["John Smith", "$50.00"]],
        )

        assert file_path.exists()
        assert file_path.stat().st_size > 0
        with open(file_path, "rb") as f:
            assert f.read(5) == b"%PDF-"

    def test_works_with_no_summary_lines(self, tmp_path):
        file_path = tmp_path / "report_no_summary.pdf"

        export_table_report(
            file_path=str(file_path),
            title="Membership Report",
            summary_lines=[],
            headers=["Status", "Count"],
            rows=[["active", "10"]],
        )

        assert file_path.exists()
        assert file_path.stat().st_size > 0

    def test_works_with_empty_rows(self, tmp_path):
        file_path = tmp_path / "report_empty.pdf"

        export_table_report(
            file_path=str(file_path),
            title="Attendance Report",
            summary_lines=["Total Check-ins: 0"],
            headers=["Hour", "Count"],
            rows=[],
        )

        assert file_path.exists()
        assert file_path.stat().st_size > 0
