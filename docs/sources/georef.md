# Source profile: Georef v2

**Status:** first read-only connector; API contract checked against the official OpenAPI definition on 2026-11-02.

## Publisher and interface

- Publisher: Argentina.gob.ar, national public-sector Georef service.
- API base: https://apis.datos.gob.ar/georef/api/v2.0
- Official overview: https://www.argentina.gob.ar/georef/georef-servicio-de-normalizacion-de-direcciones-y-unidades-territoriales-de-argentina/acerca
- Official API v2 reference: https://www.argentina.gob.ar/node/477579
- OpenAPI definition: https://raw.githubusercontent.com/datosgobar/georef-ar-api/refs/heads/development/docs/open-api/spec/openapi.json
- Full data downloads: https://www.argentina.gob.ar/georef/descarga-de-la-base-completa
- Terms and license: https://www.argentina.gob.ar/georef/condiciones-de-uso-y-licencia

## Scope in the first connector

The client currently reads provinces, departments, municipalities and localities through the v2.0 GET endpoints. It preserves the official string identifier, source name and available parent identifier. It does not infer crosswalks, geometries or historical boundary changes. Additional resources such as census tracts, EPH agglomerates, institutions, streets and addresses need separate modeling and validation before they are exposed through the kernel.

## Reuse terms

The official Georef terms state that published information is available under Creative Commons Attribution 4.0 International (CC BY 4.0). Attribution is required as “Servicio Georef – argentina.gob.ar/georef” or by linking to the official site; modifications must be identified. The connector declares CC-BY-4.0 as the dataset license only for Georef resources covered by those terms. It must not transfer that license to data from other publishers merely because Georef exposes or references it.

## Public API quota

The official terms publish these non-APN quotas:

- 10 requests per second
- 40 requests per minute
- 2,000 requests per hour
- 10,000 requests per day

The client spaces calls by at least nine seconds per instance by default, which is conservative against the daily quota when one client instance is used continuously. This is not a distributed quota manager: multiple processes, deployments or users must share an external budget before production-scale ingestion. Prefer complete dataset downloads for bulk refreshes rather than many small API calls.

## Operational behavior

- HTTPS and a fixed official API host; callers cannot supply arbitrary URLs.
- Read-only GET requests; no authentication token or secret is required for the public API.
- Bounded timeout and response size; malformed JSON, missing result collections, malformed records and HTTP/network errors fail explicitly.
- Pagination is explicit through max and inicio; no unbounded automatic pagination.
- The connector is a retrieval adapter, not permission to republish arbitrary fields without preserving attribution and modification notices.

## Known limitations

- The first connector supports only four jurisdictional resources.
- The client-level rate limiter does not coordinate across processes or deployments; production ingestion must use a shared request budget or a single controlled ingestion worker.
- The explicit ingestion pipeline stores immutable, SHA-256-addressed snapshot documents and manifests. Each document retains the source record payload alongside the normalized territory. The hash covers canonical JSON produced after parsing and validation, not the original HTTP response bytes or headers; do not describe it as a byte-for-byte hash of the publisher response.
- Georef is a territorial reference source, not a substitute for source-specific statistical geographies or their universes.
