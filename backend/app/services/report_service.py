import logging
import uuid

from app.schemas.report import (
    ReportExportRequest,
    ReportExportResponse,
    ReportFilterParams,
    ReportFormat,
    ReportSummaryResponse,
)
from app.services.base_service import BaseMockService

logger = logging.getLogger(__name__)

_MOCK_FILE = "report.json"
_SUMMARY_SECTION = "summary"
_EXPORT_SECTION = "export"
_DOWNLOAD_BASE_URL = "https://example.com/reports"


class ReportService(BaseMockService):
    """Provides accident report summaries and exports.

    Mock implementation: summary statistics and export metadata are
    loaded from mock_data/report.json, with request-derived fields
    (filters, format, report_id, download_url) overlaid on top. A real
    implementation should replace this class while keeping `get_summary`
    and `export` with the same signatures.
    """

    def get_summary(self, filters: ReportFilterParams) -> ReportSummaryResponse:
        """Return aggregate accident statistics for the requested filters.

        Args:
            filters: Validated date range and optional local authority
                filter. Echoed into the response's `filters` field;
                does not affect the mock statistics themselves.

        Returns:
            A ReportSummaryResponse whose `filters` reflect the request,
            with mock aggregate statistics.

        Raises:
            HTTPException: 500 if the mock fixture is missing, unreadable,
                missing the "summary" section, or fails schema validation.
        """
        logger.debug(
            "Serving mock report summary for %s to %s",
            filters.date_from,
            filters.date_to,
        )
        template = self._load_and_parse_section(
            _MOCK_FILE, _SUMMARY_SECTION, ReportSummaryResponse
        )
        return template.model_copy(update={"filters": filters})

    def export(self, request: ReportExportRequest) -> ReportExportResponse:
        """Generate a downloadable report file reference.

        Args:
            request: Validated filters and desired output format.

        Returns:
            A ReportExportResponse with a freshly generated `report_id`,
            `format` matching the request, and a `download_url` whose
            extension matches that format.

        Raises:
            HTTPException: 500 if the mock fixture is missing, unreadable,
                missing the "export" section, or fails schema validation.
        """
        logger.debug("Serving mock report export in %s format", request.format.value)
        template = self._load_and_parse_section(
            _MOCK_FILE, _EXPORT_SECTION, ReportExportResponse
        )
        report_id = self._generate_report_id()
        download_url = self._build_download_url(report_id, request.format)
        return template.model_copy(
            update={
                "report_id": report_id,
                "format": request.format,
                "download_url": download_url,
            }
        )

    @staticmethod
    def _generate_report_id() -> str:
        """Generate a unique identifier for a single export call."""
        return f"mock-report-{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _build_download_url(report_id: str, report_format: ReportFormat) -> str:
        """Build a download URL whose extension matches `report_format`.

        Kept as its own helper (rather than inlined) so the extension
        mapping has one place to change if the real file-serving
        implementation uses a different URL scheme.
        """
        return f"{_DOWNLOAD_BASE_URL}/{report_id}.{report_format.value}"