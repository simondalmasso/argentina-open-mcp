# Local container and production deployment

## Local

```bash
docker compose up --build -d
```

The image bundles reviewed seed snapshots under `/app/seed-snapshots`. A one-shot `snapshot-seed` service validates each document and imports it into the named `snapshots` volume. REST and MCP wait for that job to finish successfully before starting. The import uses the content-addressed store and is safe to repeat. It does not make network requests to Georef.

To capture another bounded snapshot explicitly:

```bash
docker compose --profile ingest run --rm ingest-georef departamentos --limit 1000 --max-pages 1
```

The web app and REST API listen on port 8000. The MCP Streamable HTTP server listens on port 8001. Both read the same named volume. Only the initial bundled snapshot is loaded automatically; additional ingestion remains an operator action.

## Production requirements

- Build the image from a reviewed commit and run API and MCP as separate services.
- Keep the same durable named volume attached to the seeding, API and MCP services at `SNAPSHOT_DIR`. Do not rely on an ephemeral container filesystem.
- Put both public services behind a TLS-terminating reverse proxy. Do not expose plain HTTP to the public internet.
- Set `MCP_HOST=0.0.0.0`, `MCP_PORT=8001`, and explicitly set `MCP_ALLOWED_HOSTS` to the public MCP hostname, including a `:*` pattern if the proxy sends a port.
- Set `MCP_ALLOWED_ORIGINS` only to actual browser origins that need access. Non-browser MCP clients do not need an Origin allowlist.
- Restrict the API and MCP to read-only operations. Dataset capture remains an operator-controlled job.
- Configure backups and monitor snapshot storage, service health, error rates and upstream Georef availability.
- Verify `/health`, `/api/v1/sources`, a populated territory query, MCP `tools/list` and an MCP tool call after deployment.

The repository includes a Dockerfile and Compose file, but no public service is deployed by merging code. A hosting account, persistent volume, domain, TLS and provider-specific credentials are required before a live deployment can be completed.
