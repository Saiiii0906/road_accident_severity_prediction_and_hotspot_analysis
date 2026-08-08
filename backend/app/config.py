from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration.

    Values are resolved in this order (highest priority first):
      1. Actual environment variables
      2. Values in a .env file at the backend/app/ directory (if present)
      3. The defaults declared below

    Only APP_NAME, APP_VERSION, ENVIRONMENT, and LOG_LEVEL are expected to
    be overridden via environment variables in normal use; the other
    fields are still technically overridable (pydantic-settings does not
    special-case them) but are not part of the supported configuration
    surface at this stage of the project.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


    APP_NAME: str = "Road Accident Severity Prediction & Hotspot Analysis"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    API_PREFIX: str = "/api"

    API_DESCRIPTION: str = (
        "API for predicting road accident severity, identifying accident "
        "hotspots, assessing location-based risk, and generating accident "
        "reports."
    )


    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    
    LOG_LEVEL: str = "INFO"

    @property
    def BASE_DIR(self) -> Path:
        """Directory containing this config file (backend/app/).

        Deliberately a property rather than a pydantic field: fields can
        be overridden by environment variables, and a stray BASE_DIR
        env var would silently break every path derived from it. Always
        computing this from `__file__` is what makes the project portable
        across machines instead of depending on where it happens to be
        checked out.
        """
        return Path(__file__).resolve().parent

    @property
    def MOCK_DATA_DIR(self) -> Path:
        """Directory containing mock JSON fixtures (backend/app/mock_data/).

        Also a property, for the same reason as BASE_DIR: it must always
        be derived, never accidentally overridden via the environment.
        """
        return self.BASE_DIR / "mock_data"


@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings instance.

    Wrapped in lru_cache so Settings is constructed once per process and
    can be used as a FastAPI dependency (`Depends(get_settings)`) without
    re-reading the environment or .env file on every request.
    """
    return Settings()

settings = get_settings()