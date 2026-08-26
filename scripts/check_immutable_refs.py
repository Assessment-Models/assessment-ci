#!/usr/bin/env python3
"""Reusable immutable-reference guard (CR-AM-11 §12/§20).

Usage:
  python scripts/check_immutable_refs.py <path-to-model.yaml>

Every external reference declared in the manifest — component references and
dependency references — must be immutable: a release tag (vX.Y.Z), a 40-char
commit SHA, or a sha256 digest. main / master / latest / HEAD are rejected.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

MUTABLE_REFS = {"main", "master", "latest", "HEAD", "head"}
IMMUTABLE_PATTERNS = (
    re.compile(r"^v\d+\.\d+\.\d+(-[a-z0-9.-]+)?$"),
    re.compile(r"^[0-9a-f]{40}$"),
    re.compile(r"^sha256:[0-9a-f]{64}$"),
)


def is_immutable(ref: str) -> bool:
    if ref in MUTABLE_REFS:
        return False
    return any(p.match(ref) for p in IMMUTABLE_PATTERNS)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_immutable_refs.py <path-to-model.yaml>")
        return 2
    path = Path(sys.argv[1])
    doc = yaml.safe_load(path.read_text())
    errors: list[str] = []

    if isinstance(doc, dict):
        for section in ("components", "dependencies"):
            for entry in doc.get(section) or []:
                ref = entry.get("reference", "")
                if not isinstance(ref, str) or not ref:
                    errors.append(f"{section}: {entry.get('id')!r}: missing reference")
                elif not is_immutable(ref):
                    errors.append(
                        f"{section}: {entry.get('id')!r}: reference {ref!r} is not immutable "
                        "(tag vX.Y.Z, 40-char SHA, or sha256 digest required)"
                    )

    if errors:
        print(f"FAIL — {path}:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK — {path}: all external references immutable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
