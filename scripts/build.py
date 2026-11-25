#!/usr/bin/env python3
"""Build the static JSON API into dist/ (published to GitHub Pages).

    python3 scripts/build.py

Output:
    dist/v1/index.json            list of countries with counts
    dist/v1/all.json              every country in one file
    dist/v1/countries/<CC>.json   one country
    dist/index.html               the human-facing lookup page
"""
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "countries"
DIST = ROOT / "dist"
SCHEMA_VERSION = 1


def main():
    sys.path.insert(0, str(ROOT / "scripts"))
    import validate
    if validate.main([]) != 0:
        print("Refusing to build: fix validation errors first.")
        return 1

    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "v1" / "countries").mkdir(parents=True)

    built_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    meta = {
        "schema_version": SCHEMA_VERSION,
        "built_at": built_at,
        "license": "CC0-1.0",
        "source": "https://github.com/mpatel-playground/open-helplines",
        "disclaimer": "Not an emergency service. If someone is in immediate danger, "
                      "call the local emergency number. Entries marked 'provisional' "
                      "have a single source; verify before relying on them.",
    }

    countries, index = {}, []
    for path in sorted(DATA_DIR.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        countries[doc["country"]] = doc
        (DIST / "v1" / "countries" / path.name).write_text(
            json.dumps({**meta, **doc}, ensure_ascii=False, indent=2), encoding="utf-8")
        hl = doc["helplines"]
        index.append({
            "country": doc["country"],
            "name": doc["name"],
            "helplines": len(hl),
            "verified": sum(1 for h in hl if h["status"] == "verified"),
            "emergency": [e["number"] for e in doc.get("emergency", [])],
            "url": f"v1/countries/{path.name}",
        })

    (DIST / "v1" / "index.json").write_text(
        json.dumps({**meta, "countries": index}, ensure_ascii=False, indent=2), encoding="utf-8")
    (DIST / "v1" / "all.json").write_text(
        json.dumps({**meta, "countries": countries}, ensure_ascii=False), encoding="utf-8")
    shutil.copy(ROOT / "site" / "index.html", DIST / "index.html")
    (DIST / ".nojekyll").write_text("")

    total = sum(c["helplines"] for c in index)
    print(f"Built {len(index)} countries, {total} helplines into {DIST.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
