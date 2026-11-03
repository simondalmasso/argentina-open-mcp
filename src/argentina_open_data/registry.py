"""Evidence-backed source registry for datasets admitted to the project."""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from argentina_open_data.licensing import CustomLicenseTerms, LicenseClass, assess_reuse


class SourceStatus(StrEnum):
    VERIFIED = "verified"
    METADATA_ONLY = "metadata_only"
    QUARANTINED = "quarantined"


class SourceDescriptor(BaseModel):
    """Dataset-level source entry with explicit license evidence and admission state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{1,99}$")
    name: str = Field(min_length=1, max_length=200)
    publisher: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl
    license_class: LicenseClass
    license_evidence_url: HttpUrl | None = None
    license_reviewed_at: date | None = None
    attribution: str | None = Field(default=None, max_length=500)
    status: SourceStatus
    custom_terms: CustomLicenseTerms | None = None
    scope_note: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_license_evidence_and_admission(self) -> SourceDescriptor:
        if self.license_class != LicenseClass.UNKNOWN:
            if self.license_evidence_url is None or self.license_reviewed_at is None:
                raise ValueError("known license classes require an evidence URL and review date")
        if self.license_class == LicenseClass.CUSTOM_TERMS:
            if self.custom_terms is None:
                raise ValueError("custom terms require evidence-backed, explicit conditions")
            if str(self.custom_terms.evidence_url) != str(self.license_evidence_url):
                raise ValueError("custom terms evidence URL must match the registry evidence URL")
        elif self.custom_terms is not None:
            raise ValueError("custom_terms may only be set for the custom_terms license class")
        if self.status == SourceStatus.VERIFIED:
            assessment = assess_reuse(self.license_class, custom_terms=self.custom_terms)
            if not assessment.redistributable:
                raise ValueError("verified sources must have an explicitly redistributable license assessment")
        if self.status == SourceStatus.METADATA_ONLY and self.license_class == LicenseClass.UNKNOWN:
            raise ValueError("metadata-only sources need a known, reviewed source policy")
        return self


_SOURCES = (
    SourceDescriptor(
        source_id="bcra.website-content",
        name="Contenido estadístico del sitio institucional del BCRA",
        publisher="Banco Central de la República Argentina",
        source_url="https://www.bcra.gob.ar/estadisticas-indicadores/",
        license_class=LicenseClass.CUSTOM_TERMS,
        license_evidence_url="https://www.bcra.gob.ar/aviso-legal/",
        license_reviewed_at=date(2026, 11, 2),
        attribution="Banco Central de la República Argentina (BCRA)",
        status=SourceStatus.METADATA_ONLY,
        custom_terms=CustomLicenseTerms(
            evidence_url="https://www.bcra.gob.ar/aviso-legal/",
            allowed_purposes=("informational", "educational", "academic"),
            redistribution_allowed=False,
            commercial_use_allowed=False,
            attribution_required=True,
            integrity_required=True,
        ),
        scope_note=(
            "The institutional website notice permits informational, educational and academic "
            "reuse with full attribution and preservation of meaning/context and integrity; "
            "commercial, advertising or campaign use requires prior express authorization. "
            "This is a metadata-only admission: it does not authorize bulk redistribution. "
            "The notice applies to the institutional website; APIs and third-party materials "
            "may carry separate terms and require dataset-specific review."
        ),
    ),
    SourceDescriptor(
        source_id="georef.territories",
        name="Georef v2 — unidades territoriales",
        publisher="Servicio Georef — Argentina.gob.ar",
        source_url="https://apis.datos.gob.ar/georef/api/v2.0",
        license_class=LicenseClass.CC_BY_4_0,
        license_evidence_url="https://www.argentina.gob.ar/georef/condiciones-de-uso-y-licencia",
        license_reviewed_at=date(2026, 11, 2),
        attribution="Servicio Georef – https://www.argentina.gob.ar/georef",
        status=SourceStatus.VERIFIED,
        scope_note=(
            "The official Georef terms apply to Georef-published information covered by those "
            "terms; preserve attribution and identify modifications. Do not transfer this "
            "license to third-party data merely exposed or linked by Georef."
        ),
    ),
    SourceDescriptor(
        source_id="indec.api-catalog",
        name="Catálogo API-INDEC — servicios estadísticos",
        publisher="Instituto Nacional de Estadística y Censos (INDEC)",
        source_url="https://api.indec.gob.ar/docs",
        license_class=LicenseClass.CUSTOM_TERMS,
        license_evidence_url="https://api.indec.gob.ar/ayuda/terminos",
        license_reviewed_at=date(2026, 11, 2),
        attribution="Fuente: INDEC, Catálogo API-INDEC, tabla y período consultados.",
        status=SourceStatus.METADATA_ONLY,
        custom_terms=CustomLicenseTerms(
            evidence_url="https://api.indec.gob.ar/ayuda/terminos",
            allowed_purposes=("consulta", "reutilizacion estadistica sujeta a revision"),
            redistribution_allowed=True,
            commercial_use_allowed=False,
            attribution_required=True,
            integrity_required=True,
        ),
        scope_note=(
            "The API landing page permits copying, reuse and redistribution when the primary "
            "source is cited; the FAQ requires visible INDEC attribution. The API-specific "
            "terms do not identify a standard license or clearly settle commercial reuse. "
            "This conservative metadata-only record does not approve data snapshots or public "
            "redistribution until each table's methodology, scope and applicable terms are "
            "reviewed. Commercial permission is not established by this record."
        ),
    ),
)


def list_sources() -> tuple[SourceDescriptor, ...]:
    """Return the immutable registry in stable source-id order."""
    return tuple(sorted(_SOURCES, key=lambda source: source.source_id))


def get_source(source_id: str) -> SourceDescriptor:
    """Return one source descriptor or raise KeyError for an unknown identifier."""
    for source in _SOURCES:
        if source.source_id == source_id:
            return source
    raise KeyError(source_id)
