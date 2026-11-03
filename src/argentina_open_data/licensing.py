"""Conservative dataset-level reuse decisions; never infer a license from a portal."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class LicenseClass(StrEnum):
    CC_BY_4_0 = "CC-BY-4.0"
    CC_BY_SA_4_0 = "CC-BY-SA-4.0"
    ODBL_1_0 = "ODbL-1.0"
    NON_COMMERCIAL = "non_commercial"
    CUSTOM_TERMS = "custom_terms"
    ALL_RIGHTS_RESERVED = "all_rights_reserved"
    UNKNOWN = "unknown"


class CustomLicenseTerms(BaseModel):
    """Evidence-backed, source-specific terms that do not map to a standard license."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_url: HttpUrl
    allowed_purposes: tuple[str, ...] = Field(min_length=1)
    redistribution_allowed: bool = False
    commercial_use_allowed: bool = False
    attribution_required: bool = True
    integrity_required: bool = True
    share_alike_required: bool = False


@dataclass(frozen=True)
class ReuseAssessment:
    redistributable: bool
    commercial_use: bool
    attribution_required: bool
    share_alike_required: bool
    separate_database_layer_recommended: bool
    reason: str
    allowed_purposes: tuple[str, ...] = ()
    integrity_required: bool = False
    evidence_url: str | None = None
    requires_manual_review: bool = False


def assess_reuse(
    license_class: LicenseClass,
    *,
    custom_terms: CustomLicenseTerms | None = None,
) -> ReuseAssessment:
    """Apply a conservative baseline; exact dataset terms still take precedence.

    Custom terms are quarantined unless a validated evidence URL and the actual
    purpose/redistribution restrictions are supplied. The assessment preserves
    those restrictions instead of flattening them into a generic non-commercial
    boolean.
    """
    if license_class == LicenseClass.CC_BY_4_0:
        return ReuseAssessment(
            True, True, True, False, False,
            "Attribution required; identify modifications and retain the license notice.",
        )
    if license_class == LicenseClass.CC_BY_SA_4_0:
        return ReuseAssessment(
            True, True, True, True, True,
            "Attribution and share-alike obligations apply to adaptations.",
        )
    if license_class == LicenseClass.ODBL_1_0:
        return ReuseAssessment(
            True, True, True, True, True,
            "Database rights and ODbL share-alike obligations require a distinct compliance review.",
        )
    if license_class == LicenseClass.NON_COMMERCIAL:
        return ReuseAssessment(
            True, False, True, False, True,
            "Non-commercial terms: exclude from commercial products unless separately authorized; inspect the exact license for additional conditions.",
        )
    if license_class == LicenseClass.CUSTOM_TERMS:
        if custom_terms is None:
            return ReuseAssessment(
                False, False, False, False, True,
                "Custom terms lack validated evidence and scope; quarantine pending review.",
                requires_manual_review=True,
            )
        return ReuseAssessment(
            custom_terms.redistribution_allowed,
            custom_terms.commercial_use_allowed,
            custom_terms.attribution_required,
            custom_terms.share_alike_required,
            custom_terms.share_alike_required or not custom_terms.commercial_use_allowed,
            "Apply only the evidence-backed purposes and restrictions recorded for these custom terms.",
            allowed_purposes=custom_terms.allowed_purposes,
            integrity_required=custom_terms.integrity_required,
            evidence_url=str(custom_terms.evidence_url),
            requires_manual_review=True,
        )
    if license_class == LicenseClass.ALL_RIGHTS_RESERVED:
        return ReuseAssessment(
            False, False, False, False, True,
            "No redistribution permission established; publish metadata and source link only.",
        )
    return ReuseAssessment(
        False, False, False, False, True,
        "License is unknown; quarantine the dataset pending verification.",
        requires_manual_review=True,
    )
