"""Hard guards against statistically invalid territorial comparisons."""

from __future__ import annotations

from dataclasses import dataclass

from argentina_open_data.contracts import AggregationPolicy, GeoLevel, IndicatorMetadata, Observation


@dataclass(frozen=True)
class ComparisonIssue:
    code: str
    message: str


class ComparabilityError(ValueError):
    def __init__(self, issues: tuple[ComparisonIssue, ...]):
        self.issues = issues
        super().__init__("; ".join(issue.message for issue in issues))


def validate_comparison(
    metadata: IndicatorMetadata,
    left: Observation,
    right: Observation,
) -> tuple[ComparisonIssue, ...]:
    """Return blocking issues; an empty tuple means the pair is comparable.

    This function intentionally does not infer geographic aggregation or convert
    statistical universes. Those operations require source-specific methods.
    """
    issues: list[ComparisonIssue] = []
    if left.geo_id == right.geo_id:
        issues.append(ComparisonIssue("same_territory", "The two observations refer to the same territory."))
    if left.period != right.period:
        issues.append(ComparisonIssue("period_mismatch", "Observations must refer to the same period."))
    if left.geo_level != right.geo_level:
        issues.append(ComparisonIssue("geo_level_mismatch", "Territories must be at the same geographic level."))

    policy = metadata.aggregation_policy
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

    return tuple(issues)


def require_comparable(
    metadata: IndicatorMetadata,
    left: Observation,
    right: Observation,
) -> None:
    issues = validate_comparison(metadata, left, right)
    if issues:
        raise ComparabilityError(issues)
