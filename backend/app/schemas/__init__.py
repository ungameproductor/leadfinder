from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class PlaceCandidate(BaseModel):
    external_id: str
    name: str
    category: str | None = None
    address: str | None = None
    city: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    website: str | None = None
    provider: str = "mock"


class PlaceDetails(PlaceCandidate):
    types: list[str] = Field(default_factory=list)
    raw_status: str | None = None


class SearchRequest(BaseModel):
    city: str = Field(min_length=2)
    country: str = "Italy"
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius_km: float = Field(default=10, ge=1, le=80)
    categories: list[str] = Field(default_factory=list)
    max_results: int = 40
    provider: str | None = None
    verify_websites: bool = True

    @field_validator("city", mode="before")
    @classmethod
    def strip_city(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("postal_code", mode="before")
    @classmethod
    def empty_cap(cls, value: object) -> object:
        if value == "":
            return None
        return value


class LeadPatch(BaseModel):
    category: str | None = None
    notes: str | None = None
    priority: str | None = None
    manual_status: str | None = None
    contact_status: str | None = None
    suggested_service: str | None = None


class LeadOut(BaseModel):
    id: str
    source_provider: str
    source_external_id: str | None
    name: str
    category: str | None
    address: str | None
    city: str | None
    postal_code: str | None
    latitude: float | None
    longitude: float | None
    phone: str | None
    website: str | None
    public_email: str | None
    email_source_url: str | None
    website_status: str
    website_quality_score: int | None
    website_quality_evidence: list[str] = Field(default_factory=list)
    email_status: str
    lead_score: int
    priority: str
    suggested_service: str | None
    notes: str | None
    scoring_evidence: list[str] = Field(default_factory=list)
    match_confidence: float
    phase_status: str
    first_seen_at: datetime | None
    last_checked_at: datetime | None
    manual_status: str
    contact_status: str
    quality_data_insufficient: bool
    is_new: bool | None = None

    model_config = {"from_attributes": True}


class RunOut(BaseModel):
    id: str
    kind: str
    provider: str
    query: str | None
    city: str | None
    postal_code: str | None
    latitude: float | None
    longitude: float | None
    radius_km: float | None
    categories: list[str] = Field(default_factory=list)
    status: str
    results_count: int
    processed_count: int
    errors: list[str] = Field(default_factory=list)
    api_usage: dict = Field(default_factory=dict)
    message: str | None
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class StatsOut(BaseModel):
    total: int
    priority_a: int
    priority_b: int
    priority_c: int
    no_website: int
    problematic_sites: int
    emails_found: int
    confirmed: int
    discarded: int
    do_not_contact: int
