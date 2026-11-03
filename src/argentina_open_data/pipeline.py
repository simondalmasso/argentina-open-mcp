"""Bounded source-to-snapshot pipeline. No automatic ingestion at application startup."""

from __future__ import annotations

from datetime import UTC, datetime

from argentina_open_data.registry import SourceStatus, get_source
from argentina_open_data.snapshots import SnapshotDocument, SnapshotRecord, SnapshotStore
from argentina_open_data.sources.georef import GeorefClient, GeorefResource


def capture_georef_snapshot(
    resource: GeorefResource,
    *,
    store: SnapshotStore,
    client: GeorefClient | None = None,
    limit: int = 1000,
    max_pages: int = 1,
) -> tuple[str, int]:
    """Capture at most max_pages from Georef; callers explicitly opt into more pages."""
    source = get_source("georef.territories")
    if source.status != SourceStatus.VERIFIED:
        raise ValueError("Georef is not admitted for snapshot ingestion")
    if not 1 <= max_pages <= 10:
        raise ValueError("max_pages must be between 1 and 10")
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")

    georef = client or GeorefClient()
    offset = 0
    records: list[SnapshotRecord] = []
    total = 0
    for _ in range(max_pages):
        page = georef.list(resource, limit=limit, offset=offset)
        total = page.total
        records.extend(
            SnapshotRecord(
                territory=record.to_territory(),
                source_record=record.payload,
            )
            for record in page.records
        )
        offset += page.count
        if page.count == 0 or offset >= page.total:
            break

    document = SnapshotDocument(
        source_id=source.source_id,
        resource=resource.value,
        source_url=f"{georef.BASE_URL}/{resource.value}",
        license_id=source.license_class.value,
        attribution=source.attribution or georef.ATTRIBUTION,
        retrieved_at=datetime.now(UTC),
        records=tuple(records),
    )
    manifest = store.save(document)
    return manifest.snapshot_sha256, total
