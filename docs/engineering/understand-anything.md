# Optional codebase analysis: Understand Anything

[Understand Anything](https://github.com/Egonex-AI/Understand-Anything) is an independent MIT-licensed developer tool. It scans a repository, combines static analysis with an LLM pipeline, and produces a searchable knowledge graph of files, symbols, dependencies and business flows.

It is a maintenance aid for the Argentina Open Data codebase, not a runtime dependency and not a data source. Do not add it to the production Docker image or application dependencies.

## Suggested use

Use it from a local Codex or compatible coding-agent environment when a structural audit is useful:

1. Review the upstream repository and its security/install instructions.
2. Install the Codex integration using the upstream Windows PowerShell installer, or use the documented platform installer: https://github.com/Egonex-AI/Understand-Anything#multi-platform-installation
3. Start with a narrow scope such as `src/argentina_open_data`, rather than the entire repository.
4. Run the generated graph and inspect the source-to-snapshot, snapshot-to-REST and snapshot-to-MCP paths.
5. Use the diff-impact feature before larger refactors; verify its findings against the actual code and tests.

Codex uses the `$understand` command prefix according to the upstream README. The initial analysis can consume substantial model tokens; incremental updates are cheaper. The tool can be configured for a local model, but local-model quality and compatibility must be tested rather than assumed.

## Operational boundaries

- The generated graph is derived documentation, not an authoritative architecture specification.
- Do not upload private environment files, credentials, local snapshots containing restricted data, or production secrets into an analysis workspace.
- Exclude `.env`, `.venv`, `data/snapshots`, caches, build output and generated artifacts from analysis.
- Review generated summaries and dependency edges; do not accept them as proof of runtime behavior.
- Keep generated `.ua/` or legacy `.understand-anything/` output out of Git unless a reviewed, stable artifact is intentionally useful to maintainers.

Upstream project and MIT license: https://github.com/Egonex-AI/Understand-Anything
