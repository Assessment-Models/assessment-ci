# Changelog

## [Unreleased] — Immutable validator source pin

### Changed
- The reusable Level 2 workflow accepts an optional `assessment-ci-ref` input, defaults it to a 40-character commit SHA, rejects mutable or non-SHA values, and checks out validators from that immutable commit rather than `main`.
- The independently pinned `dea-metamodel-ref` remains unchanged and continues to select the contract suite source.


## [Unreleased] — CR-AM-20: Typed touchpoint declarations in model manifests

### Added
- Optional `touchpoints.declaration` to the shared model-manifest schema. The declaration is a repository-relative YAML path to a separately governed relationship artifact; it is not free-form metadata and does not replace the dedicated touchpoint record contract.
- Level 2 validation of declaration path safety and target-file existence. Absolute paths, parent-directory traversal, non-YAML paths and missing targets are rejected.
- Positive and negative fixtures covering models with and without touchpoint declarations, missing targets, absolute paths and parent traversal.
- Self-test CI coverage for the new positive and negative controls.

### Preserved
- Existing model touchpoint artifacts, peer relationships, directional mappings, criterion mappings, overlap-resolution statements and reciprocity requirements.
- The touchpoint declaration remains optional for models that do not publish such an artifact.
- The published touchpoint record schema, contract version and immutable dea-metamodel pin are unchanged.

## [Unreleased] — CR-AM-11 Phase 4: Level 3 ecosystem validation

### Added
- `scripts/validate_ecosystem.py` — Level 3 validation against the registry's live population: immutable release refs, dependency-id resolution, and manifest coherence (registered id/type/version/contract vs the asset's own `model.yaml` at the pinned release). Assets without a `model.yaml` are informational, not failures.
- `validate-ecosystem` self-test job — checks out `assessment-registry@main` and runs the validator on every PR.

## [Unreleased] — CR-AM-11 Phase 2: contract-version resolution

### Added
- `scripts/resolve_contract.py` — resolves a model's contract handshake against the published contract suite (family id must exist; version compatibility: exact / `1.x` / `^1.0` / `1.0`-prefix). Never fetches — the caller supplies the pinned suite file.
- `.github/workflows/contract-conformance.yml` — reusable `workflow_call` Level 2 workflow: immutable-ref guard on the dea-metamodel pin, manifest + handshake validation, immutable-reference check, and suite resolution.
- `fixtures/invalid/version-mismatch.yaml` — negative control (declares 9.9 vs published 1.0).
- Self-test CI gains the `resolve-contract` job: fixtures resolved against the live suite on `dea-metamodel@main` (positive passes, mismatch rejected).

### Changed
- Negative-control loop lists its fixtures explicitly (the version-mismatch fixture is a resolve-level negative, not a handshake-level one — a glob would have false-failed it).

## [Unreleased] — CR-AM-11 Phase 1: Integration spine (CI half)

### Added
- Repository scaffold (CR-AM-11 §13): validation machinery only, no model content.
- `schemas/model-manifest.schema.json` — the root `model.yaml` contract (§22) including the §15 contract handshake, §20 component references (kind: import/extend/override), and §17 compatibility declarations.
- `scripts/validate_handshake.py` — Level 2 basic: manifest schema validation + known-contract-family check (Annex A inventory) + canonical-source check.
- `scripts/check_immutable_refs.py` — reusable immutable-reference guard (rejects `main`/`master`/`latest`/`HEAD`).
- `fixtures/` positive + negative controls; self-test CI asserts the valid fixture passes and every invalid fixture is rejected.
