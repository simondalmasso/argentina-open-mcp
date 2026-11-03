"""Read-only, package-resource snapshot store for immutable edge deployments."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from importlib.resources import files
from pathlib import PurePosixPath

from argentina_open_data.snapshots import (
    SnapshotDocument,
    SnapshotError,
    SnapshotManifest,
)


def _walk_json(directory, prefix: str = "") -> Iterator[tuple[object, str]]:
    """Yield packaged JSON resources and normalized relative POSIX paths."""
    for entry in directory.iterdir():
        relative = f"{prefix}/{entry.name}" if prefix else entry.name
        if entry.is_dir():
            yield from _walk_json(entry, relative)
        elif entry.is_file() and entry.name.endswith(".json"):
            yield entry, relative


class BundledSnapshotStore:
    """Expose reviewed package snapshots through the SnapshotStore read interface.

    This backend is deliberately immutable. Dataset changes are delivered with a
    reviewed application version; runtime requests never write to local disk or
    call an upstream data provider.
    """

    def __init__(self) -> None:
        self.root = files("argentina_open_data").joinpath("seed_snapshots")

    def list_manifests(self, source_id: str | None = None) -> tuple[SnapshotManifest, ...]:
        manifests: list[SnapshotManifest] = []
        for resource, relative in _walk_json(self.root):
            try:
                raw = resource.read_bytes()
                digest = hashlib.sha256(raw).hexdigest()
                document = SnapshotDocument.model_validate_json(raw)
            except (OSError, ValueError) as exc:
                raise SnapshotError(f"invalid bundled snapshot {relative}") from exc

            if source_id is not None and document.source_id != source_id:
                continue
            manifests.append(
                SnapshotManifest(
                    snapshot_sha256=digest,
                    source_id=document.source_id,
                    resource=document.resource,
                    retrieved_at=document.retrieved_at,
                    record_count=len(document.records),
                    license_id=document.license_id,
                    attribution=document.attribution,
                    document_path=relative,
                )
            )
        return tuple(sorted(manifests, key=lambda item: item.retrieved_at, reverse=True))

    def load(self, manifest: SnapshotManifest) -> SnapshotDocument:
        relative = PurePosixPath(manifest.document_path)
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            raise SnapshotError("manifest path escapes bundled snapshot root")
        resource = self.root.joinpath(*relative.parts)
        try:
            raw = resource.read_bytes()
        except OSError as exc:
            raise SnapshotError("bundled snapshot object cannot be read") from exc
        if hashlib.sha256(raw).hexdigest() != manifest.snapshot_sha256:
            raise SnapshotError("bundled snapshot hash verification failed")
        return SnapshotDocument.model_validate_json(raw)
