# Contributing

Thank you. The most valuable contribution is **adding or checking one country's helplines**. You don't need to write code.

> AI agents: please read [`AGENTS.md`](AGENTS.md) first. The rules are the same, but it's written for you.

## Ways to help

| Task | Skill needed | Where |
|---|---|---|
| Add a country | Careful reading | Issues labelled [`country-data`](https://github.com/mpatel-playground/open-helplines/labels/country-data) |
| Add a second source to a `provisional` entry | Careful reading | [`needs-second-source`](https://github.com/mpatel-playground/open-helplines/labels/needs-second-source) |
| Re-check a stale or flagged entry | Careful reading | [`needs-recheck`](https://github.com/mpatel-playground/open-helplines/labels/needs-recheck) |
| Report a wrong number | None | [Report form](https://github.com/mpatel-playground/open-helplines/issues/new?template=report-wrong-info.yml) |
| Tooling, packages, site | Python / JS | [`tooling`](https://github.com/mpatel-playground/open-helplines/labels/tooling) |
| Speak a language well? | Languages | Help find and read sources for countries where English sources are scarce |

Not comfortable with GitHub? Open an issue with the helpline name, number and the link where you found it, and a maintainer will add it.

## Ground rules for data

1. **Every number needs a source you read yourself during this contribution**, and a `quote`: text copied exactly from that page showing the number.
2. Prefer the operator's own website, then government pages, then reputable directories.
3. Don't claim what the source doesn't say. If it doesn't say 24/7, use `"unknown"`.
4. `verified` means sources on two different websites agree. Otherwise `provisional`.
5. One country per pull request.

Run `python3 scripts/validate.py` before opening a PR. CI runs it too.

## Field reference

File: `data/countries/<CC>.json`, where `<CC>` is the [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) code.

### Country

| Field | Required | Notes |
|---|---|---|
| `country` | yes | ISO alpha-2, uppercase, same as file name |
| `name` | yes | Country name in English |
| `emergency` | no | List of `{ "number", "sources" }` for police/ambulance numbers |
| `helplines` | yes | List of helplines (may be empty) |
| `notes` | no | Anything a maintainer should know |

### Helpline

| Field | Required | Values |
|---|---|---|
| `id` | yes | `<cc>-<kebab-name>`, e.g. `gb-samaritans`. Unique. Never change once published. |
| `name` | yes | Official name |
| `operator` | no | Organisation running it, if different from the name |
| `categories` | yes | `suicide`, `mental-health`, `crisis`, `domestic-violence`, `sexual-assault`, `child-abuse`, `youth`, `substance-use`, `poison`, `eating-disorders`, `human-trafficking`, `elder-abuse`, `gambling`, `lgbtq`, `veterans` |
| `audiences` | yes | `everyone`, `children`, `youth`, `lgbtq`, `veterans`, `women`, `men`, `seniors`, `indigenous`, `deaf-hard-of-hearing`, `parents`, `students` |
| `contacts` | yes | See below |
| `availability` | yes | `24/7`, `limited`, `unknown` |
| `hours_note` | no | Free text, e.g. "Mon–Fri 9:00–17:00 local time" |
| `cost` | yes | `free`, `standard-rates`, `unknown` |
| `languages` | no | BCP 47 codes (`en`, `es`, `pt-BR`). Only if the source states them. |
| `regions` | no | For sub-national lines, e.g. `["Ontario"]` |
| `website` | no | https URL |
| `sources` | yes | See below |
| `status` | yes | `provisional` or `verified` |
| `last_verified` | yes | `YYYY-MM-DD` |
| `notes` | no | Caveats for maintainers or users |

Need a new category or audience? Open an issue rather than inventing one.

### Contact

| Field | Notes |
|---|---|
| `type` | `phone`, `sms`, `whatsapp`, `chat`, `email` |
| `value` | Phone/SMS/WhatsApp: digits only, optional leading `+`, as dialled within the country. Chat: https URL. Email: address. |
| `display` | How to show it to people, e.g. `116 123` or `Text HOME to 741741` |
| `keyword` | SMS keyword to send, if any |
| `notes` | Optional |

### Source

| Field | Notes |
|---|---|
| `url` | https URL of the page you read |
| `type` | `operator`, `government`, `third-party` |
| `accessed` | Date you read it, `YYYY-MM-DD` |
| `quote` | Exact text from the page that shows the number. Join separate snippets with ` ... ` |

## Review and merging

See [`GOVERNANCE.md`](GOVERNANCE.md). Data PRs need passing CI and a maintainer review. Reports of wrong numbers jump the queue.

## Code of conduct

Be kind; this project exists for people having the worst days of their lives. See [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
