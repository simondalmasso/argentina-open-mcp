"""Seed immutable snapshots into the configured durable store."""

from __future__ import annotations

import json
import os
from pathlib import Path

from argentina_open_data.snapshots import SnapshotDocument, SnapshotStore


def seed_snapshot_documents(
    seed_dir: str | Path,
    store: SnapshotStore,
) -> int:
    """Validate and copy bundled snapshot documents into the runtime store.

    SnapshotStore.save is content-addressed, so repeating this operation is safe.
    Missing seed directories are a valid empty configuration; malformed seed files
    fail closed instead of being silently skipped.
    """
    root = Path(seed_dir)
    if not root.is_dir():
        return 0

    seeded = 0
    for path in sorted(root.rglob("*.json")):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            raw = path.read_bytes()
            document = SnapshotDocument.model_validate_json(raw)
            store.save(document)
        except (OSError, ValueError) as exc:
            raise ValueError(f"invalid snapshot seed {path}: {exc}") from exc
        seeded += 1
    return seeded


def main() -> None:
    seed_dir = os.getenv("SNAPSHOT_SEED_DIR", "/app/seed-snapshots")
    snapshot_dir = os.getenv("SNAPSHOT_DIR", "data/snapshots")
    count = seed_snapshot_documents(seed_dir, SnapshotStore(snapshot_dir))
    print(json.dumps({"seeded_documents": count, "seed_directory": seed_dir}))


if __name__ == "__main__":
    main()
