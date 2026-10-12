import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("governance", Path(__file__).parents[1] / "lint_skill_governance.py")
governance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(governance)

class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.skill = self.root / "demo"
        self.skill.mkdir()
        self.write("SKILL.md", "---\nname: demo\ndescription: test capability\n---\n# Demo\n")
    def tearDown(self):
        self.tmp.cleanup()
    def write(self, name, text):
        path = self.skill / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    def errors(self):
        return governance.audit(self.root)["errors"]
    def manifest(self, files=None):
        return {"version": 1, "cases": [{
            "id": "minimal", "kind": "synthetic", "files": files or ["input.json"],
            "scenario": "exercise input contract", "preconditions": "a valid schema",
            "expected": "parsed input", "limits": "not real data",
            "source": "test synthesis", "verified_at": "unknown"}]}
    def test_self_contained_skill_needs_no_empty_resource_directories(self):
        self.assertEqual(self.errors(), [])
    def test_fenced_case_is_detected_and_parameterized_schema_is_allowed(self):
        self.write("references/method.md", "# Method\n## Worked example\n" + chr(96)*3 + "json\n{\"company\":\"Acme\"}\n" + chr(96)*3 + "\n")
        self.assertTrue(any("move example" in x for x in self.errors()))
        self.write("references/method.md", "# Schema\n" + chr(96)*3 + "json\n{\"company\":\"<company-name>\"}\n" + chr(96)*3 + "\n")
        self.assertEqual(self.errors(), [])
    def test_conditional_case_link_and_registered_data_pass(self):
        self.write("example/input.json", "{}")
        self.write("example/index.json", json.dumps(self.manifest()))
        self.write("references/method.md", "# Method\n## Worked example\nOnly when needed: [case](../example/input.json).\n")
        self.assertEqual(self.errors(), [])
    def test_missing_case_and_unregistered_file_fail(self):
        self.write("example/input.json", "{}")
        self.write("example/extra.json", "{}")
        self.write("example/index.json", json.dumps(self.manifest(["missing.json"])))
        self.assertTrue(any("missing example" in x for x in self.errors()))
        self.assertTrue(any("unregistered" in x for x in self.errors()))
    def test_manifest_escape_and_duplicate_id_fail(self):
        m = self.manifest(["../../outside.json"])
        m["cases"].append(dict(m["cases"][0]))
        self.write("example/input.json", "{}")
        self.write("example/index.json", json.dumps(m))
        errors = self.errors()
        self.assertTrue(any("invalid file path" in x for x in errors))
        self.assertTrue(any("duplicate id" in x for x in errors))
    def test_broken_link_and_cross_skill_dependency_fail(self):
        self.write("references/method.md", "# Method\n[absent](missing.md)\n[external local](../../other/file.md)\n")
        errors = self.errors()
        self.assertTrue(any("broken local link" in x for x in errors))
        self.assertTrue(any("leaves installable skill" in x for x in errors))
    def test_test_only_fixtures_and_generated_output_are_not_cases(self):
        self.write("tests/fixtures/input.json", "{}")
        self.write("SKILL.md", "---\nname: demo\ndescription: test\n---\nWrite project " + chr(96) + "assets/output.json" + chr(96) + ".\n")
        self.assertEqual(self.errors(), [])
    def test_legacy_fingerprint_changes_when_source_changes(self):
        self.write("references/method.md", "# Method\n[absent](missing.md)\n")
        issue = self.errors()[0]
        before = governance.fingerprint(self.root, issue)
        self.write("references/method.md", "# Method\n[absent](missing.md)\nChanged instructions.\n")
        self.assertNotEqual(before, governance.fingerprint(self.root, issue))

if __name__ == "__main__":
    unittest.main()
