# Changelog

## [Unreleased] — CR-AM-11 Phase 1: Integration spine (CI half)

### Added
- Repository scaffold (CR-AM-11 §13): validation machinery only, no model content.
- `schemas/model-manifest.schema.json` — the root `model.yaml` contract (§22) including the §15 contract handshake, §20 component references (kind: import/extend/override), and §17 compatibility declarations.
- `scripts/validate_handshake.py` — Level 2 basic: manifest schema validation + known-contract-family check (Annex A inventory) + canonical-source check.
- `scripts/check_immutable_refs.py` — reusable immutable-reference guard (rejects `main`/`master`/`latest`/`HEAD`).
- `fixtures/` positive + negative controls; self-test CI asserts the valid fixture passes and every invalid fixture is rejected.
