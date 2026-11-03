from datetime import UTC, datetime

import pytest

from argentina_open_data.comparability import (
    ComparabilityError,
    require_comparable,
    validate_comparison,
)
from argentina_open_data.contracts import (
    AggregationPolicy,
    Coverage,
    GeoLevel,
    IndicatorMetadata,
    Observation,
    Provenance,
)


def make_metadata(policy=AggregationPolicy.AGGLOMERATE_LOCKED, levels=(GeoLevel.EPH_AGGLOMERATE,)):
    return IndicatorMetadata(
        indicator_id="labor.unemployment_rate",
        name="Tasa de desocupación",
        unit="percent",
        frequency="quarterly",
        available_geo_levels=levels,
        aggregation_policy=policy,
        coverage=Coverage(scope="Población urbana cubierta por los aglomerados EPH"),
        provenance=Provenance(
            source_id="indec-eph",
            source_name="INDEC EPH",
            source_url="https://www.indec.gob.ar/indec/web/Institucional-Indec-BasesDeDatos",
            license_id="pending_dataset_level_verification",
            retrieved_at=datetime(2026, 11, 2, tzinfo=UTC),
        ),
    )


def obs(geo_id, level=GeoLevel.EPH_AGGLOMERATE, period="2026-Q2"):
    return Observation(period=period, value=8.1, geo_id=geo_id, geo_level=level)


def test_eph_comparison_accepts_two_distinct_agglomerates_same_period():
    assert validate_comparison(make_metadata(), obs("agl-01"), obs("agl-02")) == ()


def test_eph_comparison_rejects_department_level_expansion():
    with pytest.raises(ComparabilityError, match="restricted to its published EPH agglomerates"):
        require_comparable(make_metadata(), obs("dep-01", GeoLevel.DEPARTMENT), obs("dep-02", GeoLevel.DEPARTMENT))


def test_comparison_rejects_mixed_periods_and_levels():
    issues = validate_comparison(make_metadata(), obs("agl-01"), obs("dep-02", GeoLevel.DEPARTMENT, "2026-Q1"))
    assert {issue.code for issue in issues} >= {"period_mismatch", "geo_level_mismatch", "unsupported_geo_level", "agglomerate_locked"}


def test_comparison_rejects_same_territory():
    issues = validate_comparison(make_metadata(), obs("agl-01"), obs("agl-01"))
    assert "same_territory" in {issue.code for issue in issues}


def test_coverage_declared_policy_emits_non_blocking_warning():
    from argentina_open_data.comparability import ComparisonSeverity

    metadata = make_metadata(
        policy=AggregationPolicy.COVERAGE_DECLARED,
        levels=(GeoLevel.DEPARTMENT,),
    )
    left = obs("dep-01", GeoLevel.DEPARTMENT, "2026-Q2")
    right = obs("dep-02", GeoLevel.DEPARTMENT, "2026-Q2")

    issues = validate_comparison(metadata, left, right)

    assert len(issues) == 1
    assert issues[0].code == "coverage_declared"
    assert issues[0].severity == ComparisonSeverity.WARNING
    require_comparable(metadata, left, right)


def test_period_granularity_must_match_indicator_frequency():
    metadata = make_metadata(
        policy=AggregationPolicy.COVERAGE_DECLARED,
        levels=(GeoLevel.DEPARTMENT,),
    )
    left = obs("dep-01", GeoLevel.DEPARTMENT, "2026-06")
    right = obs("dep-02", GeoLevel.DEPARTMENT, "2026-06")

    issues = validate_comparison(metadata, left, right)

    assert "period_frequency_mismatch" in {issue.code for issue in issues}


def test_partial_coverage_flags_emit_non_blocking_warning():
    from argentina_open_data.comparability import ComparisonSeverity
    from argentina_open_data.contracts import QualityFlag

    metadata = make_metadata(
        policy=AggregationPolicy.COVERAGE_DECLARED,
        levels=(GeoLevel.DEPARTMENT,),
    )
    left = Observation(
        period="2026-Q2",
        value=1,
        geo_id="dep-01",
        geo_level=GeoLevel.DEPARTMENT,
        flags=(QualityFlag.PARTIAL_COVERAGE,),
    )
    right = obs("dep-02", GeoLevel.DEPARTMENT, "2026-Q2")

    issues = validate_comparison(metadata, left, right)

    assert "partial_coverage" in {issue.code for issue in issues}
    require_comparable(metadata, left, right)
    assert all(
        issue.severity == ComparisonSeverity.WARNING
        for issue in issues
        if issue.code in {"coverage_declared", "partial_coverage"}
    )
