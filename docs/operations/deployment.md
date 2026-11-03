# Local container and production deployment

## Local

```bash
docker compose up --build -d
docker compose --profile ingest run --rm ingest-georef provincias --limit 1000 --max-pages 1
```

The web app and REST API listen on port 8000. The MCP Streamable HTTP server listens on port 8001. Both read the same named volume. Ingestion is manual and bounded; it does not run at startup.

## Production requirements

- Build the image from a reviewed commit and run API and MCP as separate services.
- Attach the same durable persistent volume to both services at `SNAPSHOT_DIR`. Do not rely on an ephemeral container filesystem.
- Put both services behind a TLS-terminating reverse proxy. Do not expose plain HTTP to the public internet.
- Set `MCP_HOST=0.0.0.0`, `MCP_PORT=8001`, and explicitly set `MCP_ALLOWED_HOSTS` to the public MCP hostname, including a `:*` pattern if the proxy sends a port.
- Set `MCP_ALLOWED_ORIGINS` only to actual browser origins that need access. Non-browser MCP clients do not need an Origin allowlist.
- Restrict the API and MCP to read-only operations. Dataset capture remains an operator-controlled job.
- Configure backups and monitor snapshot storage, service health, error rates and upstream Georef availability.
- Verify `/health`, `/api/v1/sources`, a populated territory query, MCP `tools/list` and an MCP tool call after deployment.

The repository includes a Dockerfile and Compose file, but no public service is deployed by merging code. A hosting account, persistent volume, domain, TLS and provider-specific credentials are required before a live deployment can be completed.
