---
id: "WFGY/WFGY_-_ProblemMap_Atlas_Fixes_community_prompts_f1_reg"
company: "WFGY"
product: "WFGY - ProblemMap Atlas Fixes community prompts f1 reg..."
category: "general-purpose"
source_file: "ProblemMap_Atlas_Fixes_community_prompts_f1-regrounding-prompt-pack-v1.md"
---

<!--
AI_NOTE_START

Document role:
This file is a small community prompt pack for an F1 grounding repair pattern.

How to use this file:
1. Read this page before using the prompts below.
2. Use these prompts only after routing the case to F1 or a nearby grounding-first region.
3. Treat this as a community prompt example, not as official atlas doctrine.

AI_NOTE_END
-->

# F1 Re-grounding Prompt Pack v1

## Community prompt example

This is a small community prompt pack for F1-style grounding repair.

It is designed for cases where:

- the answer looks fluent
- the evidence anchor is wrong
- the first repair move should be re-grounding

---

## When to use this pack

Use this prompt pack when the case has already been routed to:

- F1 Grounding & Evidence Integrity
- or a nearby F1-first boundary region

Do not use this pack as a substitute for routing.

Route first.
Prompt second.

---

## Prompt A

### Re-grounding prompt

```text
You are debugging a grounding-first failure.

Do not improve style first.
Do not expand reasoning first.

Your task is:

1. identify the evidence source that should anchor the answer
2. ignore semantically adjacent but unverified sources
3. restate the answer using only the verified source
4. state briefly why the original answer drifted

Return:
- verified anchor
- corrected answer
- short drift explanation
````

---

## Prompt B

### Anchor comparison prompt

```text
You are comparing two candidate evidence anchors.

Your task is:

1. identify which source is the valid anchor
2. explain why the other source is misleading
3. rewrite the answer using only the valid source

Keep the output short and structured.
Do not add unsupported inference.
```

---

## Prompt C

### Minimal route-first repair prompt

```text
This is an F1 grounding-first case.

Do the first repair move only.

Required steps:
1. re-check the evidence anchor
2. discard the wrong anchor
3. produce a corrected answer from the verified anchor

Do not attempt broader workflow redesign.
Do not speculate beyond the verified source.
```

---

## What this pack is trying to improve

This pack is trying to improve:

* anchor discipline
* evidence fidelity
* grounding-first repair behavior

It is not trying to solve every downstream issue.

---

## Known limits

This pack is weaker when:

* no verified source exists
* the case is really an F5 visibility problem first
* the case is actually an F7 container problem disguised as a grounding issue

---

## One-line status

**This is a small community prompt pack for route-first F1 re-grounding behavior.**
