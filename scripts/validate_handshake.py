#!/usr/bin/env python3
"""Level 2 (basic) — validate a model repository's contract handshake.

Usage:
  python scripts/validate_handshake.py <path-to-model.yaml>

Checks:
  1. model.yaml conforms to schemas/model-manifest.schema.json (CR-AM-11 §22)
  2. The handshake (§15) names a KNOWN OpenDEA contract family
     (CR-AM-11 Annex A inventory) — typos in the contract id are caught here
  3. The handshake source is the canonical engineering authority
     (technehub-labs/dea-metamodel)
  4. An optional touchpoint declaration is a safe repository-relative YAML path
     and resolves to an existing file; its record semantics remain separate

Exit 0 with OK when valid; exit 1 listing every failure otherwise.
"""
from __future__ import annotations

import sys
from pathlib import Path, PurePosixPath

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = yaml.safe_load((ROOT / "schemas" / "model-manifest.schema.json").read_text())

# Known contract families (CR-AM-11 section 16 / Annex A). The top-level
# metamodel contract plus the six independently-identifiable families.
KNOWN_CONTRACT_IDS = {
    "opendea-assessment-metamodel",
    "assessment-contract",
    "maturity-model-contract",
    "maturity-scale-contract",
    "scoring-contract",
    "conformance-contract",
    "benchmark-contract",
}

CANONICAL_SOURCE = ("technehub-labs", "dea-metamodel")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_handshake.py <path-to-model.yaml>")
        return 2
    path = Path(sys.argv[1])
    errors: list[str] = []
    doc = yaml.safe_load(path.read_text())

    # Optional relationship-artifact declaration. The manifest schema checks
    # its shape; this check ensures the repository-relative target is safe and
    # exists. Touchpoint record semantics remain governed by their own contract
    # and ecosystem validation, not by free-form manifest metadata.
    touchpoints = (doc or {}).get("touchpoints") if isinstance(doc, dict) else None
    if touchpoints is not None:
        declaration = touchpoints.get("declaration") if isinstance(touchpoints, dict) else None
        if not isinstance(declaration, str) or not declaration.strip():
            errors.append("touchpoints: declaration must be a non-empty repository-relative YAML path")
        else:
            relative = PurePosixPath(declaration)
            if (
                relative.is_absolute()
                or "\\" in declaration
                or ".." in relative.parts
                or relative.suffix.lower() not in {".yaml", ".yml"}
                or not relative.parts
            ):
                errors.append("touchpoints: declaration must be a safe repository-relative YAML path (no absolute path or parent traversal)")
            else:
                repository_root = path.resolve().parent
                target = (repository_root / Path(*relative.parts)).resolve()
                try:
                    target.relative_to(repository_root)
                except ValueError:
                    errors.append("touchpoints: declaration resolves outside the model repository")
                else:
                    if not target.is_file():
                        errors.append(f"touchpoints: declared file does not exist: {declaration}")

    for err in sorted(
        jsonschema.Draft202012Validator(SCHEMA).iter_errors(doc),
        key=lambda e: list(e.path),
    ):
        errors.append(f"schema: {'/'.join(map(str, err.path)) or '<root>'}: {err.message}")

    if isinstance(doc, dict):
        conf = doc.get("conformance") or {}
        cid = (conf.get("contract") or {}).get("id", "")
        if cid and cid not in KNOWN_CONTRACT_IDS:
            errors.append(
                f"handshake: contract id {cid!r} is not a known OpenDEA contract family "
                f"(known: {sorted(KNOWN_CONTRACT_IDS)})"
            )
        src = conf.get("source") or {}
        org_repo = (src.get("organization"), src.get("repository"))
        if all(org_repo) and org_repo != CANONICAL_SOURCE:
            errors.append(
                f"handshake: contract source {org_repo} is not the canonical engineering "
                f"authority {CANONICAL_SOURCE}"
            )

    if errors:
        print(f"FAIL — {path}:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK — {path}: manifest, handshake and optional touchpoint declaration valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
