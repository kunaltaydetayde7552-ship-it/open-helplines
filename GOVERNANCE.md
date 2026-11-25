# Governance

## Roles

**Owner:** [mpatel-playground](https://github.com/mpatel-playground), a human. Holds final authority, admin rights, and the merge button for anything safety-critical.

**Team lead:** an AI agent (Claude, by Anthropic, running as Claude Code) acting on the owner's behalf. The team lead:

- writes and triages issues, breaks work into small tasks, and labels them;
- reviews pull requests against `AGENTS.md` and `CONTRIBUTING.md`, re-checks cited sources, and requests changes;
- recommends merges; keeps the roadmap and docs current;
- posts under the owner's GitHub account, and signs its comments so you know it's the AI.

The team lead can be wrong. If you disagree with one of its reviews, say so on the PR and ask for the owner. A human will look.

**Contributors:** anyone, human or AI agent.

## Merge policy

| Change | Requirement |
|---|---|
| New or changed phone numbers | CI passes **and** the source quote is independently re-checked by a reviewer **and** the owner approves |
| Removing a number reported as wrong | Can be merged fast by the owner after one confirmation; safety over completeness |
| Docs, tooling, tests | CI passes and one approving review |
| Changes to validation rules or this file | Owner approval; must not weaken the "every number has a quoted source" rule |

## Handling wrong numbers

See [`SAFETY.md`](SAFETY.md). Target: triaged within 24 hours, and an incorrect entry removed or corrected within 72 hours of confirmation.

## Decisions

Made in issues, in public. The owner decides when consensus isn't reached.
