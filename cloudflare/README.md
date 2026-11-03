# Cloudflare Worker deployment

This deployment uses one Python Worker named `arg-open` for the public web page, REST API and remote MCP endpoint.

## Why one Worker

- FastAPI serves the existing REST routes and the packaged homepage.
- The Python MCP server is mounted as a stateless Streamable HTTP ASGI application at `/mcp/`. Each request gets a fresh MCP server and one-shot session manager because the Workers ASGI adapter owns application lifespan per request.
- Both interfaces use the same `BundledSnapshotStore`, the same Pydantic contracts and the same reviewed Georef snapshot.
- The first release packages the 24-province snapshot as immutable application data. It does not write to a Worker filesystem, call Georef at request time or need an R2 bucket. New datasets are added through reviewed data updates and a new deploy. R2 is the next storage step if dataset size or refresh cadence warrants it.

All public FastAPI handlers and MCP tools are asynchronous. Cloudflare Workers do not provide a Python threadpool, so synchronous handlers must not be added to this app. MCP construction is deferred until the first request because Cloudflare blocks access to entropy during module initialization. The MCP server is stateless and constructed per request: its session manager only supports one lifecycle run, while the Workers ASGI adapter starts and stops application lifespan per request.

Cloudflare Python Workers require Python 3.13 and the `python_workers` compatibility flag. Python Workers are currently in open beta. Cloudflare's free Workers plan currently publishes request, CPU and bundle-size limits; confirm the live limits before scaling beyond this read-only catalogue.

## Local development

Requires Node.js 22+, Python 3.13+ and uv.

From the repository root:

```bash
uv sync --project cloudflare/worker --all-groups
cd cloudflare/worker
uv run pywrangler dev --ip 127.0.0.1 --port 8787
```

Endpoints:

- Web: http://127.0.0.1:8787/
- Health: http://127.0.0.1:8787/health
- REST/OpenAPI: http://127.0.0.1:8787/docs
- MCP: http://127.0.0.1:8787/mcp/

The CI job starts the actual local Cloudflare runtime and smoke-tests the homepage, REST province search, MCP handshake, tool discovery and tool execution.

## One-time GitHub configuration

To deploy the existing `arg-open` Worker from GitHub Actions, configure these repository secrets:

- **Secret** `CLOUDFLARE_API_TOKEN`: a Cloudflare API token with the **Workers Editor** role scoped to the existing `arg-open` Worker. This is sufficient to update and deploy that Worker without granting access to every Worker in the account.
- **Secret** `CLOUDFLARE_ACCOUNT_ID`: that account's Account ID. The deployment workflow reads it from GitHub Secrets.

The token is stored only in GitHub Actions Secrets. Do not commit it, paste it into the repository, or add it to `.env`.

## Publish

After configuring the secret and variable:

1. Open GitHub Actions → **Deploy Cloudflare Worker**.
2. Run the workflow against `main`.
3. The workflow builds the Python Worker, deploys the configured Worker name `arg-open`, and runs post-deploy HTTP and MCP smoke tests against `https://arg-open.simondalmasso44.workers.dev`.

This updates the existing placeholder Worker with the same name and keeps the target hostname. The workflow is manual; ordinary pushes and pull requests never publish production.

## Snapshot updates

The packaged snapshot lives under `src/argentina_open_data/seed_snapshots/` so it is included in the Python wheel. Its canonical SHA-256 is asserted by the test suite. To publish another dataset, add a reviewed snapshot resource, verify its source and license, update coverage tests and deploy a new Worker version.

No mutable database is required for this initial read-only catalogue. Do not add R2, D1, or a paid plan merely to serve this first snapshot.
