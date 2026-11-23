from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.validate_touchpoints import validate_manifest_touchpoints


class ValidateTouchpointsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.manifest = self.root / "model.yaml"
        self.schema = self.root / "schema.json"
        self.suite = self.root / "contract-suite.yaml"
        self.schema.write_text(json.dumps({
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["id", "repo_id", "version", "status", "touchpoints"],
            "properties": {
                "id": {"type": "string"},
                "repo_id": {"type": "string"},
                "version": {"type": "string"},
                "status": {"enum": ["draft", "stable"]},
                "touchpoints": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "peer_asset", "peer_repo", "direction", "mapping_type", "reciprocity"],
                        "properties": {
                            "id": {"type": "string"},
                            "mirrors": {"type": "string", "minLength": 1},
                            "peer_touchpoint_id": {"type": "string", "minLength": 1},
                            "peer_asset": {"type": "string"},
                            "peer_repo": {"type": "string"},
                            "direction": {"type": "string"},
                            "mapping_type": {"type": "string"},
                            "reciprocity": {"type": "string", "pattern": "^mirrors-[a-z0-9]+(-[a-z0-9]+)*$"}
                        },
                        "allOf": [
                            {"if": {"required": ["mirrors"]}, "then": {"required": ["peer_touchpoint_id"]}},
                            {"if": {"required": ["peer_touchpoint_id"]}, "then": {"required": ["mirrors"]}}
                        ]
                    }
                }
            }
        }))
        self.suite.write_text(yaml.safe_dump({
            "families": [{"id": "maturity-touchpoint-contract", "version": "0.1.0-draft"}]
        }))

    def tearDown(self):
        self.tmp.cleanup()

    def write_manifest(self, declaration=None):
        doc = {"id": "fixture-model"}
        if declaration is not None:
            doc["touchpoints"] = {"declaration": declaration}
        self.manifest.write_text(yaml.safe_dump(doc))

    def write_touchpoints(self, record=None, contract_version="0.1.0-draft"):
        doc = {
            "id": "dea:touchpoints-fixture-v1",
            "repo_id": "fixture-model",
            "version": "0.1.0",
            "status": "draft",
            "contract": {
                "id": "maturity-touchpoint-contract",
                "version": contract_version,
                "source": {"organization": "technehub-labs", "repository": "dea-metamodel"}
            },
            "touchpoints": [record or {
                "id": "tp-fixture-source",
                "mirrors": "tp-fixture-peer",
                "peer_touchpoint_id": "tp-fixture-peer",
                "peer_asset": "dea:maturity-peer",
                "peer_repo": "maturity-model-peer",
                "direction": "feeds",
                "mapping_type": "feeds",
                "reciprocity": "mirrors-tp-fixture-peer"
            }]
        }
        (self.root / "touchpoints.yaml").write_text(yaml.safe_dump(doc))

    def test_optional_declaration_is_skipped(self):
        self.write_manifest()
        errors, skipped = validate_manifest_touchpoints(self.manifest, self.schema, self.suite)
        self.assertEqual(errors, [])
        self.assertTrue(skipped)

    def test_valid_declaration_passes(self):
        self.write_manifest("touchpoints.yaml")
        self.write_touchpoints()
        errors, skipped = validate_manifest_touchpoints(self.manifest, self.schema, self.suite)
        self.assertEqual(errors, [])
        self.assertFalse(skipped)

    def test_unpaired_mirror_is_rejected(self):
        self.write_manifest("touchpoints.yaml")
        self.write_touchpoints(record={
            "id": "tp-fixture-source",
            "mirrors": "tp-fixture-peer",
            "peer_asset": "dea:maturity-peer",
            "peer_repo": "maturity-model-peer",
            "direction": "feeds",
            "mapping_type": "feeds",
            "reciprocity": "mirrors-tp-fixture-peer"
        })
        errors, _ = validate_manifest_touchpoints(self.manifest, self.schema, self.suite)
        self.assertTrue(any("peer_touchpoint_id" in error for error in errors))

    def test_invalid_reciprocity_is_rejected(self):
        self.write_manifest("touchpoints.yaml")
        self.write_touchpoints(record={
            "id": "tp-fixture-source",
            "mirrors": "tp-fixture-peer",
            "peer_touchpoint_id": "tp-fixture-peer",
            "peer_asset": "dea:maturity-peer",
            "peer_repo": "maturity-model-peer",
            "direction": "feeds",
            "mapping_type": "feeds",
            "reciprocity": "required"
        })
        errors, _ = validate_manifest_touchpoints(self.manifest, self.schema, self.suite)
        self.assertTrue(any("reciprocity" in error for error in errors))

    def test_contract_version_must_match_pinned_suite(self):
        self.write_manifest("touchpoints.yaml")
        self.write_touchpoints(contract_version="0.1.0")
        errors, _ = validate_manifest_touchpoints(self.manifest, self.schema, self.suite)
        self.assertTrue(any("publishes" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
