# Source profile: Catálogo API-INDEC

**Admission:** metadata-only; no API data snapshots are approved for public redistribution by this repository yet.

## Publisher and access

- Publisher: Instituto Nacional de Estadística y Censos (INDEC), Argentina.
- Catalog: https://api.indec.gob.ar/
- Human documentation: https://api.indec.gob.ar/docs
- OpenAPI v2 specification: https://api.indec.gob.ar/api/openapi?v=2
- API base: https://api.indec.gob.ar/v1/{table}
- Official terms: https://api.indec.gob.ar/ayuda/terminos
- Official FAQ: https://api.indec.gob.ar/ayuda/faq

The API is a PostgREST-style, read-only JSON interface. The current upstream `indec-api-skill` documents 19 table endpoints and provides a zero-dependency Python CLI. Its operational notes are useful, but the upstream skill is an independent, unofficial project and is not an INDEC product.

## Authentication and secret handling

Data endpoints require a personal JWT. INDEC states that registration and token generation are free; the token expires after 12 months, and regenerating it immediately invalidates the previous token. The token is shown only once.

- Never commit `INDEC_TOKEN`, put it in a browser bundle, expose it in a public response, or include it in logs.
- Do not ask a user to paste a personal token into a public issue or chat.
- The current application does not proxy INDEC queries publicly and does not contain a token.
- Before enabling a shared server-side token, implement caller authentication, per-caller rate limits, request budgets, audit logging and a secret manager. Otherwise a public proxy could consume the account's quota.
- Until that boundary exists, use the official API directly or a local operator-controlled client.

## License and reuse decision

The API landing page says catalog information may be copied, reused or redistributed when the primary source is clearly cited. The FAQ specifies visible attribution as “Fuente: INDEC” with the specific data service. The current terms page additionally states that published results are aggregate and that individual data are protected by statistical secrecy.

The API-specific terms do not express a standard SPDX license or clearly settle every downstream condition, including commercial redistribution. The registry therefore records custom terms and keeps the source **metadata-only**. This is a conservative engineering gate, not a claim that INDEC prohibits commercial reuse. A dataset-specific legal review is required before storing or republishing table contents.

Suggested attribution format:

> Fuente: INDEC, Catálogo API-INDEC, tabla `<table>`, período `<periodo>`. Consulta: `<retrieved_at>`.

Preserve the original table name, field names, period labels, null values and observation notes. Never treat the API's authentication requirement as a license.

## Data-quality and query constraints

The upstream `indec-api-skill` identifies operational details that must be preserved in any future connector:

- The public OpenAPI specification is available without the data JWT; table queries are authenticated.
- Column names are case-sensitive and some are mixed-case (for example `Anio`, `Periodo`, `Mes`).
- Table route names are not uniformly snake_case; some use hyphens.
- Responses are capped at 1,000 rows. Stable pagination must order by the complete primary key, not just the period.
- HTTP 206 is a valid partial response when using `Prefer: count=exact`; inspect `Content-Range`.
- Dimension values are not always enumerated in OpenAPI. Discover exact values before filtering; never guess labels such as region or indicator type.
- A null value may carry a statistical symbol in `observaciones` (for example, suppressed, provisional or unavailable). Preserve both fields.
- `indice_salarios.valor` is documented as text; do not assume every `valor` field is numeric.
- EPH tables represent agglomerates and their defined statistical universe, not province-level estimates. Do not map an agglomerate to a province or extrapolate it.

These constraints are sourced from the upstream skill and must be revalidated against the live INDEC API before implementation. The skill is MIT-licensed and independent: https://github.com/jonymusky/indec-api-skill

## Integration sequence

1. Refresh and validate the official OpenAPI spec without authentication; store the spec hash and retrieval time.
2. Select a specific table and review its official methodology, universe, period, dimensions, primary key and missing-value conventions.
3. Obtain an operator-managed credential through INDEC; keep it outside source control and CI logs.
4. Build a bounded read-only adapter with fixed host, table allowlist, column validation, response-size/time limits, stable PK pagination and explicit 200/206 handling.
5. Add fixture tests for mixed-case fields, route names, null/observation symbols, nonnumeric values and 1,000-row pagination.
6. Complete table-specific license and statistical review before snapshot publication.
7. Do not expose a public MCP/REST query proxy until caller authentication and quota controls are implemented.

## Current implementation status

No INDEC HTTP client, API proxy, data snapshot or token is included in the runtime yet. This profile records a reviewed integration candidate and the safeguards required before it becomes an executable source.
