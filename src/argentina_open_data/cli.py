"""Command line interface for explicit, bounded dataset snapshot capture."""

from __future__ import annotations

import argparse
import json
import os

from argentina_open_data.pipeline import capture_georef_snapshot
from argentina_open_data.snapshots import SnapshotStore
from argentina_open_data.sources.georef import GeorefResource


def main() -> None:
    parser = argparse.ArgumentParser(prog="argentina-open")
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot = subparsers.add_parser("snapshot-georef", help="Capture a bounded Georef snapshot")
    snapshot.add_argument("resource", choices=[item.value for item in GeorefResource])
    snapshot.add_argument("--limit", type=int, default=1000)
    snapshot.add_argument("--max-pages", type=int, default=1)
    snapshot.add_argument("--output", default=os.getenv("SNAPSHOT_DIR", "data/snapshots"))

    mcp = subparsers.add_parser("mcp", help="Run the MCP Streamable HTTP server")

    args = parser.parse_args()
    if args.command == "snapshot-georef":
        digest, total = capture_georef_snapshot(
            GeorefResource(args.resource),
            store=SnapshotStore(args.output),
            limit=args.limit,
            max_pages=args.max_pages,
        )
        print(json.dumps({"snapshot_sha256": digest, "source_total": total}))
    elif args.command == "mcp":
        from argentina_open_data.mcp_server import run

        run()
