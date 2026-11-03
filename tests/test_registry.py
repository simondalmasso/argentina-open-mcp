import pytest
from pydantic import ValidationError

from argentina_open_data.licensing import LicenseClass, assess_reuse
from argentina_open_data.registry import (
    SourceDescriptor,
    SourceStatus,
    get_source,
    list_sources,
)


def test_registry_exposes_georef_as_verified_with_official_license_evidence():
    source = get_source("georef.territories")
    assert source.status == SourceStatus.VERIFIED
    assert source.license_class == LicenseClass.CC_BY_4_0
    assert str(source.license_evidence_url) == "https://www.argentina.gob.ar/georef/condiciones-de-uso-y-licencia"


def test_registry_records_bcra_custom_terms_without_approving_redistribution():
    source = get_source("bcra.website-content")
    assert source.status == SourceStatus.METADATA_ONLY
    assert source.license_class == LicenseClass.CUSTOM_TERMS
    assert source.custom_terms is not None
    assert not source.custom_terms.redistribution_allowed
    assert not source.custom_terms.commercial_use_allowed
    assert source.custom_terms.integrity_required
    result = assess_reuse(source.license_class, custom_terms=source.custom_terms)
    assert not result.redistributable
    assert not result.commercial_use
    assert result.allowed_purposes == ("informational", "educational", "academic")


def test_registry_lists_sources_in_stable_order():
    sources = list_sources()
    assert [source.source_id for source in sources] == [
        "bcra.website-content",
        "georef.territories",
    ]


def test_verified_source_requires_license_evidence():
    with pytest.raises(ValidationError):
        SourceDescriptor(
            source_id="example.dataset",
            name="Example",
            publisher="Example publisher",
            source_url="https://example.org/data",
            license_class=LicenseClass.CC_BY_4_0,
            status=SourceStatus.VERIFIED,
            scope_note="Example dataset.",
        )
