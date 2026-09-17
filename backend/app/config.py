from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    database_url: str = "sqlite:///./data/leads.db"
    discovery_provider: str = "mock"
    google_maps_api_key: str = ""

    search_city: str = ""
    search_country: str = "Italy"
    search_postal_code: str = ""
    search_latitude: float | None = None
    search_longitude: float | None = None
    search_radius_km: float = 10.0

    @field_validator("search_latitude", "search_longitude", mode="before")
    @classmethod
    def empty_coord_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value

    max_results_per_query: int = 40
    request_timeout_seconds: float = 10.0
    crawl_max_pages_per_domain: int = 4
    crawl_delay_seconds: float = 1.0
    http_user_agent: str = "LeadFinder/1.0 (+local-research; respect-robots)"
    job_poll_seconds: float = 1.0

    config_dir: Path = Field(default_factory=lambda: ROOT_DIR / "config")
    data_dir: Path = Field(default_factory=lambda: ROOT_DIR / "data")
    frontend_dist: Path = Field(default_factory=lambda: ROOT_DIR / "frontend" / "dist")

    @property
    def scoring_path(self) -> Path:
        return self.config_dir / "scoring.yaml"

    @property
    def categories_path(self) -> Path:
        return self.config_dir / "categories.yaml"

    @property
    def location_path(self) -> Path:
        return self.config_dir / "location.yaml"

    @property
    def sqlite_path(self) -> Path:
        if self.database_url.startswith("sqlite:///"):
            raw = self.database_url.removeprefix("sqlite:///")
            path = Path(raw)
            if not path.is_absolute():
                path = ROOT_DIR / path
            return path
        return self.data_dir / "leads.db"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
