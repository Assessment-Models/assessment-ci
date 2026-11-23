# Assessment's Continuous Integration (Automation Pipeline)

**Cross-repository validation and ecosystem integration logic for the Assessment-Models ecosystem** (CR-AM-11 §13).

This repository owns **no assessment model content**. It provides the validation machinery for the three-level CI model (§14):

| Level | Name | Where it runs | What it checks |
|---|---|---|---|
| 1 | Local model CI | Each model repository | Syntax, schema validation, reference integrity, internal consistency, version consistency, examples, tests |
| 2 | Contract conformance CI | Each model repository, against pinned contract/schema sources | Manifest and handshake conformance, immutable references, touchpoint record structural conformance, and contract-version resolution |
| 3 | Ecosystem CI | This repo + [assessment-registry](https://github.com/Assessment-Models/assessment-registry) | Registry integrity, reference resolution, contract/version compatibility, component dependencies, and cross-model semantic relationships |

## Phase 1 scope (current)

- `schemas/model-manifest.schema.json` — the root `model.yaml` manifest contract (CR-AM-11 §22): identity, version, contract handshake, components, dependencies, compatibility (§15/§17), and typed optional declarations for separately governed artifacts such as `touchpoints.yaml`.
- `scripts/validate_handshake.py` — Level 2 basic: validate `model.yaml` against the manifest schema, verify the handshake names a known contract family (Annex A inventory), and validate that an optional touchpoint declaration is a safe repository-relative YAML path to an existing file.
- `scripts/validate_touchpoints.py` — Level 2 structural: validate a declared touchpoint artifact against `maturity-touchpoint-contract` schema from the caller's pinned `dea-metamodel-ref`; resolve its contract-family/version pin against the same pinned suite; confirm `repo_id` matches the caller's model identity. Models without declarations are explicitly skipped and remain valid.
- `scripts/check_immutable_refs.py` — reusable guard: every external reference in a manifest (components, dependencies) must be immutable (tag `vX.Y.Z`, commit SHA, or digest — never `main`/`latest`).
- `fixtures/` and `tests/` — positive and negative controls for manifest/path and touchpoint structural validation.
- Self-test CI runs the validators and unit tests on every PR.

**Boundary:** Level 2 structural conformance does not establish peer repository/model/touchpoint existence, criterion existence, reciprocal-record existence or reverse-endpoint consistency. Those remain Level 3 semantic checks under issue #9.

## Phase 2 additions (current)

- `scripts/resolve_contract.py` — Level 2 full: resolves a model's root handshake against the published contract suite from a pinned dea-metamodel checkout. Family id must exist in the suite; declared version must be compatible (exact, major wildcard, caret range, or supported prefix).
- `.github/workflows/contract-conformance.yml` — reusable `workflow_call` workflow for model repositories. It requires immutable refs for both the dea-metamodel contract/schema source and assessment-ci validator source, then runs manifest/path validation, immutable-reference checks, root handshake resolution and touchpoint structural validation.
- Self-test CI resolves against the immutable `dea-metamodel@v0.1.0-draft` contract release for touchpoint-specific fixtures.

## Phase 4 additions (current)

- `scripts/validate_ecosystem.py` — Level 3 registry validation: immutable release refs, dependency-id resolution, and manifest coherence (registered id/type/version/contract vs the asset's own `model.yaml` at the pinned release). Assets without a `model.yaml` are informational, not failures.
- `validate-ecosystem` self-test job — checks out `Assessment-Models/assessment-registry@main` and runs Level 3 validation against the live population on every PR.
- Cross-repo fan-out stays `workflow_dispatch`-only until the org-level dispatch credential exists.

## Next Level 3 increment

Issue #9 governs touchpoint semantic validation against registry-pinned model releases: peer identity resolution, peer touchpoint resolution, reciprocal mirror/endpoint checks and criterion mapping resolution. This work must not be conflated with Level 2 structural validation.

## Nightly ecosystem health (M-5)

The self-test suite (including `validate-ecosystem` and `catalog-view-check`) also runs nightly and via `workflow_dispatch`. Schedule runs are read-only guards.

---

*Established under [CR-AM-11 — Federated Assessment Model Ecosystem](https://github.com/technehub-labs/dea-metamodel/blob/main/change-requests/CR-AM-11.md) Phase 1.*
