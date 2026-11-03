# Argentina Open Data Foundation Implementation Plan

> **For agentic workers:** Use the host's available task-by-task implementation workflow. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a tested, transport-neutral kernel foundation that prevents unsupported territorial comparisons and unverified data reuse.

**Architecture:** A small Python package defines strict Pydantic contracts, explicit territorial comparability rules and conservative dataset-level license assessments. The web, MCP and REST surfaces will consume this kernel later; no network connector or deployment platform is introduced in this milestone.

**Tech Stack:** Python 3.11+, Pydantic 2, pytest, Ruff, GitHub Actions.

## Global Constraints

- National coverage is a product goal, not a claim that every source covers every territory.
- Santa Fe is an initial validation territory, not a permanent geographic limitation.
- EPH agglomerates, provinces, departments and other geographic levels must not be conflated.
- No source is redistributed until its exact dataset license and scope have been reviewed.
- Every observation retains period, geography, quality flags and provenance through the shared contract.
- No deployment, paid service, secret, production credential or external account is introduced in this milestone.
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

- [ ] Configure CI for Python 3.11, 3.12 and 3.13 with pytest and Ruff.
- [x] Document product boundaries, contract, territorial rules, provenance, license admission and deferred infrastructure decisions.
- [ ] Run the same test and lint commands locally and in GitHub Actions.

## Deferred decisions

The MCP framework and protocol revision, REST framework, web framework, data storage, geographic crosswalk source, dataset-specific license approvals, ingestion scheduler, hosting and domain remain open until source and compatibility proofs are completed.
