from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from argentina_open_data.contracts import (
    AggregationPolicy,
    Coverage,
    GeoLevel,
    IndicatorMetadata,
    Observation,
    Provenance,
)


def metadata(**overrides):
    values = {
        "indicator_id": "employment.private_formal",
        "name": "Empleo privado formal",
        "unit": "puestos",
        "frequency": "monthly",
        "available_geo_levels": (GeoLevel.DEPARTMENT,),
        "aggregation_policy": AggregationPolicy.SUM_ALLOWED,
        "coverage": Coverage(scope="Empleo privado registrado; no incluye informalidad ni empleo público"),
        "provenance": Provenance(
            source_id="ode",
            source_name="Observatorio de Empleo y Dinámica Empresarial",
            source_url="https://www.argentina.gob.ar/trabajo/estadisticas",
            license_id="dataset-specific-review-required",
            retrieved_at=datetime(2026, 11, 2, tzinfo=UTC),
        ),
    }
    values.update(overrides)
    return IndicatorMetadata(**values)


def test_metadata_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        metadata(unreviewed_license_claim="CC-BY-4.0")


def test_provenance_requires_timezone_and_valid_snapshot_hash():
    with pytest.raises(ValidationError):
        Provenance(
            source_id="ode",
            source_name="ODE",
            source_url="https://example.org/data",
            license_id="unknown",
            retrieved_at=datetime(2026, 11, 2),
        )
    with pytest.raises(ValidationError):
        Provenance(
            source_id="ode",
            source_name="ODE",
            source_url="https://example.org/data",
            license_id="unknown",
            retrieved_at=datetime(2026, 11, 2, tzinfo=UTC),
            snapshot_sha256="not-a-hash",
        )


def test_observation_rejects_non_finite_numeric_values():
    with pytest.raises(ValidationError):
        Observation(period="2026-09", value=float("nan"), geo_id="82.084", geo_level=GeoLevel.DEPARTMENT)


def test_observation_keeps_period_and_territorial_level_explicit():
    observation = Observation(period="2026-09", value=1234, geo_id="82.084", geo_level=GeoLevel.DEPARTMENT)
    assert observation.period == "2026-09"
    assert observation.geo_level == GeoLevel.DEPARTMENT


def test_indicator_frequency_is_a_supported_canonical_frequency():
    with pytest.raises(ValidationError):
        metadata(frequency="monthly-ish")


@pytest.mark.parametrize("period", ["2026-9", "2026-Q5", "2026/09", "2026-13", "0000"])
def test_observation_rejects_noncanonical_periods(period):
    with pytest.raises(ValidationError):
        Observation(period=period, value=1, geo_id="82", geo_level=GeoLevel.PROVINCE)
