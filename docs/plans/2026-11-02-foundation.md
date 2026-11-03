# Argentina Open Data Foundation Implementation Plan

> **For agentic workers:** Use the host's available task-by-task implementation workflow. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a tested, transport-neutral kernel foundation that prevents unsupported territorial comparisons and unverified data reuse.

**Architecture:** A Python package defines strict Pydantic contracts, explicit territorial comparability rules, conservative dataset-level license assessments, immutable snapshots, a REST API, a browser UI and an MCP server. Runtime services read only locally stored snapshots; ingestion is an explicit operator action.

**Tech Stack:** Python 3.11+, Pydantic 2, FastAPI 0.156.8, MCP Python SDK 2.3.0, Uvicorn, pytest, Ruff, Docker Compose and GitHub Actions.

## Global Constraints

- National coverage is a product goal, not a claim that every source covers every territory.
- Santa Fe is an initial validation territory, not a permanent geographic limitation.
- EPH agglomerates, provinces, departments and other geographic levels must not be conflated.
- No source is redistributed until its exact dataset license and scope have been reviewed.
- Every observation retains period, geography, quality flags and provenance through the shared contract.
- No paid service, secret, production credential or external account is introduced. Container packaging is provided; a public deployment still requires an approved hosting account and hostname.
- The default branch is protected from direct implementation; work is performed on a feature branch.

---

### Task 1: Canonical data and provenance contracts

**Files:**
- Create: `src/argentina_open_data/contracts.py`
- Create: `src/argentina_open_data/__init__.py`
- Test: `tests/test_contracts.py`

**Interfaces:**
- Produces `GeoLevel`, `AggregationPolicy`, `QualityFlag`, `Coverage`, `Provenance`, `IndicatorMetadata`, `Observation`, `Pagination`, `DataResponse` and `Territory`.
- Pydantic models reject undeclared fields and timezone-naive provenance timestamps.

- [x] Add tests for strict fields, valid provenance timestamps, invalid hashes and explicit observation geography.
- [x] Verify invalid payloads raise `pydantic.ValidationError`.
- [x] Implement the typed models with bounded string fields and explicit enumerations.
- [x] Verify contract tests pass and run the complete suite.

### Task 2: Territorial comparability guard

**Files:**
- Create: `src/argentina_open_data/comparability.py`
- Test: `tests/test_comparability.py`

**Interfaces:**
- `validate_comparison(metadata, left, right) -> tuple[ComparisonIssue, ...]`
- `require_comparable(metadata, left, right) -> None`, raising `ComparabilityError` with structured issues.

- [x] Test valid same-period comparisons between distinct EPH agglomerates.
- [x] Test rejection of department-level expansion for agglomerate-locked indicators, mixed periods, mixed levels, unsupported levels and identical territories.
- [x] Implement blocking checks without inventing aggregation or crosswalk logic.
- [x] Verify focused and full tests pass.

### Task 3: Dataset-level license gate

**Files:**
- Create: `src/argentina_open_data/licensing.py`
- Test: `tests/test_licensing.py`

**Interfaces:**
- `LicenseClass` enumerates recognized broad license classes.
- `assess_reuse(license_class) -> ReuseAssessment` returns conservative redistribution, commercial-use, attribution and share-alike flags.

- [x] Test unknown and all-rights-reserved quarantine, non-commercial exclusion from commercial use, CC-BY attribution and share-alike review.
- [x] Implement the classifier without claiming that a portal-wide license applies to every dataset.
- [x] Verify focused and full tests pass.

### Task 4: CI and project documentation

**Files:**
- Create: `.github/workflows/ci.yml`, `.gitignore`, `README.md`, `docs/architecture/overview.md`, `docs/governance/data-and-licenses.md`

- [x] Configure CI for Python 3.11, 3.12 and 3.13 with pytest and Ruff.
- [x] Document product boundaries, contract, territorial rules, provenance, license admission and deferred infrastructure decisions.
- [x] GitHub Actions verified pytest and Ruff successfully on Python 3.11, 3.12 and 3.13 (run 41557469584). Local pytest: 11 passed; local Ruff unavailable in the isolated environment.

### Task 5: First verified territorial source adapter — Georef v2

**Files:**
- Create: `src/argentina_open_data/sources/georef.py`
- Create: `tests/test_georef.py`
- Create: `docs/sources/georef.md`

**Interfaces:**
- `GeorefClient.list(resource, limit=100, offset=0, province_id=None) -> GeorefPage`
- `GeorefRecord.to_territory() -> Territory`
- Read-only resources: provinces, departments, municipalities and localities.

- [x] Verify the official v2 OpenAPI server, resource names, attribution, license and published quotas.
- [x] Add fixture-based tests for pagination, official IDs, parent links, malformed responses, response-size limits and request throttling.
- [x] Implement a fixed-host HTTPS GET client with bounded timeout, payload size and conservative per-instance request spacing.
- [x] Verify the full test suite locally and through CI.

## Deferred decisions

The MCP framework and protocol revision, REST framework, web framework, data storage, geographic crosswalk source, dataset-specific license approvals, ingestion scheduler, hosting and domain remain open until source and compatibility proofs are completed.


### Task 6: Governance hardening and evidence-backed source registry

**Files:**
- Update: `src/argentina_open_data/licensing.py`, `contracts.py`, `comparability.py`
- Create: `src/argentina_open_data/registry.py`, `tests/test_registry.py`
- Update: `docs/governance/data-and-licenses.md`, `docs/architecture/overview.md`, `README.md`
- Create: `docs/sources/registry.md`, `docs/sources/bcra.md`

- [x] Add custom terms with mandatory evidence URL, purposes, attribution, integrity, redistribution, commercial-use and share-alike controls; default to quarantine when evidence is absent.
- [x] Replace free-form frequency with annual, quarterly and monthly values; validate canonical `YYYY`, `YYYY-QN` and `YYYY-MM` periods.
- [x] Match each observation period granularity against the indicator frequency.
- [x] Separate blocking comparability failures from non-blocking coverage and quality warnings.
- [x] Create an evidence-backed registry with Georef as verified and BCRA institutional-site content as metadata-only.
- [x] Document why unreviewed sources and the unverified Tucumán license claim remain out of the approved registry.
- [x] Verify the full Python matrix and Ruff in GitHub Actions before merging (PR #1).

## Runtime milestone — 2026-11-02

- [x] Add content-addressed immutable snapshot storage with SHA-256 verification.
- [x] Add bounded, explicit Georef snapshot capture; no automatic ingestion at startup or request time.
- [x] Add FastAPI REST endpoints for health, source registry, snapshots and territorial search/detail.
- [x] Add a browser UI that consumes REST and renders an honest empty state before ingestion.
- [x] Add official MCP Python SDK 2.3.0 tools over Streamable HTTP.
- [x] Run REST and MCP as separate processes sharing the same snapshot volume.
- [x] Add Dockerfile, Docker Compose services and a manual ingestion profile.
- [x] Verify 48 tests and Ruff on Python 3.11, 3.12 and 3.13; validate Compose and build the production image in GitHub Actions run 41561596744.
- [x] Capture and inspect the bounded live Georef v2 provinces response (24 records, including Santa Fe ID `82`); preserve the official identifiers, names, centroid payloads, attribution and CC BY 4.0 evidence in a SHA-256-addressed snapshot.
- [x] Bundle the immutable provinces snapshot in the Docker image and seed the named runtime volume idempotently before REST and MCP start; verify the snapshot hash, record count and Santa Fe lookup in CI.
- [ ] Deploy to an approved public host with HTTPS, hostname, durable storage and successful REST/MCP smoke tests.

## Cloudflare edge runtime validation — 2026-11-03

- [x] Add a Python Worker entrypoint for the existing FastAPI homepage and REST API, plus stateless MCP Streamable HTTP.
- [x] Package the reviewed 24-province Georef snapshot as an immutable Python package resource; do not rely on a persistent Worker filesystem or an R2 bucket for the initial catalogue.
- [x] Add a read-only bundled snapshot store with SHA-256 verification and path traversal protection.
- [x] Make public REST handlers and MCP tools asynchronous so the runtime does not depend on threadpool support.
- [x] Defer MCP server construction until the first request because Workers block entropy during module initialization.
- [x] Create one stateless MCP server per request because the Workers ASGI adapter starts/stops app lifespan per request and the MCP session manager is single-use.
- [x] Validate the actual local Cloudflare runtime: homepage, REST health/snapshot/territory lookup, MCP initialize, tools/list and tools/call. Use the canonical mounted endpoint `/mcp/`.
- [x] Verify Python 3.11/3.12/3.13 tests, Ruff, Docker build, Compose configuration and REST/MCP persistence smoke test after the Cloudflare changes (CI run 41579476876).
- [x] Add a manually triggered production deploy workflow that updates the existing `arg-open` Worker and runs post-deploy smoke checks; pushes and pull requests do not deploy production.
- [ ] Configure the GitHub repository secret `CLOUDFLARE_API_TOKEN` with Workers Editor scoped to the existing `arg-open` Worker and secret `CLOUDFLARE_ACCOUNT_ID`.
- [ ] Run the production deploy workflow and verify `https://arg-open.simondalmasso44.workers.dev` end-to-end.
- [ ] Review live Cloudflare plan limits and observed usage before adding larger datasets or external storage such as R2.

## INDEC source assessment — 2026-11-02

- [x] Review the upstream `indec-api-skill` repository, MIT license, API query behavior and documented 19-table catalog.
- [x] Verify the official INDEC catalog, FAQ and current terms; record authentication, token expiry, attribution and aggregate-data constraints.
- [x] Add `indec.api-catalog` to the runtime source registry as metadata-only with custom terms; no table contents are approved for public snapshots.
- [x] Document the upstream skill's useful query constraints: mixed-case columns, route names, 1,000-row cap, full-PK pagination, 206 partial responses, dimension discovery and statistical null markers.
- [x] Document why a public proxy is disabled until caller authentication, quota controls, audit logging and secret management exist.
- [x] Document optional Understand Anything usage and exclude its generated graph from Git.
- [ ] Implement a fixed-host, bounded INDEC adapter after obtaining an operator-managed token and completing table-specific methodology/license review.
- [ ] Add caller authentication and per-caller budgets before enabling INDEC queries through public REST or MCP.
- [ ] Validate the selected INDEC tables with real responses and fixtures, including suppressed/provisional markers and mixed-case field names.

## Delivery and deployment boundary

The repository includes one bounded, verified Georef v2 provinces snapshot (24 records) under CC BY 4.0 with attribution. Docker Compose imports it idempotently into a durable named volume. A Python Cloudflare Worker now serves the homepage, REST API and stateless MCP endpoint from package-bundled read-only data; its actual local runtime is CI-verified, as are all three Python versions, Ruff, Docker build and the native REST/MCP smoke test. The Worker has not been deployed to production: the supplied `workers.dev` URL still returns `Hello World!`. The manual deploy workflow is ready but requires a GitHub secret `CLOUDFLARE_API_TOKEN` with Workers Editor scoped to the existing `arg-open` Worker and a repository variable `CLOUDFLARE_ACCOUNT_ID`. No R2 bucket, paid hosting plan or new compute instance is required for the initial 24-province catalogue. Production publication remains the only release blocker; a locally verified runtime or source-control merge is not a production deployment.
