import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_a_share.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SPEC = importlib.util.spec_from_file_location("verify_a_share", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class VerifyAShareTests(unittest.TestCase):
    def run_fixture(self, name):
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPT), str(FIXTURES / name), "--json"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return result, json.loads(result.stdout)

    def test_complete_a_share_intake_has_no_errors(self):
        result, payload = self.run_fixture("a-share-valid.json")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(0, payload["counts"]["error"])

    def test_missing_a_share_evidence_fails(self):
        result, payload = self.run_fixture("a-share-invalid.json")
        self.assertEqual(1, result.returncode)
        rule_ids = {item["rule_id"] for item in payload["findings"]}
        self.assertIn("A_SHARE_EXCHANGE", rule_ids)
        self.assertIn("A_SHARE_PRIMARY_SOURCES", rule_ids)
        self.assertIn("A_SHARE_CHECK_MISSING", rule_ids)
        self.assertIn("SOURCE_TIER_HEADLINE_AGGREGATOR", rule_ids)

    def test_template_is_json(self):
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPT), "--template"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("CN-A", json.loads(result.stdout)["market_profile"])

    def test_ttm_requires_explicit_bridge(self):
        doc = json.loads((FIXTURES / "a-share-valid.json").read_text(encoding="utf-8"))
        doc["datapoints"][0]["period"] = "TTM to H1 2026"
        findings = MODULE.check_a_share(doc)
        self.assertIn("A_SHARE_TTM_BRIDGE", {item.rule_id for item in findings})


if __name__ == "__main__":
    unittest.main()
