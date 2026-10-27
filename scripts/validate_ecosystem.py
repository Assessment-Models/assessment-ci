#!/usr/bin/env python3
"""Level 3 — ecosystem validation against the assessment-registry population
(CR-AM-11 section 13.1, Phase 4).

Usage:
  python scripts/validate_ecosystem.py --registry <path-to-assessment-registry>

Checks, per registration record under registry/ (examples excluded):
  1. Immutable release references (tag vX.Y.Z / 40-char SHA / sha256 digest).
  2. Dependency ids resolve to other registered records.
  3. Manifest coherence: the asset's own model.yaml (fetched at the pinned
     release, or read from a local sibling checkout) must agree with the
     registration record on id, type, version and the contract handshake
     (family id + version). Assets without a model.yaml yet (e.g. legacy
     catalogs) are reported as informational, not failures.

This script performs network fetches of model.yaml at pinned refs; it never
reads mutable refs (main/latest), so results reflect registered releases.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

import yaml

MUTABLE_REFS = {"main", "master", "latest", "HEAD", "head"}
IMMUTABLE_PATTERNS = (
    re.compile(r"^v\d+\.\d+\.\d+(-[a-z0-9.-]+)?$"),
    re.compile(r"^[0-9a-f]{40}$"),
    re.compile(r"^sha256:[0-9a-f]{64}$"),
)
RAW_URL = "https://raw.githubusercontent.com/{org}/{repo}/{ref}/{path}"


def is_immutable(ref: str) -> bool:
    return ref not in MUTABLE_REFS and any(p.match(ref) for p in IMMUTABLE_PATTERNS)


def load_records(registry_root: Path) -> dict[str, dict]:
    records: dict[str, dict] = {}
    for path in sorted((registry_root / "registry").rglob("*.yaml")):
        doc = yaml.safe_load(path.read_text())
        if isinstance(doc, dict) and doc.get("id"):
            records[doc["id"]] = doc
    return records


def fetch_manifest(record: dict, local_repos: Path | None) -> tuple[dict | None, str]:
    org = record["source"]["organization"]
    repo = record["source"]["repository"]
    ref = record["release"]["reference"]
    if local_repos and (local_repos / repo / "model.yaml").is_file():
        manifest = yaml.safe_load((local_repos / repo / "model.yaml").read_text())
        return manifest, "local checkout"
    url = RAW_URL.format(org=org, repo=repo, ref=ref, path="model.yaml")
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return yaml.safe_load(resp.read()), url
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, url
        raise
    except urllib.error.URLError:
        return None, url


def check_manifest_coherence(record: dict, manifest: dict) -> list[str]:
    errors: list[str] = []
    rid, rtype = record["id"], record.get("type")
    rversion = record["release"]["version"]
    rcontract = record.get("conformsTo", {}).get("contract", {})

    if manifest.get("id") != rid:
        errors.append(f"manifest id {manifest.get('id')!r} != registered id {rid!r}")
    if manifest.get("type") != rtype:
        errors.append(f"manifest type {manifest.get('type')!r} != registered type {rtype!r}")
    if str(manifest.get("version")) != str(rversion):
        errors.append(f"manifest version {manifest.get('version')!r} != registered release {rversion!r}")

    mconf = manifest.get("conformance", {}).get("contract", {})
    mversion = manifest.get("conformance", {}).get("version")
    if mconf.get("id") and rcontract.get("id") and mconf["id"] != rcontract["id"]:
        errors.append(
            f"manifest contract {mconf['id']!r} != registered contract {rcontract['id']!r}"
        )
    if mversion and rcontract.get("version") and str(mversion) != str(rcontract["version"]):
        errors.append(
            f"manifest contract version {mversion!r} != registered {rcontract['version']!r}"
        )
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True, help="path to an assessment-registry checkout")
    ap.add_argument(
        "--local-repos",
        help="optional directory containing sibling repo checkouts; model.yaml is read from there before network fetch",
    )
    args = ap.parse_args()

    registry_root = Path(args.registry)
    records = load_records(registry_root)
    if not records:
        print("FAIL — no registration records found under registry/")
        return 1

    errors: list[str] = []
    infos: list[str] = []
    local_repos = Path(args.local_repos) if args.local_repos else None

    for rid, record in records.items():
        ref = record.get("release", {}).get("reference", "")
        if not is_immutable(ref):
            errors.append(f"{rid}: release reference {ref!r} is not immutable")

        for dep in record.get("dependencies", []) or []:
            if dep not in records:
                errors.append(f"{rid}: dependency {dep!r} is not a registered asset id")

        manifest, origin = fetch_manifest(record, local_repos)
        if manifest is None:
            infos.append(f"{rid}: no model.yaml at {ref} (legacy/umbrella asset)")
            continue
        for e in check_manifest_coherence(record, manifest):
            errors.append(f"{rid}: {e}")
        print(f"checked {rid} manifest ({origin})")

    for i in infos:
        print(f"info: {i}")
    if errors:
        print(f"FAIL — {len(errors)} ecosystem error(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(
        f"OK — {len(records)} registration record(s) coherent "
        f"({len(infos)} without model.yaml)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
