"""Immutable, content-addressed snapshots of approved public datasets."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from argentina_open_data.contracts import Territory


class SnapshotError(RuntimeError):
    """Raised when a snapshot is invalid, corrupt or cannot be persisted."""


class SnapshotRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    territory: Territory
    source_record: dict[str, Any]


class SnapshotDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: int = 1
    source_id: str
    resource: str
    source_url: HttpUrl
    license_id: str
    attribution: str
    retrieved_at: datetime
    records: tuple[SnapshotRecord, ...]


class SnapshotManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_id: str
    resource: str
    retrieved_at: datetime
    record_count: int = Field(ge=0)
    license_id: str
    attribution: str
    document_path: str


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


class SnapshotStore:
    """Filesystem store with immutable SHA-256-addressed objects."""

    def __init__(self, root: str | Path = "data/snapshots") -> None:
        self.root = Path(root).resolve()

    def save(self, document: SnapshotDocument) -> SnapshotManifest:
        payload = _canonical_json(document.model_dump(mode="json"))
        digest = hashlib.sha256(payload).hexdigest()
        relative = Path(document.source_id) / document.resource / f"{digest}.json"
        destination = (self.root / relative).resolve()
        if self.root not in destination.parents:
            raise SnapshotError("snapshot path escapes configured storage root")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if destination.read_bytes() != payload:
                raise SnapshotError("content-addressed snapshot collision or corruption")
        else:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=".snapshot-", suffix=".tmp", dir=destination.parent
            )
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                try:
                    os.link(temporary_name, destination)
                except FileExistsError:
                    if destination.read_bytes() != payload:
                        raise SnapshotError("concurrent snapshot write produced different bytes")
            finally:
                Path(temporary_name).unlink(missing_ok=True)

        return SnapshotManifest(
            snapshot_sha256=digest,
            source_id=document.source_id,
            resource=document.resource,
            retrieved_at=document.retrieved_at,
            record_count=len(document.records),
            license_id=document.license_id,
            attribution=document.attribution,
            document_path=relative.as_posix(),
        )

    def list_manifests(self, source_id: str | None = None) -> tuple[SnapshotManifest, ...]:
        if not self.root.exists():
            return ()
        pattern = f"{source_id}/**/*.json" if source_id else "**/*.json"
        manifests: list[SnapshotManifest] = []
        for path in self.root.glob(pattern):
            try:
                raw = path.read_bytes()
                digest = hashlib.sha256(raw).hexdigest()
                document = SnapshotDocument.model_validate_json(raw)
                relative = path.relative_to(self.root).as_posix()
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
            except (OSError, ValueError):
                continue
        return tuple(sorted(manifests, key=lambda item: item.retrieved_at, reverse=True))

    def load(self, manifest: SnapshotManifest) -> SnapshotDocument:
        path = (self.root / manifest.document_path).resolve()
        if self.root not in path.parents:
            raise SnapshotError("manifest path escapes configured storage root")
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise SnapshotError("snapshot object cannot be read") from exc
        if hashlib.sha256(raw).hexdigest() != manifest.snapshot_sha256:
            raise SnapshotError("snapshot hash verification failed")
        return SnapshotDocument.model_validate_json(raw)


def utc_now() -> datetime:
    return datetime.now(UTC)
