import json
import logging
from pathlib import Path
from typing import Type, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=BaseModel)

# app/services/base_service.py -> parent is app/services -> parent.parent is app/
DEFAULT_MOCK_DATA_DIR = Path(__file__).resolve().parent.parent / "mock_data"


class MockDataUnavailableError(RuntimeError):
    """Internal error raised when a mock fixture is missing, unreadable,
    not valid JSON, or fails Pydantic validation.

    This never escapes the service layer. `_load_and_parse` catches it and
    converts it into an `HTTPException`, so routes only ever see one of:
    a valid response model, or an `HTTPException`.
    """


class BaseMockService:
    """Base class providing fixture loading for mock service implementations.

    Subclasses get two building blocks:
      * `_load_and_parse(filename, model_cls)` — for fixtures that map
        1:1 to a single response model.
      * `_load_and_parse_section(filename, section_key, model_cls)` — for
        fixtures that bundle several response models under one JSON file
        (e.g. report.json holding both "summary" and "export").

    Both raise `HTTPException(500)` on any failure. Callers do not need
    their own try/except blocks around these calls.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize the service with a mock data directory.

        Args:
            data_dir: Directory containing mock JSON fixtures. Defaults to
                `app/mock_data`. Overridable so tests can point at fixture
                directories without touching the real ones.
        """
        self._data_dir = data_dir or DEFAULT_MOCK_DATA_DIR

    def _load_and_parse(self, filename: str, model_cls: Type[ModelT]) -> ModelT:
        """Read a JSON fixture and validate it against `model_cls`.

        Args:
            filename: Name of the JSON file inside the mock data directory.
            model_cls: Pydantic model the file's contents must satisfy.

        Returns:
            A validated instance of `model_cls`.

        Raises:
            HTTPException: 500 if the file is missing, unreadable, not
                valid JSON, or fails validation against `model_cls`.
        """
        try:
            data = self._read_json_file(filename)
            return self._parse_model(model_cls, data)
        except MockDataUnavailableError as exc:
            raise self._service_unavailable(exc) from exc

    def _load_and_parse_section(
        self, filename: str, section_key: str, model_cls: Type[ModelT]
    ) -> ModelT:
        """Read a JSON fixture, pull out one top-level section, and validate it.

        Use this when a single fixture file holds data for more than one
        response model (e.g. a report fixture with "summary" and "export"
        keys), so each logical response still gets its own fixture entry
        without needing a separate file per method.

        Args:
            filename: Name of the JSON file inside the mock data directory.
            section_key: Top-level key whose value should be validated.
            model_cls: Pydantic model the section's contents must satisfy.

        Returns:
            A validated instance of `model_cls`.

        Raises:
            HTTPException: 500 if the file is missing, unreadable, not
                valid JSON, missing `section_key`, or the section fails
                validation against `model_cls`.
        """
        try:
            data = self._read_json_file(filename)
            section = self._extract_section(data, filename, section_key)
            return self._parse_model(model_cls, section)
        except MockDataUnavailableError as exc:
            raise self._service_unavailable(exc) from exc

    def _read_json_file(self, filename: str) -> dict | list:
        """Read and JSON-decode a fixture file.

        Raises:
            MockDataUnavailableError: if the file does not exist or its
                contents are not valid JSON.
        """
        file_path = self._data_dir / filename
        try:
            raw_text = file_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            logger.error("Mock data file not found: %s", file_path)
            raise MockDataUnavailableError(
                f"Mock data file not found: {file_path}"
            ) from exc

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.error("Mock data file %s is not valid JSON: %s", file_path, exc)
            raise MockDataUnavailableError(
                f"Mock data file {file_path} is not valid JSON"
            ) from exc

    @staticmethod
    def _extract_section(data: dict | list, filename: str, section_key: str) -> dict:
        """Pull a named top-level section out of a decoded fixture.

        Raises:
            MockDataUnavailableError: if `data` is not a dict or does not
                contain `section_key`.
        """
        if not isinstance(data, dict) or section_key not in data:
            logger.error(
                "Mock data file %s is missing expected section '%s'",
                filename,
                section_key,
            )
            raise MockDataUnavailableError(
                f"Mock data file {filename} is missing expected section "
                f"'{section_key}'"
            )
        return data[section_key]

    @staticmethod
    def _parse_model(model_cls: Type[ModelT], data: dict | list) -> ModelT:
        """Validate raw data against a Pydantic model.

        Raises:
            MockDataUnavailableError: if `data` fails validation.
        """
        try:
            return model_cls.model_validate(data)
        except ValidationError as exc:
            logger.error(
                "Mock data failed validation against %s: %s",
                model_cls.__name__,
                exc,
            )
            raise MockDataUnavailableError(
                f"Mock data failed validation against {model_cls.__name__}"
            ) from exc

    @staticmethod
    def _service_unavailable(exc: MockDataUnavailableError) -> HTTPException:
        """Build the HTTPException returned when mock data cannot be served.

        A broken or missing fixture is a server-side problem, not something
        the caller did wrong, so this always maps to 500 regardless of
        which endpoint triggered it. The original exception is logged
        elsewhere with full detail; the client only sees a generic message.
        """
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "This service is temporarily unavailable due to a data "
                "provisioning error. Please try again later."
            ),
        )