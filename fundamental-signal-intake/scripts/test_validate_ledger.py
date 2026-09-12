import unittest

from validate_ledger import validate


def record(**updates):
    base = {
        "record_id": "r1",
        "entity": "Issuer",
        "business_line": "Core",
        "supply_chain_stage": "downstream",
        "metric": "orders",
        "value": 10,
        "unit": "units",
        "geography": "CN",
        "product_or_project": "Product A",
        "counterparty": "Customer A",
        "observed_at": "2026-01-01T00:00:00Z",
        "published_at": "2026-01-02T00:00:00Z",
        "collected_at": "2026-01-03T00:00:00Z",
        "available_at": "2026-01-02T00:00:00Z",
        "vintage_at": "2026-01-02T00:00:00Z",
        "vintage_id": "original",
        "snapshot_reference": "fixture://original",
        "source_group": "original-publisher",
        "driver": "quantity", "scope": "CN/Product-A", "coverage": 1,
        "source_kind": "fundamental",
        "source_title": "Primary record",
        "source_publisher": "Publisher",
        "source_url_or_file": "https://example.invalid/source",
        "source_excerpt": "Ten units were ordered.",
        "evidence_class": "primary_confirmation",
        "confidence": "high",
        "cross_checks": [],
        "status": "confirmed",
        "notes": "Direct primary record.",
    }
    base.update(updates)
    return base


class LedgerValidationTest(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate({"as_of": "2026-01-03T00:00:00Z", "records": [record()]}), [])

    def test_rejects_lookahead(self):
        errors = validate({"as_of": "2026-01-01T00:00:00Z", "records": [record()]})
        self.assertTrue(any("look-ahead" in error for error in errors))

    def test_rejects_duplicate(self):
        errors = validate({"as_of": "2026-01-03T00:00:00Z", "records": [record(), record()]})
        self.assertTrue(any("duplicate" in error for error in errors))

    def test_rejects_missing_minimum_field(self):
        item = record()
        del item["source_excerpt"]
        errors = validate({"as_of": "2026-01-03T00:00:00Z", "records": [item]})
        self.assertTrue(any("source_excerpt" in error for error in errors))

    def test_rejects_null_value_disguised_as_fact(self):
        errors = validate({"as_of": "2026-01-03T00:00:00Z", "records": [record(value=None)]})
        self.assertTrue(any("value cannot be null" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

