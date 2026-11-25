#!/usr/bin/env python3
"""Validate every file in data/countries/.

Standard library only, so anyone (human or agent) can run it with no setup:

    python3 scripts/validate.py            # validate everything
    python3 scripts/validate.py data/countries/US.json   # specific files

Exit code 0 = all files valid. Errors block a merge; warnings do not.
The rules enforced here are documented in CONTRIBUTING.md and AGENTS.md.
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "countries"

CATEGORIES = {
    "suicide", "mental-health", "crisis", "domestic-violence", "sexual-assault",
    "child-abuse", "youth", "substance-use", "poison", "eating-disorders",
    "human-trafficking", "elder-abuse", "gambling", "lgbtq", "veterans",
}
AUDIENCES = {
    "everyone", "children", "youth", "lgbtq", "veterans", "women", "men",
    "seniors", "indigenous", "deaf-hard-of-hearing", "parents", "students",
}
CONTACT_TYPES = {"phone", "sms", "whatsapp", "chat", "email"}
SOURCE_TYPES = {"operator", "government", "third-party"}
STATUSES = {"provisional", "verified"}
AVAILABILITY = {"24/7", "limited", "unknown"}
COSTS = {"free", "standard-rates", "unknown"}

HELPLINE_REQUIRED = {
    "id", "name", "categories", "audiences", "contacts", "availability",
    "cost", "sources", "status", "last_verified",
}
HELPLINE_ALLOWED = HELPLINE_REQUIRED | {
    "operator", "regions", "languages", "website", "hours_note", "notes",
}
COUNTRY_ALLOWED = {"country", "name", "emergency", "helplines", "notes"}

NUMBER_RE = re.compile(r"^\+?[0-9]{3,15}$")
ID_RE = re.compile(r"^[a-z]{2}-[a-z0-9]+(-[a-z0-9]+)*$")
LANG_RE = re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$")  # BCP 47-ish
DIGIT_RUN_RE = re.compile(r"\+?\d[\d\s.\-()]*\d|\d")
STALE_DAYS = 365


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, where, msg):
        self.errors.append(f"ERROR   {where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"WARNING {where}: {msg}")


def parse_date(value):
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def digit_runs(text):
    """Phone-like digit sequences in text, with separators removed."""
    return {re.sub(r"\D", "", m) for m in DIGIT_RUN_RE.findall(text or "")}


def check_url(rep, where, url):
    if not isinstance(url, str):
        rep.err(where, "url must be a string")
        return
    p = urlparse(url)
    if p.scheme != "https" or not p.netloc:
        rep.err(where, f"url must be an absolute https:// URL, got {url!r}")


def check_sources(rep, where, sources, today):
    if not isinstance(sources, list) or not sources:
        rep.err(where, "needs at least one source")
        return []
    for i, s in enumerate(sources):
        w = f"{where}.sources[{i}]"
        if not isinstance(s, dict):
            rep.err(w, "must be an object")
            continue
        extra = set(s) - {"url", "type", "accessed", "quote"}
        if extra:
            rep.err(w, f"unknown fields {sorted(extra)}")
        check_url(rep, w, s.get("url"))
        if s.get("type") not in SOURCE_TYPES:
            rep.err(w, f"type must be one of {sorted(SOURCE_TYPES)}")
        d = parse_date(s.get("accessed"))
        if not d:
            rep.err(w, "accessed must be a YYYY-MM-DD date")
        elif d > today:
            rep.err(w, "accessed date is in the future")
        q = s.get("quote")
        if not isinstance(q, str) or not q.strip():
            rep.err(w, "quote is required: copy the exact text from the source "
                       "that shows the number (join separate snippets with ' ... ')")
    return [s for s in sources if isinstance(s, dict)]


def check_helpline(rep, where, h, country, today, seen_ids):
    if not isinstance(h, dict):
        rep.err(where, "must be an object")
        return
    missing = HELPLINE_REQUIRED - set(h)
    if missing:
        rep.err(where, f"missing required fields {sorted(missing)}")
    extra = set(h) - HELPLINE_ALLOWED
    if extra:
        rep.err(where, f"unknown fields {sorted(extra)}")

    hid = h.get("id")
    if not isinstance(hid, str) or not ID_RE.match(hid):
        rep.err(where, "id must be lowercase-kebab-case, e.g. 'us-988-lifeline'")
    else:
        where = f"{where}({hid})"
        if not hid.startswith(country.lower() + "-"):
            rep.err(where, f"id must start with '{country.lower()}-'")
        if hid in seen_ids:
            rep.err(where, f"duplicate id (also in {seen_ids[hid]})")
        seen_ids[hid] = country

    if not isinstance(h.get("name"), str) or not h.get("name", "").strip():
        rep.err(where, "name must be a non-empty string")

    for field, allowed in (("categories", CATEGORIES), ("audiences", AUDIENCES)):
        vals = h.get(field)
        if not isinstance(vals, list) or not vals:
            rep.err(where, f"{field} must be a non-empty list")
            continue
        bad = [v for v in vals if v not in allowed]
        if bad:
            rep.err(where, f"unknown {field} {bad}; allowed: {sorted(allowed)} "
                           "(open an issue to propose a new one)")
        if len(set(vals)) != len(vals):
            rep.err(where, f"duplicate values in {field}")

    if h.get("availability") not in AVAILABILITY:
        rep.err(where, f"availability must be one of {sorted(AVAILABILITY)}")
    if h.get("cost") not in COSTS:
        rep.err(where, f"cost must be one of {sorted(COSTS)}")
    if h.get("status") not in STATUSES:
        rep.err(where, f"status must be one of {sorted(STATUSES)}")
    for lang in h.get("languages", []) or []:
        if not isinstance(lang, str) or not LANG_RE.match(lang):
            rep.err(where, f"language {lang!r} is not a BCP 47 code like 'en' or 'pt-BR'")
    if "website" in h:
        check_url(rep, where + ".website", h["website"])

    sources = check_sources(rep, where, h.get("sources"), today)
    quoted = set()
    for s in sources:
        quoted |= digit_runs(s.get("quote", ""))

    contacts = h.get("contacts")
    if not isinstance(contacts, list) or not contacts:
        rep.err(where, "needs at least one contact")
        contacts = []
    for i, c in enumerate(contacts):
        w = f"{where}.contacts[{i}]"
        if not isinstance(c, dict):
            rep.err(w, "must be an object")
            continue
        extra = set(c) - {"type", "value", "display", "keyword", "notes"}
        if extra:
            rep.err(w, f"unknown fields {sorted(extra)}")
        ctype, value = c.get("type"), c.get("value")
        if ctype not in CONTACT_TYPES:
            rep.err(w, f"type must be one of {sorted(CONTACT_TYPES)}")
            continue
        if ctype in {"phone", "sms", "whatsapp"}:
            if not isinstance(value, str) or not NUMBER_RE.match(value):
                rep.err(w, "value must be digits only (optional leading '+'), "
                           "e.g. '116123' or '+441234567890'; put spacing in 'display'")
                continue
            digits = value.lstrip("+")
            if not any(r == digits or r.endswith(digits) or digits.endswith(r)
                       for r in quoted if len(r) >= 3):
                rep.err(w, f"number {value} does not appear in any source quote; "
                           "every number must be backed by quoted source text")
        elif ctype == "chat":
            check_url(rep, w + ".value", value)
        elif ctype == "email":
            if not isinstance(value, str) or "@" not in value:
                rep.err(w, "value must be an email address")

    if h.get("status") == "verified":
        domains = {urlparse(s.get("url", "")).netloc.lower().removeprefix("www.")
                   for s in sources}
        if len(domains) < 2:
            rep.err(where, "status 'verified' needs sources from at least two "
                           "different websites; use 'provisional' otherwise")

    lv = parse_date(h.get("last_verified"))
    if not lv:
        rep.err(where, "last_verified must be a YYYY-MM-DD date")
    elif lv > today:
        rep.err(where, "last_verified is in the future")
    elif (today - lv).days > STALE_DAYS:
        rep.warn(where, f"last verified {lv}, over {STALE_DAYS} days ago; please re-check")


def check_file(rep, path, today, seen_ids):
    try:
        where = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        where = str(path)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        rep.err(where, f"invalid JSON: {e}")
        return
    if not isinstance(doc, dict):
        rep.err(where, "top level must be an object")
        return
    extra = set(doc) - COUNTRY_ALLOWED
    if extra:
        rep.err(where, f"unknown top-level fields {sorted(extra)}")
    country = doc.get("country")
    if not isinstance(country, str) or not re.fullmatch(r"[A-Z]{2}", country):
        rep.err(where, "country must be an ISO 3166-1 alpha-2 code like 'US'")
        return
    if path.stem != country:
        rep.err(where, f"file name must be {country}.json")
    if not isinstance(doc.get("name"), str) or not doc["name"].strip():
        rep.err(where, "name (country name in English) is required")

    for i, e in enumerate(doc.get("emergency", [])):
        w = f"{where}.emergency[{i}]"
        if not isinstance(e, dict) or not NUMBER_RE.match(str(e.get("number", ""))):
            rep.err(w, "needs a 'number' of digits")
            continue
        srcs = check_sources(rep, w, e.get("sources"), today)
        quoted = set().union(*(digit_runs(s.get("quote", "")) for s in srcs)) if srcs else set()
        if e["number"] not in quoted:
            rep.err(w, f"emergency number {e['number']} does not appear in any source quote")

    helplines = doc.get("helplines")
    if not isinstance(helplines, list):
        rep.err(where, "helplines must be a list")
        return
    for i, h in enumerate(helplines):
        check_helpline(rep, f"{where}.helplines[{i}]", h, country, today, seen_ids)


def main(argv):
    today = dt.date.today()
    targets = [Path(a).resolve() for a in argv] or sorted(DATA_DIR.glob("*.json"))
    rep, seen_ids = Report(), {}
    # Always load every file so duplicate ids across countries are caught,
    # but only report on the files that were asked for.
    all_files = sorted(DATA_DIR.glob("*.json"))
    for path in all_files:
        if path.resolve() not in targets:
            check_file(Report(), path, today, seen_ids)
    for path in targets:
        check_file(rep, path, today, seen_ids)

    for line in rep.warnings + rep.errors:
        print(line)
    n = len(targets)
    if rep.errors:
        print(f"\n{len(rep.errors)} error(s) in {n} file(s). See CONTRIBUTING.md for the rules.")
        return 1
    print(f"OK: {n} file(s) valid, {len(rep.warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
