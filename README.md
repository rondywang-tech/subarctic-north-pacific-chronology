# Code for a harmonized radiocarbon chronology framework for subarctic North Pacific marine sediment cores

This repository contains the recovered code components accompanying ESSD-2026-742. The primary scientific data and verified formal model inputs are deposited at [PANGAEA.996868](https://doi.pangaea.de/10.1594/PANGAEA.996868). PANGAEA currently controls access to those data. This public repository does not reproduce the restricted formal input tables, source transcriptions, age-model tables, posterior summaries, or other restricted scientific values.

## Release status

`PARTIAL_NOT_END_TO_END_VALIDATED`

The repository preserves 18 author-owned Python/R code files from the historical execution lineage. Sixteen are byte-identical historical copies. Two are explicitly marked publication-sanitized copies because their historical versions embedded record-level values; the reusable logic is retained and the transformations are recorded in `documentation/CODE_FILE_MANIFEST.csv`.

This is not a clean-room, one-click rebuild of the v7 scientific product. The complete raw-to-prepared transformation chain has not been recovered for every historical input. Users need the PANGAEA data/input package to execute data-dependent stages. Historical scripts retain stage-specific absolute paths such as `/Volumes/UH100/...`; users must adapt these paths to their local environment before reuse.

Posterior draws are not part of v1.0.

## Repository structure

- `historical_execution/` — recovered author-owned Python/R components.
- `environment/` — version and dependency documentation; no third-party source or metadata is redistributed.
- `documentation/` — reuse limits, dependencies, code hashes, and the public-content exclusion audit.
- `checksums/` — SHA-256 manifest.

## Licence

The root MIT `LICENSE` applies only to software code owned by the repository author. It does not license or relicense PANGAEA data, formal inputs, calibration data, or external R/Python packages. External dependencies and their upstream licences are listed in `THIRD_PARTY_NOTICES.md`; no third-party package source or metadata is redistributed here.

## Citation

See `CITATION.cff`. Cite PANGAEA.996868 separately as the associated scientific data publication.
