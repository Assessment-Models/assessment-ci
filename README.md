# assessment-ci

**Cross-repository validation and ecosystem integration logic for the Assessment-Models ecosystem** (CR-AM-11 §13).

This repository owns **no assessment model content**. It provides the validation machinery for the three-level CI model (§14):

| Level | Name | Where it runs | What it checks |
|---|---|---|---|
| 1 | Local model CI | Each model repository | Syntax, schema validation, reference integrity, internal consistency, version consistency, examples, tests |
| 2 | Contract conformance CI | Each model repository, against a pinned dea-metamodel release | The declared contract handshake (§15) resolves and the model validates against that contract version |
| 3 | Ecosystem CI | This repo + [assessment-registry](https://github.com/Assessment-Models/assessment-registry) | Registry integrity, reference resolution, contract/version compatibility, component dependencies, cross-model mappings, duplicate identifiers (§13.1) |

## Phase 1 scope (current)

- `schemas/model-manifest.schema.json` — the root `model.yaml` manifest contract (§22): identity, version, contract handshake, components, dependencies, compatibility (§15/§17).
- `scripts/validate_handshake.py` — Level 2 basic: validate a model repository's `model.yaml` against the manifest schema + verify the handshake names a known contract family (Annex A inventory).
- `scripts/check_immutable_refs.py` — reusable guard: every external reference in a manifest (components, dependencies) must be immutable (tag `vX.Y.Z`, commit SHA, or digest — never `main`/`latest`).
- `fixtures/` — positive + negative controls proving the validators can both pass and fail.
- Self-test CI running the validators against the fixtures on every PR.

## Phase 2 additions (current)

- `scripts/resolve_contract.py` — Level 2 full: resolves a model's handshake against the **published contract suite** from a pinned dea-metamodel checkout. Family id must exist in the suite; declared version must be compatible (exact, `1.x` wildcard, `^1.0` caret, or `1`/`1.0` prefix of the published X.Y.Z).
- `.github/workflows/contract-conformance.yml` — **reusable `workflow_call` workflow** for model repositories:

  ```yaml
  jobs:
    contract-conformance:
      uses: Assessment-Models/assessment-ci/.github/workflows/contract-conformance.yml@main
      with:
        dea-metamodel-ref: v1.0.0   # immutable tag or SHA — never main/latest
        manifest-path: model.yaml   # optional
  ```

  It runs the full Level 2 chain: manifest schema + handshake shape, immutable-reference guard, and resolution against the contract suite at the caller's pin. The `dea-metamodel-ref` input is guarded — mutable refs fail the job.
- Self-test CI resolves the fixtures against the **live** suite on `dea-metamodel@main` (positive + version-mismatch negative).

## Phase 4 additions (current)

- `scripts/validate_ecosystem.py` — Level 3 full: validates the registry's live population — immutable release refs, dependency ids resolve to registered assets, and manifest coherence (each asset's `model.yaml` at its pinned release must agree with its registration record on id, type, version, and contract handshake). Assets without a `model.yaml` (legacy catalogs/umbrellas) are reported as informational.
- `validate-ecosystem` self-test job — checks out `Assessment-Models/assessment-registry@main` and runs Level 3 validation against the live population on every PR.
- Cross-repo fan-out stays `workflow_dispatch`-only until the org-level dispatch credential exists (Phase 1 prerequisite, §13 note).

## Later phases

- Cross-repo fan-out: trigger ecosystem CI in every registered model repo on registry changes, once the org-level dispatch credential exists.
- Cross-repo fan-out stays `workflow_dispatch`-only until the org-level dispatch credential exists (Phase 1 prerequisite, §13 note).

---

*Established under [CR-AM-11 — Federated Assessment Model Ecosystem](https://github.com/technehub-labs/dea-metamodel/blob/main/change-requests/CR-AM-11.md) Phase 1.*
