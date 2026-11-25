"""Tests for scripts/validate.py. Run: python3 -m unittest discover tests"""
import copy
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import validate  # noqa: E402

TODAY = dt.date(2026, 11, 24)

GOOD = {
    "country": "ZZ",
    "name": "Testland",
    "emergency": [{"number": "112", "sources": [
        {"url": "https://gov.example/", "type": "government",
         "accessed": "2026-11-01", "quote": "In an emergency call 112"}]}],
    "helplines": [{
        "id": "zz-test-line",
        "name": "Test Line",
        "categories": ["suicide"],
        "audiences": ["everyone"],
        "contacts": [{"type": "phone", "value": "116123", "display": "116 123"}],
        "availability": "24/7",
        "cost": "free",
        "sources": [{"url": "https://line.example/", "type": "operator",
                     "accessed": "2026-11-01", "quote": "Call us free on 116 123"}],
        "status": "provisional",
        "last_verified": "2026-11-01",
    }],
}


def run(doc, name=None):
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / f"{name or doc.get('country', 'XX')}.json"
        path.write_text(json.dumps(doc))
        rep = validate.Report()
        validate.check_file(rep, path, TODAY, {})
        return rep


def mutate(fn):
    doc = copy.deepcopy(GOOD)
    fn(doc)
    return doc


class ValidateTests(unittest.TestCase):
    def assertErrorContains(self, rep, text):
        self.assertTrue(any(text in e for e in rep.errors),
                        f"expected an error containing {text!r}, got {rep.errors}")

    def test_good_file_passes(self):
        rep = run(GOOD)
        self.assertEqual(rep.errors, [])

    def test_filename_must_match_country(self):
        self.assertErrorContains(run(GOOD, name="US"), "file name must be ZZ.json")

    def test_number_must_appear_in_quote(self):
        doc = mutate(lambda d: d["helplines"][0]["contacts"][0].update(value="999999"))
        self.assertErrorContains(run(doc), "does not appear in any source quote")

    def test_number_with_country_code_matches_local_quote(self):
        doc = mutate(lambda d: d["helplines"][0]["contacts"][0].update(value="+44116123"))
        self.assertEqual(run(doc).errors, [])

    def test_quote_required(self):
        doc = mutate(lambda d: d["helplines"][0]["sources"][0].pop("quote"))
        self.assertErrorContains(run(doc), "quote is required")

    def test_number_must_be_digits(self):
        doc = mutate(lambda d: d["helplines"][0]["contacts"][0].update(value="116 123"))
        self.assertErrorContains(run(doc), "value must be digits only")

    def test_verified_needs_two_domains(self):
        doc = mutate(lambda d: d["helplines"][0].update(status="verified"))
        self.assertErrorContains(run(doc), "at least two different websites")

    def test_verified_with_two_domains_passes(self):
        def f(d):
            h = d["helplines"][0]
            h["status"] = "verified"
            h["sources"].append({"url": "https://www.gov.example/help", "type": "government",
                                 "accessed": "2026-11-02", "quote": "116 123"})
        self.assertEqual(run(mutate(f)).errors, [])

    def test_http_url_rejected(self):
        doc = mutate(lambda d: d["helplines"][0]["sources"][0].update(url="http://x.example/"))
        self.assertErrorContains(run(doc), "https://")

    def test_future_dates_rejected(self):
        doc = mutate(lambda d: d["helplines"][0].update(last_verified="2030-01-01"))
        self.assertErrorContains(run(doc), "in the future")

    def test_unknown_category_rejected(self):
        doc = mutate(lambda d: d["helplines"][0].update(categories=["sadness"]))
        self.assertErrorContains(run(doc), "unknown categories")

    def test_unknown_field_rejected(self):
        doc = mutate(lambda d: d["helplines"][0].update(phone="116123"))
        self.assertErrorContains(run(doc), "unknown fields")

    def test_id_must_be_prefixed_with_country(self):
        doc = mutate(lambda d: d["helplines"][0].update(id="us-test-line"))
        self.assertErrorContains(run(doc), "must start with 'zz-'")

    def test_duplicate_ids_rejected(self):
        doc = mutate(lambda d: d["helplines"].append(copy.deepcopy(d["helplines"][0])))
        self.assertErrorContains(run(doc), "duplicate id")

    def test_emergency_number_needs_quote(self):
        doc = mutate(lambda d: d["emergency"][0]["sources"][0].update(quote="call us"))
        self.assertErrorContains(run(doc), "emergency number 112")

    def test_stale_entry_warns(self):
        doc = mutate(lambda d: d["helplines"][0].update(last_verified="2024-01-01"))
        rep = run(doc)
        self.assertEqual(rep.errors, [])
        self.assertTrue(rep.warnings)

    def test_repository_data_is_valid(self):
        self.assertEqual(validate.main([]), 0)


if __name__ == "__main__":
    unittest.main()
