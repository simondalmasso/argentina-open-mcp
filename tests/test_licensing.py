from argentina_open_data.licensing import LicenseClass, assess_reuse


def test_unknown_license_is_quarantined():
    result = assess_reuse(LicenseClass.UNKNOWN)
    assert not result.redistributable
    assert not result.commercial_use


def test_cc_by_sa_requires_share_alike_and_layer_review():
    result = assess_reuse(LicenseClass.CC_BY_SA_4_0)
    assert result.redistributable and result.commercial_use
    assert result.attribution_required and result.share_alike_required
    assert result.separate_database_layer_recommended


def test_non_commercial_license_is_not_commercially_usable():
    result = assess_reuse(LicenseClass.NON_COMMERCIAL)
    assert result.redistributable
    assert not result.commercial_use


def test_custom_terms_without_evidence_are_quarantined():
    result = assess_reuse(LicenseClass.CUSTOM_TERMS)
    assert not result.redistributable
    assert not result.commercial_use
    assert result.requires_manual_review


def test_custom_terms_preserve_allowed_purposes_and_integrity_requirements():
    from argentina_open_data.licensing import CustomLicenseTerms

    terms = CustomLicenseTerms(
        evidence_url="https://www.bcra.gob.ar/aviso-legal/",
        allowed_purposes=("informational", "educational", "academic"),
        redistribution_allowed=False,
        commercial_use_allowed=False,
        attribution_required=True,
        integrity_required=True,
    )
    result = assess_reuse(LicenseClass.CUSTOM_TERMS, custom_terms=terms)

    assert not result.redistributable
    assert not result.commercial_use
    assert result.attribution_required
    assert result.integrity_required
    assert result.allowed_purposes == ("informational", "educational", "academic")
    assert result.evidence_url == "https://www.bcra.gob.ar/aviso-legal/"


def test_custom_terms_require_a_valid_evidence_url_and_nonempty_scope():
    import pytest
    from pydantic import ValidationError

    from argentina_open_data.licensing import CustomLicenseTerms

    with pytest.raises(ValidationError):
        CustomLicenseTerms(allowed_purposes=("informational",))
    with pytest.raises(ValidationError):
        CustomLicenseTerms(
            evidence_url="https://www.bcra.gob.ar/aviso-legal/",
            allowed_purposes=(),
        )
