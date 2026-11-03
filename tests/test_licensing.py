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
