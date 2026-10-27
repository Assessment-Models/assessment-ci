#!/usr/bin/env python3
"""Generate the legacy catalog index view (D-4b) from the registry population.

Usage:
  python scripts/generate_catalog_view.py \
    --registry <path-to-assessment-registry> \
    --index <path-to-assessments/index.yaml>

Reads the legacy v1-alpha index (its catalog header and scoring bands are
hand-maintained umbrella content) and regenerates its `catalog.domains`
block from the registry's live assessment-model records, so the two can
never drift.

With --check: writes nothing; exits non-zero if the regenerated domains
block differs from the committed index (the generated-view CI guard).
Without --check: rewrites the index in place.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO_URL = "https://github.com/{org}/{repo}"
SUPPORTED_TYPES = {"assessment-model": "assessment"}


def load_registry_models(registry_root: Path) -> list[dict]:
    records = []
    base = registry_root / "registry" / "assessment-models"
    for path in sorted(base.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text())
        if isinstance(doc, dict) and doc.get("type") in SUPPORTED_TYPES:
            records.append(doc)
    return records


def domain_entry(record: dict) -> dict:
    src = record["source"]
    domain = src["repository"].removeprefix("dea-assessment-")
    return {
        "id": domain,
        "name": record["name"].replace(" Assessment", "").replace(" (legacy v1-alpha)", "").strip(),
        "repository": REPO_URL.format(org=src["organization"], repo=src["repository"]),
        "registry_id": record["id"],
        "registry_status": record["status"],
        "registered_release": record["release"]["version"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True, help="path to an assessment-registry checkout")
    ap.add_argument("--index", required=True, help="path to the legacy assessments/index.yaml")
    ap.add_argument("--check", action="store_true", help="verify only; fail on drift")
    args = ap.parse_args()

    index_path = Path(args.index)
    doc = yaml.safe_load(index_path.read_text())
    catalog = doc.get("catalog")
    if not catalog or not isinstance(catalog, dict):
        print("FAIL — index has no catalog block")
        return 1

    records = load_registry_models(Path(args.registry))
    if not records:
        print("FAIL — no assessment-model records found in the registry")
        return 1

    domains = [domain_entry(r) for r in sorted(records, key=lambda d: d["source"]["repository"])]
    old_domains = catalog.get("domains", [])

    if args.check:
        if domains == old_domains:
            print(f"OK — index domains match the registry ({len(domains)} entries)")
            return 0
        print("FAIL — index domains drifted from the registry:")
        print(f"  index:   {[d.get('id') for d in old_domains]}")
        print(f"  registry: {[d['id'] for d in domains]}")
        return 1

    catalog["domains"] = domains
    header = [
        line for line in index_path.read_text().splitlines() if line.startswith("#")
    ]
    body = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True)
    index_path.write_text("\n".join(header) + "\n\n" + body + "\n")
    print(f"OK — regenerated {len(domains)} domain entries into {index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
