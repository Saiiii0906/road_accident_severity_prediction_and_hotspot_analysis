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
    """

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
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

    # Multi-Provider Routing
    LLM_PRIMARY_PROVIDER: str = "gemini"

    # Gemini Provider Settings
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-3.6-flash"

    # Claude Provider Settings
    CLAUDE_API_KEY: str | None = None
    CLAUDE_MODEL: str = "claude-3-7-sonnet-20250219"

    # Common LLM Settings
    LLM_TEMPERATURE: float = 0.2
    LLM_TIMEOUT_SECONDS: float = 60.0
    LLM_MAX_RETRIES: int = 2
    LLM_RETRY_BASE_DELAY: float = 1.0
    LLM_RETRY_MAX_DELAY: float = 4.0

    # Geocoding Provider Settings
    GEOCODING_PROVIDER: str = "nominatim"
    GEOCODING_BASE_URL: str = "https://nominatim.openstreetmap.org/search"
    GEOCODING_USER_AGENT: str = (
        "Mozilla/5.0 (compatible; RoadSafetyAnalytics/1.0; +https://example.com/safety-analytics)"
    )
    GEOCODING_TIMEOUT_SECONDS: float = 10.0

    # Routing Provider Settings
    ROUTING_PROVIDER: str = "osrm"
    ROUTING_BASE_URL: str = "https://router.project-osrm.org/route/v1/driving"
    ROUTING_TIMEOUT_SECONDS: float = 15.0

    # Weather Provider Settings (Open-Meteo)
    WEATHER_PROVIDER: str = "open-meteo"
    WEATHER_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"
    WEATHER_TIMEOUT_SECONDS: float = 10.0

    # Traffic Provider Settings (TfL / Open Corridor Feeds)
    TRAFFIC_PROVIDER: str = "tfl"
    TRAFFIC_BASE_URL: str = "https://api.tfl.gov.uk/Road"
    TRAFFIC_TIMEOUT_SECONDS: float = 10.0

    # Road Incident Provider Settings (TfL / Disruptions)
    INCIDENT_PROVIDER: str = "tfl"
    INCIDENT_BASE_URL: str = "https://api.tfl.gov.uk/Road/all/Disruption"
    INCIDENT_TIMEOUT_SECONDS: float = 10.0

    # Historical Model Corridor Matching Settings (Phase 4C)
    HISTORICAL_CORRIDOR_RADIUS_METERS: float = 1000.0
    HISTORICAL_COVERAGE_BOUNDS: tuple[float, float, float, float] = (50.0, 60.5, -6.5, 2.0)

    @property
    def BASE_DIR(self) -> Path:
        """Directory containing this config file (backend/app/)."""
        return Path(__file__).resolve().parent

    @property
    def PROJECT_ROOT(self) -> Path:
        """Root workspace directory."""
        return self.BASE_DIR.parent.parent

    @property
    def MOCK_DATA_DIR(self) -> Path:
        """Directory containing mock JSON fixtures (backend/app/mock_data/)."""
        return self.BASE_DIR / "mock_data"

    @property
    def STUDENT_A_MODELS_DIR(self) -> Path:
        """Directory containing Student A model artifacts."""
        return self.PROJECT_ROOT / "student_A" / "models"

    @property
    def STUDENT_A_MODEL_PATH(self) -> Path:
        """Path to Student A Random Forest model binary."""
        return self.STUDENT_A_MODELS_DIR / "accident_severity_model.pkl"

    @property
    def STUDENT_A_ENCODER_PATH(self) -> Path:
        """Path to Student A LabelEncoder binary."""
        return self.STUDENT_A_MODELS_DIR / "severity_encoder.pkl"

    @property
    def STUDENT_A_FEATURES_PATH(self) -> Path:
        """Path to Student A 138-features list pickle."""
        return self.STUDENT_A_MODELS_DIR / "features.pkl"

    STUDENT_B_HOTSPOT_PATH_ENV: str | None = Field(
        default=None,
        alias="STUDENT_B_HOTSPOT_PATH",
    )

    @property
    def STUDENT_B_HOTSPOT_PATH(self) -> Path:
        """Path to Student B DBSCAN hotspot summary CSV."""
        if self.STUDENT_B_HOTSPOT_PATH_ENV:
            p = Path(self.STUDENT_B_HOTSPOT_PATH_ENV)
            return p if p.is_absolute() else self.PROJECT_ROOT / p
        default_path = self.PROJECT_ROOT / "data" / "output" / "hotspot_summary.csv"
        if default_path.exists():
            return default_path
        return self.PROJECT_ROOT / "student_B" / "results" / "hotspot_summary.csv"

    STUDENT_C_RISK_PATH_ENV: str | None = Field(
        default=None,
        alias="STUDENT_C_RISK_PATH",
    )

    @property
    def STUDENT_C_RISK_PATH(self) -> Path:
        """Path to Student C GNN road risk predictions JSON."""
        if self.STUDENT_C_RISK_PATH_ENV:
            p = Path(self.STUDENT_C_RISK_PATH_ENV)
            return p if p.is_absolute() else self.PROJECT_ROOT / p
        return self.PROJECT_ROOT / "student_C" / "gnn_risk_predictions.json"


@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings instance."""
    return Settings()


settings = get_settings()