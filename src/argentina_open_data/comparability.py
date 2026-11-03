"""Hard guards and visible warnings for statistically honest comparisons."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from argentina_open_data.contracts import (
    AggregationPolicy,
    GeoLevel,
    IndicatorMetadata,
    Observation,
    ObservationFrequency,
    QualityFlag,
)


class ComparisonSeverity(StrEnum):
    BLOCKING = "blocking"
    WARNING = "warning"


@dataclass(frozen=True)
class ComparisonIssue:
    code: str
    message: str
    severity: ComparisonSeverity = ComparisonSeverity.BLOCKING


class ComparabilityError(ValueError):
    def __init__(self, issues: tuple[ComparisonIssue, ...]):
        self.issues = issues
        super().__init__("; ".join(issue.message for issue in issues))


def _period_frequency(period: str) -> ObservationFrequency:
    if re.fullmatch(r"[0-9]{4}", period):
        return ObservationFrequency.ANNUAL
    if re.fullmatch(r"[0-9]{4}-Q[1-4]", period):
        return ObservationFrequency.QUARTERLY
    if re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", period):
        return ObservationFrequency.MONTHLY
    raise ValueError(f"unsupported canonical period: {period}")


def validate_comparison(
    metadata: IndicatorMetadata,
    left: Observation,
    right: Observation,
) -> tuple[ComparisonIssue, ...]:
    """Return blocking issues and non-blocking warnings for a comparison.

    Warnings remain visible to callers; `require_comparable` raises only for
    blocking issues. This keeps data-quality cautions from being silently lost
    while allowing comparisons that the source explicitly supports.
    """
    issues: list[ComparisonIssue] = []
    if left.geo_id == right.geo_id:
        issues.append(ComparisonIssue("same_territory", "The two observations refer to the same territory."))
    if left.period != right.period:
        issues.append(ComparisonIssue("period_mismatch", "Observations must refer to the same period."))
    if left.geo_level != right.geo_level:
        issues.append(ComparisonIssue("geo_level_mismatch", "Territories must be at the same geographic level."))

    expected_frequency = ObservationFrequency(metadata.frequency)
    if any(_period_frequency(item.period) != expected_frequency for item in (left, right)):
        issues.append(
            ComparisonIssue(
                "period_frequency_mismatch",
                "Observation period granularity must match the indicator frequency.",
            )
        )

    policy = AggregationPolicy(metadata.aggregation_policy)
    for observation in (left, right):
        if observation.geo_level not in metadata.available_geo_levels:
            issues.append(ComparisonIssue("unsupported_geo_level", "This indicator is not published at this geographic level."))
        if policy == AggregationPolicy.AGGLOMERATE_LOCKED and observation.geo_level != GeoLevel.EPH_AGGLOMERATE:
            issues.append(ComparisonIssue("agglomerate_locked", "This indicator is restricted to its published EPH agglomerates."))
        elif policy == AggregationPolicy.FIXED_REGIONS and observation.geo_level not in {
            GeoLevel.INDEC_REGION,
            GeoLevel.COUNTRY,
        }:
            issues.append(ComparisonIssue("fixed_regions_only", "This indicator is only comparable at its official regional or national level."))

    if policy == AggregationPolicy.COVERAGE_DECLARED:
        issues.append(
            ComparisonIssue(
                "coverage_declared",
                "Coverage is declared by the source; inspect its scope and limitations before interpreting differences.",
                ComparisonSeverity.WARNING,
            )
        )

    if QualityFlag.PARTIAL_COVERAGE in left.flags or QualityFlag.PARTIAL_COVERAGE in right.flags:
        issues.append(
            ComparisonIssue(
                "partial_coverage",
                "At least one observation has partial coverage; differences may reflect coverage as well as the measured value.",
                ComparisonSeverity.WARNING,
            )
        )
    if QualityFlag.STALE in left.flags or QualityFlag.STALE in right.flags:
        issues.append(
            ComparisonIssue(
                "stale_observation",
                "At least one observation is marked stale; check source freshness before interpreting the comparison.",
                ComparisonSeverity.WARNING,
            )
        )

    return tuple(issues)


def require_comparable(
    metadata: IndicatorMetadata,
    left: Observation,
    right: Observation,
) -> None:
    issues = validate_comparison(metadata, left, right)
    blocking = tuple(issue for issue in issues if issue.severity == ComparisonSeverity.BLOCKING)
    if blocking:
        raise ComparabilityError(blocking)
