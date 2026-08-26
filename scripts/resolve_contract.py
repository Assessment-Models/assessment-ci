#!/usr/bin/env python3
"""Level 2 (full) — resolve a model's contract handshake against the published
OpenDEA contract suite (CR-AM-11 §15–16, Phase 2).

Usage:
  python scripts/resolve_contract.py <model.yaml> --suite <path-to-contract-suite.yaml>

Checks:
  1. The handshake's contract id exists in the published suite — either as a
     family id or as the top-level suite id (opendea-assessment-metamodel
     maps to the suite as a whole)
  2. The declared version is compatible with the published family version:
       exact match ("1.0" vs "1.0")
       major wildcard ("1.x" matches any 1.Y)
       caret range ("^1.0" matches any 1.Y)

The suite file comes from a dea-metamodel checkout at the caller's pinned,
immutable release — this script never fetches; the workflow provides the pin.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

SUITE_ID = "opendea-assessment-contract-suite"
# Alias: the metamodel-level handshake id maps to the whole suite.
SUITE_ALIASES = {"opendea-assessment-metamodel": SUITE_ID}


def version_compatible(declared: str, published: str) -> bool:
    declared = declared.strip()
    published = published.strip()
    if declared == published:
        return True
    pub_parts = published.split(".")
    pub_major = pub_parts[0]
    m = re.match(r"^(\d+)\.x$", declared)          # "1.x"
    if m:
        return m.group(1) == pub_major
    m = re.match(r"^\^(\d+)\.(\d+)$", declared)     # "^1.0"
    if m:
        return m.group(1) == pub_major
    m = re.match(r"^(\d+)(?:\.(\d+))?$", declared)  # "1" or "1.0" — prefix of X.Y.Z
    if m and len(pub_parts) == 3:
        if m.group(2) is None:
            return m.group(1) == pub_parts[0]
        return m.group(1) == pub_parts[0] and m.group(2) == pub_parts[1]
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", help="path to the model repository's model.yaml")
    ap.add_argument("--suite", required=True, help="path to contract-suite.yaml from the pinned dea-metamodel checkout")
    args = ap.parse_args()

    errors: list[str] = []
    manifest = yaml.safe_load(Path(args.manifest).read_text())
    suite = yaml.safe_load(Path(args.suite).read_text())

    conf = (manifest or {}).get("conformance") or {}
    cid = (conf.get("contract") or {}).get("id", "")
    declared_version = str(conf.get("version", ""))

    families = {f.get("id"): f for f in suite.get("families") or []}
    suite_version = str(suite.get("version", ""))

    resolved_id = SUITE_ALIASES.get(cid, cid)

    if resolved_id == SUITE_ID:
        published_version = suite_version
        target = f"suite {SUITE_ID}"
    elif resolved_id in families:
        published_version = str(families[resolved_id].get("version", ""))
        target = f"family {resolved_id}"
    else:
        errors.append(
            f"contract id {cid!r} does not resolve in the published suite "
            f"(families: {sorted(families)}; suite: {SUITE_ID})"
        )
        published_version, target = "", ""

    if not errors and not version_compatible(declared_version, published_version):
        errors.append(
            f"version mismatch: handshake declares {declared_version!r} but the "
            f"pinned suite publishes {target} at {published_version!r}"
        )

    if errors:
        print(f"FAIL — {args.manifest}:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK — {args.manifest}: handshake {cid}@{declared_version} resolves "
          f"against {target} v{published_version} (suite v{suite_version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
