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

## Later phases

- **Phase 2**: contract-version resolution against pinned dea-metamodel releases (reusable `workflow_call` workflow consumed by model repos).
- **Phase 4**: Level 3 ecosystem validation wired to the registry's live population; all three levels demonstrated by the same first model (§31).
- Cross-repo fan-out stays `workflow_dispatch`-only until the org-level dispatch credential exists (Phase 1 prerequisite, §13 note).

---

*Established under [CR-AM-11 — Federated Assessment Model Ecosystem](https://github.com/technehub-labs/dea-metamodel/blob/main/change-requests/CR-AM-11.md) Phase 1.*
