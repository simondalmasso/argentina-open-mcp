"""Conservative dataset-level reuse decisions; never infer a license from a portal."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LicenseClass(StrEnum):
    CC_BY_4_0 = "CC-BY-4.0"
    CC_BY_SA_4_0 = "CC-BY-SA-4.0"
    ODBL_1_0 = "ODbL-1.0"
    NON_COMMERCIAL = "non_commercial"
    ALL_RIGHTS_RESERVED = "all_rights_reserved"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ReuseAssessment:
    redistributable: bool
    commercial_use: bool
    attribution_required: bool
    share_alike_required: bool
    separate_database_layer_recommended: bool
    reason: str


def assess_reuse(license_class: LicenseClass) -> ReuseAssessment:
    """Apply a conservative baseline; dataset-specific terms still take precedence."""
    if license_class == LicenseClass.CC_BY_4_0:
        return ReuseAssessment(True, True, True, False, False, "Attribution required; retain the dataset's license notice.")
    if license_class == LicenseClass.CC_BY_SA_4_0:
        return ReuseAssessment(True, True, True, True, True, "Attribution and share-alike obligations apply to adaptations.")
    if license_class == LicenseClass.ODBL_1_0:
        return ReuseAssessment(True, True, True, True, True, "Database rights and ODbL share-alike obligations require a distinct compliance review.")
    if license_class == LicenseClass.NON_COMMERCIAL:
        return ReuseAssessment(True, False, True, False, True, "Non-commercial terms: exclude from commercial products unless separately authorized; inspect the exact license for any additional conditions.")
    if license_class == LicenseClass.ALL_RIGHTS_RESERVED:
        return ReuseAssessment(False, False, False, False, True, "No redistribution permission established; publish metadata and source link only.")
    return ReuseAssessment(False, False, False, False, True, "License is unknown; quarantine the dataset pending verification.")
