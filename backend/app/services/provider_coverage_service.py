"""
Provider Geographic Coverage & Eligibility Service.

Evaluates route geometry against upstream provider service domains
to deterministically enforce geographic scoping (e.g. TfL London-only,
historical models Great Britain-only) and avoid false incident/traffic reporting.
"""

import logging
from typing import Optional

from app.config import settings
from app.schemas.journey import ProviderCoverageStatus, RouteInfoSchema

logger = logging.getLogger(__name__)


class ProviderCoverageService:
    """Evaluates geographic eligibility and operational coverage for journey providers."""

    @staticmethod
    def extract_route_coordinates(route: RouteInfoSchema) -> list[list[float]]:
        """Extract [lon, lat] coordinates sequence from route geometry or endpoints."""
        if route.geometry and route.geometry.coordinates:
            return route.geometry.coordinates
        if route.source and route.destination:
            return [
                [route.source.longitude, route.source.latitude],
                [route.destination.longitude, route.destination.latitude],
            ]
        return []

    @classmethod
    def evaluate_route_bounds(
        cls, route: RouteInfoSchema, bounds: tuple[float, float, float, float]
    ) -> tuple[int, int]:
        """
        Count coordinates inside (min_lat, max_lat, min_lon, max_lon) bounding box.

        Returns:
            tuple[inside_count, total_count]
        """
        coords = cls.extract_route_coordinates(route)
        if not coords:
            return 0, 0

        min_lat, max_lat, min_lon, max_lon = bounds
        inside_count = sum(
            1 for lon, lat in coords if (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon)
        )
        return inside_count, len(coords)

    @classmethod
    def check_tfl_eligibility(
        cls,
        route: RouteInfoSchema,
        bounds: Optional[tuple[float, float, float, float]] = None,
    ) -> tuple[bool, ProviderCoverageStatus, str]:
        """
        Evaluate whether route is eligible for TfL (Transport for London) feeds.

        Returns:
            tuple[is_eligible, coverage_status, reason]
        """
        tfl_bounds = bounds or settings.TFL_COVERAGE_BOUNDS
        inside_count, total_count = cls.evaluate_route_bounds(route, tfl_bounds)

        if total_count == 0:
            return (
                False,
                ProviderCoverageStatus.UNSUPPORTED_FOR_GEOGRAPHY,
                "Route coordinates unavailable to evaluate TfL geographic eligibility.",
            )

        if inside_count == 0:
            logger.info("Route is completely outside Greater London (TfL service area).")
            return (
                False,
                ProviderCoverageStatus.UNSUPPORTED_FOR_GEOGRAPHY,
                "TfL traffic and disruption monitoring is unavailable: route lies outside Greater London.",
            )

        if inside_count == total_count:
            return (
                True,
                ProviderCoverageStatus.SUPPORTED,
                "Route is within Greater London (TfL service area).",
            )

        return (
            True,
            ProviderCoverageStatus.PARTIALLY_SUPPORTED,
            "Route partially traverses Greater London; TfL data applies to the London corridor portion only.",
        )

    @classmethod
    def check_historical_gb_eligibility(
        cls,
        route: RouteInfoSchema,
        bounds: Optional[tuple[float, float, float, float]] = None,
    ) -> tuple[bool, ProviderCoverageStatus, str]:
        """
        Evaluate whether route is eligible for UK historical road safety models.

        Returns:
            tuple[is_eligible, coverage_status, reason]
        """
        gb_bounds = bounds or settings.HISTORICAL_COVERAGE_BOUNDS
        inside_count, total_count = cls.evaluate_route_bounds(route, gb_bounds)

        if total_count == 0:
            return (
                False,
                ProviderCoverageStatus.UNSUPPORTED_FOR_GEOGRAPHY,
                "Route coordinates unavailable for historical coverage evaluation.",
            )

        if inside_count == 0:
            return (
                False,
                ProviderCoverageStatus.UNSUPPORTED_FOR_GEOGRAPHY,
                "Route lies outside Great Britain historical model coverage.",
            )

        if inside_count == total_count:
            return (
                True,
                ProviderCoverageStatus.SUPPORTED,
                "Route is within supported historical model coverage (Great Britain).",
            )

        return (
            True,
            ProviderCoverageStatus.PARTIALLY_SUPPORTED,
            "Route partially traverses supported historical model coverage (Great Britain).",
        )

