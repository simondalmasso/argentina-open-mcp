# Data governance: provenance, coverage and reuse

## Dataset admission checklist

A dataset is not eligible for public redistribution until its record includes:

1. Official publisher and canonical source URL.
2. Dataset identity, version or publication date, retrieval timestamp and raw snapshot hash.
3. Exact license or terms applicable to that dataset and version, with the evidence URL and review date.
4. Geographic and temporal coverage, statistical universe, frequency and known omissions.
5. Field definitions, units, missing-value conventions and revisions policy.
6. Personal-data and re-identification review appropriate to the granularity.
7. Validation results and the transformation chain from raw source to published artifact.

If license evidence is missing or ambiguous, quarantine the data. A public catalog may display descriptive metadata and a link to the publisher without copying or redistributing the dataset, subject to a separate review of the metadata itself.

## License handling

Licenses are recorded per dataset and per generated artifact, not inferred from the portal domain. A portal may host resources with different terms. `CC-BY-4.0`, `CC-BY-SA-4.0`, `ODbL`, non-commercial terms, all-rights-reserved notices and unknown terms are not interchangeable.

The code uses a deliberately conservative classifier and a versioned source registry. Standard licenses and custom terms remain distinct: custom terms require a valid evidence URL, an explicit purpose scope and separate redistribution, commercial-use, attribution, integrity and share-alike flags. Missing custom-term evidence means quarantine. The BCRA institutional-site notice is recorded as metadata-only: informational, educational and academic reuse requires full attribution and preservation of meaning/context and integrity; commercial use requires prior express authorization; bulk redistribution is not enabled by this registry record. The notice applies to the institutional site, not automatically to every API or externally sourced dataset.

This is an engineering gate, not legal advice and not a substitute for reviewing the actual license text, attribution requirements, database rights, exceptions and jurisdiction. Combining datasets with different share-alike regimes requires an explicit compatibility analysis; no blanket repository-wide data license is assumed. See the [source registry](../sources/registry.md) and [BCRA source policy profile](../sources/bcra.md).

Software license: Apache-2.0. Dataset and third-party asset licenses remain independent.

## Statistical coverage

Every indicator must state its represented universe. Examples of materially different universes include all residents, urban residents, EPH-covered agglomerates, registered private employment, exports recorded by province, and operator-reported connectivity coverage. These are not interchangeable denominators.

A missing local estimate is represented as unavailable, not zero. A stale observation is flagged, not silently described as current. Revisions preserve the earlier snapshot and identify the superseding version.

## Privacy and minimization

Prefer aggregate outputs. Exclude person-level identifiers, sensitive financial records and precise locations of vulnerable populations unless a separate documented legal and ethical review establishes necessity and lawful basis. Public availability at source does not automatically make bulk republication appropriate.

## Provenance vocabulary

- `source_published_at`: when the publisher released the source, if known.
- `retrieved_at`: when this project retrieved it.
- `snapshot_sha256`: hash of the exact raw snapshot, when stored.
- `transform_chain`: ordered identifiers for deterministic transformations.
- `quality_flags`: preliminary, revised, imputed, suppressed, stale or partial coverage.

A result must never label retrieval time as the period represented by the data.
