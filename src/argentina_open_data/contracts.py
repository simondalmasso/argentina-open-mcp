"""Canonical, transport-neutral data contracts shared by REST, MCP and web."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ContractModel(BaseModel):
    """Base model: reject undeclared fields to keep public contracts predictable."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=True)


class GeoLevel(StrEnum):
    COUNTRY = "country"
    INDEC_REGION = "indec_region"
    PROVINCE = "province"
    DEPARTMENT = "department"
    MUNICIPALITY = "municipality"
    LOCALITY = "locality"
    CENSUS_TRACT = "census_tract"
    EPH_AGGLOMERATE = "eph_agglomerate"


class AggregationPolicy(StrEnum):
    SUM_ALLOWED = "sum_allowed"
    AGGLOMERATE_LOCKED = "agglomerate_locked"
    FIXED_REGIONS = "fixed_regions"
    OFFICIAL_ONLY = "official_only"
    COVERAGE_DECLARED = "coverage_declared"
    NOT_AGGREGATABLE = "not_aggregatable"


class QualityFlag(StrEnum):
    ESTIMATE = "estimate"
    PRELIMINARY = "preliminary"
    REVISED = "revised"
    IMPUTED = "imputed"
    SUPPRESSED = "suppressed"
    STALE = "stale"
    PARTIAL_COVERAGE = "partial_coverage"


class Coverage(ContractModel):
    """Describes the population or universe represented by a dataset."""

    scope: str = Field(min_length=1, max_length=500)
    population_share: Annotated[float, Field(ge=0, le=1)] | None = None
    note: str | None = Field(default=None, max_length=1000)


class Provenance(ContractModel):
    """Lineage for a returned dataset or observation batch."""

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{1,79}$")
    source_name: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl
    license_id: str = Field(min_length=1, max_length=100)
    retrieved_at: datetime
    published_at: datetime | None = None
    snapshot_sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    transform_chain: tuple[str, ...] = ()

    @field_validator("retrieved_at", "published_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("timestamps must include a timezone")
        return value


class IndicatorMetadata(ContractModel):
    indicator_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{1,119}$")
    name: str = Field(min_length=1, max_length=200)
    unit: str = Field(min_length=1, max_length=80)
    frequency: str = Field(min_length=1, max_length=40)
    available_geo_levels: tuple[GeoLevel, ...] = Field(min_length=1)
    aggregation_policy: AggregationPolicy
    coverage: Coverage
    provenance: Provenance
    comparability_warnings: tuple[str, ...] = ()


class Observation(ContractModel):
    period: str = Field(min_length=1, max_length=40)
    value: int | float | None
    geo_id: str = Field(min_length=1, max_length=100)
    geo_level: GeoLevel
    flags: tuple[QualityFlag, ...] = ()


class Pagination(ContractModel):
    next_cursor: str | None = None


class DataResponse(ContractModel):
    """Stable envelope used by both public REST and MCP tools."""

    data: tuple[Observation, ...]
    meta: IndicatorMetadata
    pagination: Pagination = Field(default_factory=Pagination)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Territory(ContractModel):
    geo_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    level: GeoLevel
    parent_geo_id: str | None = Field(default=None, max_length=100)
    source_system: str = Field(min_length=1, max_length=100)
    valid_from: date | None = None
    valid_to: date | None = None
