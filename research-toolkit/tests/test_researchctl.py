import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "researchctl.py"
SPEC = importlib.util.spec_from_file_location("researchctl", SCRIPT)
researchctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(researchctl)


class ResearchCtlTests(unittest.TestCase):
    def test_clean_doi(self):
        self.assertEqual(researchctl.clean_doi("https://doi.org/10.1000/ABC"), "10.1000/abc")

    def test_strip_jats_markup(self):
        value = "<jats:title>Abstract</jats:title><jats:p>A &amp; B</jats:p>"
        self.assertEqual(researchctl.strip_markup(value), "Abstract A & B")

    def test_crossref_link_is_not_assumed_open_access(self):
        item = {
            "title": ["Example"],
            "DOI": "10.1000/example",
            "link": [{"URL": "https://publisher.example/paper.pdf", "content-version": "vor"}],
        }
        record = researchctl.crossref_record(item)
        self.assertIsNone(record["open_access"]["is_oa"])
        self.assertIn("https://publisher.example/paper.pdf", record["urls"])

    def test_dedupe_prefers_identifiers_and_merges_sources(self):
        first = researchctl.base_record(
            "openalex",
            title="A Test Paper",
            year=2024,
            identifiers={"doi": "10.1000/test"},
            abstract="short",
        )
        second = researchctl.base_record(
            "crossref",
            title="A test paper",
            year=2024,
            identifiers={"doi": "10.1000/test"},
            abstract="a much longer abstract",
        )
        result = researchctl.deduplicate([first, second])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sources"], ["openalex", "crossref"])
        self.assertEqual(result[0]["abstract"], "a much longer abstract")

    def test_same_title_different_year_is_not_merged(self):
        one = researchctl.base_record("a", title="Repeated Title", year=2020)
        two = researchctl.base_record("b", title="Repeated Title", year=2021)
        self.assertEqual(len(researchctl.deduplicate([one, two])), 2)

    def test_cli_dedupe_offline_fixture(self):
        records = [
            {"title": "Unicode：Test", "year": 2024, "identifiers": {}, "sources": ["a"]},
            {"title": "Unicode: Test", "year": 2024, "identifiers": {}, "sources": ["b"]},
        ]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.json"
            target = Path(directory) / "output.json"
            source.write_text(json.dumps(records), encoding="utf-8")
            status = researchctl.main(["dedupe", "--input", str(source), "--output", str(target)])
            payload = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(status, 0)
        self.assertEqual(len(payload["records"]), 1)
        self.assertEqual(payload["schema_version"], "1.0")


if __name__ == "__main__":
    unittest.main()
