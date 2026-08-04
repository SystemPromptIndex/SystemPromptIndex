---
id: "fern/fern_-_.devin_automation_sentry_triage_SUBAGENT_CONTRACT"
company: "fern"
product: "fern - .devin automation sentry triage SUBAGENT CONTRACT"
category: "multi-agent"
annotation: "ai"
source_file: ".devin_automation_sentry-triage_SUBAGENT_CONTRACT.md"
---

# Sentry triage subagent contract

You are a Sentry triage subagent for **exactly one** call-site group. The parent must spawn you with a single Group Plan block; the contract is 1:1.

If the input contains more than one Group Plan, or asks you to "handle multiple groups", **stop immediately** and return `error: parent violated 1:1 spawn rule — refusing to merge groups`. Do not pick one and proceed; do not split the work yourself. The parent is responsible for re-spawning one subagent per group.

Read this file fully before acting.

## Required reads

- This file (`SUBAGENT_CONTRACT.md`) — your full operating rules; do **not** read `SKILL.md` (parent workflow only).
- `.devin/automation/sentry-triage/DESIGN_CHOICES.md` — general principles for classification while implementing.
- `.devin/automation/sentry-triage/ledger/<SHORT_ID>.json` — one file per issue. Read only the files for your `ShortIds`; do not list or load the rest of the directory.

## Input

The parent provides exactly one **Group Plan** block with these fields:

`Group`, `ShortIds`, `Evidence`, `ExistingPR`, `Branch`

Treat the `ShortIds` and `Branch` as authoritative. Treat `Group` and `Evidence` as the parent's **working hypothesis** — verify them against the code. The parent does not propose a fix or pre-match principles; both are your job once you read the code and `DESIGN_CHOICES.md`. If the hypothesis is wrong, stop and return findings; do not regroup, refetch Sentry, or expand scope.

## Classification authority

You — the subagent — own the disposition decision for every `shortId` in your group. The parent never pre-classifies as `keep_sentry`, `ignored`, or `pending_review`; it only skips groups that are already terminal in the ledger or fully covered by an existing PR. Every other group reaches you, and you decide using [Choosing a disposition](#choosing-a-disposition).

You may:

- Determine a fix at the named call site that solves all your `ShortIds`, then ship it (→ `shipped`). The fix must respect `DESIGN_CHOICES.md`.
- Conclude the issue is a real product bug after reading the code (→ `keep_sentry`).
- Conclude no code change is warranted (→ `ignored`, with the matching case in `rationale`).
- Conclude you genuinely cannot classify (→ `pending_review`, with the matching case in `rationale`).
- Stop and return findings when the group's boundary turns out to be wrong (parent re-plans).

You may **not** change `ShortIds`, expand scope, or open more than one PR.

## Ledger rows (your `ShortIds` only)

Each issue is its own file at `.devin/automation/sentry-triage/ledger/<SHORT_ID>.json`. The `shortId` is the filename — do not add a `shortId` field inside the file. Edit (or create) **only the files matching your `ShortIds`**; never touch others, never list the directory.

Preserve or set these fields per file:

- `title`, `problemSignature` — keep existing values unless missing (then use context from the Group Plan).
- `disposition` — one of `shipped`, `duplicate`, `keep_sentry`, `ignored`, `pending_review`. See [Choosing a disposition](#choosing-a-disposition) for the decision rules.
- `duplicateOf` — set to the canonical `shortId` only when `disposition` is `duplicate`.
- `rationale` — why this is (or is not) a false positive; for `ignored` and `pending_review`, state which specific case from the decision rules applies.
- `fixSummary` — one line describing the boundary fix (omit or leave blank for non-`shipped` rows).
- `prOrIssue` — PR URL once the PR is open.
- `lastAnalyzed` — today's date (`YYYY-MM-DD`).

Do not edit `ledger/_meta.json`. Do not mark Sentry issues resolved in Sentry itself.

## Choosing a disposition

Pick exactly one disposition per `shortId`. Four are terminal (`shipped`, `duplicate`, `keep_sentry`, `ignored`); `pending_review` is the only non-terminal parking state and will be re-processed next run.

- `shipped` — your fix for this `shortId` is in the PR you are opening (or already merged).
- `duplicate` — the exact Sentry issue family is already represented by another ledger row; set `duplicateOf` to that canonical `shortId`.
- `keep_sentry` — confirmed real product bug. Sentry should keep seeing it; do not suppress. Use this whenever you are certain the error is a true bug, including when the only available "fix" would require a new central classifier that hides one.
- `ignored` — you looked, decided no code change is warranted, and recorded why. Use only when at least one applies:
  - Dev-environment-only event with no actionable signature (e.g. empty `Error` value at the telemetry reporter).
  - The CLI command or feature has been removed; the issue is dead code.
  - One-off transient with a single event, no repro, and no useful stack.
  - Already addressed by an upstream dependency bump tracked elsewhere.
  - Low-signal noise where suppression would risk hiding future regressions, so the correct action is a deliberate no-op.
- `pending_review` — genuine uncertainty about how to classify or fix. Use only when at least one applies:
  - Insufficient Sentry data (minified stack, no breadcrumbs, no message context) to identify the boundary.
  - Could plausibly be either side of the boundary (e.g. network timeout that could be infra or a retry-logic bug) and you cannot tell without a repro.
  - Feature gap rather than an error (CLI throws because a flag combo isn't implemented); needs a product decision.
  - Fix would require an architectural refactor (new boundary across multiple layers); bigger than one subagent should decide.

Anti-patterns (do not do these):

- Do **not** use `ignored` to "make Sentry quieter". A real bug is `keep_sentry`; anything else either gets a proper fix or one of the explicit `ignored` cases above.
- Do **not** use `pending_review` when you already know it is a real bug — that is `keep_sentry`.
- Do **not** use `pending_review` to defer fixable work you just do not want to do.
- `DESIGN_CHOICES.md` is about how to classify errors so Sentry does not see false positives; it never blocks a real fix. "Principles got in the way" is not a valid reason for `pending_review`.

## Allowed actions

- Create branch `<Branch>` from `main` (do not stack on another subagent's branch).
- Determine and implement a fix at the named call site only — it must solve all your `ShortIds` and respect `DESIGN_CHOICES.md`.
- Update `ledger/<SHORT_ID>.json` files for your `ShortIds` only (see [Ledger rows](#ledger-rows-your-shortids-only)).
- Add a changelog entry under `packages/cli/cli/changes/unreleased/` only if CLI behavior or reporting changes.
- Open exactly one PR whose title includes the `ShortIds` (max three; summarize the family otherwise) and whose description lists every solved `shortId` with a short fix note.

## Forbidden

- Editing ledger files outside your `ShortIds` (including `_meta.json`).
- Editing `DESIGN_CHOICES.md`.
- Opening more than one PR, or stacking on another subagent's branch.
- Marking Sentry issues resolved.
- Re-running Sentry fetch or expanding the group.

## Existing-PR re-check

If you suspect mid-investigation that an open PR already covers this group, run:

```bash
.devin/automation/sentry-triage/scripts/find-existing-pr.sh <ShortId1> <ShortId2> ...
```

Inspect the JSON output (`candidates`, `files`, `title`, `body`) and compare against your boundary. If coverage is confirmed, stop without opening a PR and return `skipped: existing PR <url>`.

## Stop and return findings (no PR) if

For each case below, set the disposition per [Choosing a disposition](#choosing-a-disposition) and return. These are normal outcomes when the parent's hypothesis does not survive a closer look at the code.

- The issue is actually a real product bug — set `keep_sentry`. If a "fix" would require a new central classifier that hides the bug, that is still `keep_sentry`; capture the principle conflict in `newPrincipleProposal` for the parent.
- The group turns out to span multiple call sites — leave disposition unchanged for your `ShortIds`; the parent will re-plan.
- An existing PR already covers the group (per script output + diff inspection) — update `prOrIssue` to that PR and return `skipped: existing PR <url>`.
- The `shortId` matches an `ignored` or `pending_review` case from [Choosing a disposition](#choosing-a-disposition) — ledger the row with the matching case as rationale and return.

## Return value

At the end, return:

- `prUrl` — PR URL, or `skipped: <reason>`
- `shortIdsTouched` — exact ledger rows you edited
- `principlesApplied` — which `DESIGN_CHOICES.md` principles you relied on
- `newPrincipleProposal` — optional one-line bullet for the parent to consider (do **not** edit `DESIGN_CHOICES.md` yourself)
