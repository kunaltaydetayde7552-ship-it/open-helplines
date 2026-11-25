#!/usr/bin/env python3
"""Fetch every cited source and check its quoted numbers still appear on the page.

    python3 scripts/check_sources.py                  # all files
    python3 scripts/check_sources.py data/countries/GB.json
    python3 scripts/check_sources.py --markdown report.md

This is advisory, not a merge gate: some sites block bots or render with
JavaScript. A failure means "a human should look", not "the data is wrong".
It runs weekly in CI and opens an issue listing anything that needs re-checking.
"""
import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "countries"
UA = "Mozilla/5.0 (compatible; open-helplines-source-check; +https://github.com/mpatel-playground/open-helplines)"


def page_text(url, cache):
    if url not in cache:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                raw = r.read(3_000_000).decode("utf-8", errors="replace")
            text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
            cache[url] = (None, re.sub(r"\D", "", text))
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
            cache[url] = (f"could not fetch ({e.__class__.__name__}: {e})", "")
    return cache[url]


def numbers_for(entry):
    return [c["value"].lstrip("+") for c in entry.get("contacts", [])
            if c.get("type") in {"phone", "sms", "whatsapp"}]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--markdown", help="write a markdown report here")
    args = ap.parse_args()
    files = [Path(f) for f in args.files] or sorted(DATA_DIR.glob("*.json"))

    cache, problems, checked = {}, [], 0
    for path in files:
        doc = json.loads(path.read_text(encoding="utf-8"))
        items = [(h["id"], numbers_for(h), h.get("sources", [])) for h in doc["helplines"]]
        items += [(f"{doc['country'].lower()}-emergency-{e['number']}", [e["number"]], e["sources"])
                  for e in doc.get("emergency", [])]
        for item_id, numbers, sources in items:
            for s in sources:
                checked += 1
                err, digits = page_text(s["url"], cache)
                if err:
                    problems.append((doc["country"], item_id, s["url"], err))
                    continue
                missing = [n for n in numbers if n not in digits]
                # Numbers stored with a country code (e.g. +44...) may appear
                # without it on the page, so also try dropping 1-3 leading digits.
                missing = [n for n in missing if not any(len(n) - i >= 7 and n[i:] in digits
                                                         for i in range(1, 4))]
                if missing:
                    problems.append((doc["country"], item_id, s["url"],
                                     f"number(s) {', '.join(missing)} not found in page text"))

    lines = [f"Checked {checked} source citation(s); {len(problems)} need a human look."]
    for country, item_id, url, why in problems:
        lines.append(f"- [ ] **{country}** `{item_id}`: {why} <{url}>")
    out = "\n".join(lines)
    print(out)
    if args.markdown:
        Path(args.markdown).write_text(out + "\n", encoding="utf-8")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
