#!/usr/bin/env python3
"""Level 2 structural validation for a model's optional touchpoint declaration.

Usage:
  python scripts/validate_touchpoints.py <model.yaml> --schema <schema.json> --suite <contract-suite.yaml>

The schema and suite MUST come from the caller's pinned dea-metamodel reference.
This validator proves local structural conformance and contract-pin alignment only;
it does not resolve peers or prove reciprocal relationships.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath

import jsonschema
import yaml

TOUCHPOINT_CONTRACT_ID = "maturity-touchpoint-contract"
CANONICAL_SOURCE = ("technehub-labs", "dea-metamodel")


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_manifest_touchpoints(
    manifest_path: Path, schema_path: Path, suite_path: Path
) -> tuple[list[str], bool]:
    errors: list[str] = []
    manifest = load_yaml(manifest_path)
    if not isinstance(manifest, dict):
        return ["model manifest must contain a YAML object"], False

    declaration_block = manifest.get("touchpoints")
    if declaration_block is None:
        return [], True
    if not isinstance(declaration_block, dict):
        return ["touchpoints must be an object"], False

    declaration = declaration_block.get("declaration")
    if not isinstance(declaration, str) or not declaration.strip():
        return ["touchpoints.declaration must be a non-empty repository-relative YAML path"], False

    relative = PurePosixPath(declaration)
    if (
        relative.is_absolute()
        or "\\" in declaration
        or ".." in relative.parts
        or relative.suffix.lower() not in {".yaml", ".yml"}
        or not relative.parts
    ):
        return ["touchpoints.declaration must be a safe repository-relative YAML path"], False

    repository_root = manifest_path.resolve().parent
    declaration_path = (repository_root / Path(*relative.parts)).resolve()
    try:
        declaration_path.relative_to(repository_root)
    except ValueError:
        return ["touchpoints.declaration resolves outside the model repository"], False
    if not declaration_path.is_file():
        return [f"declared touchpoint file does not exist: {declaration}"], False

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        suite = load_yaml(suite_path)
        touchpoints = load_yaml(declaration_path)
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        return [f"unable to load pinned contract inputs or touchpoint declaration: {exc}"], False

    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(touchpoints), key=lambda e: list(e.path)):
        path = "/".join(map(str, err.path)) or "<root>"
        errors.append(f"schema: {path}: {err.message}")

    if not isinstance(touchpoints, dict):
        return errors or ["touchpoint declaration must contain a YAML object"], False

    if touchpoints.get("repo_id") != manifest.get("id"):
        errors.append(
            f"identity: repo_id {touchpoints.get('repo_id')!r} does not match "
            f"model.yaml id {manifest.get('id')!r}"
        )

    families = {
        family.get("id"): family
        for family in (suite or {}).get("families", [])
        if isinstance(family, dict)
    }
    family = families.get(TOUCHPOINT_CONTRACT_ID)
    if family is None:
        errors.append(
            f"contract suite does not publish required family {TOUCHPOINT_CONTRACT_ID!r}"
        )
    else:
        published_version = str(family.get("version", ""))
        pins: list[dict] = []
        top_pin = touchpoints.get("contract")
        if isinstance(top_pin, dict) and top_pin.get("id") == TOUCHPOINT_CONTRACT_ID:
            pins.append(top_pin)
        for handshake in touchpoints.get("handshakes", []) or []:
            if isinstance(handshake, dict):
                pin = handshake.get("contract")
                if isinstance(pin, dict) and pin.get("id") == TOUCHPOINT_CONTRACT_ID:
                    pins.append(pin)

        if not pins:
            errors.append(
                f"contract: no {TOUCHPOINT_CONTRACT_ID!r} pin found in contract or handshakes"
            )
        for pin in pins:
            declared_version = str(pin.get("version", ""))
            if declared_version != published_version:
                errors.append(
                    f"contract: {TOUCHPOINT_CONTRACT_ID} declares {declared_version!r} "
                    f"but pinned suite publishes {published_version!r}"
                )
            source = pin.get("source")
            if isinstance(source, dict):
                actual_source = (source.get("organization"), source.get("repository"))
                if all(actual_source) and actual_source != CANONICAL_SOURCE:
                    errors.append(
                        f"contract: source {actual_source!r} is not canonical {CANONICAL_SOURCE!r}"
                    )

    return errors, False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path, help="caller repository model.yaml")
    parser.add_argument("--schema", required=True, type=Path, help="schema from pinned dea-metamodel")
    parser.add_argument("--suite", required=True, type=Path, help="contract suite from pinned dea-metamodel")
    args = parser.parse_args()

    errors, skipped = validate_manifest_touchpoints(args.manifest, args.schema, args.suite)
    if skipped:
        print(f"SKIP — {args.manifest}: no touchpoint declaration (optional)")
        return 0
    if errors:
        print(f"FAIL — {args.manifest}:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(
        f"OK — {args.manifest}: touchpoint declaration is structurally valid "
        f"against {TOUCHPOINT_CONTRACT_ID}"
    )
    print("NOTE — structural conformance does not establish peer existence or reciprocity")
    return 0


if __name__ == "__main__":
    sys.exit(main())
