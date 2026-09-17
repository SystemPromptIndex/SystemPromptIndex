# Supplementary data

Anonymised supplementary material for a submission under review.

```
prompts/<org>/<product>.md     system prompt text
audits/<org>/<product>.json    span-level annotations for that prompt
dimensions.json                definitions of the eight auditing dimensions
PAPER_SUBSET.md                the 88 human-audited products analysed in the paper
```

Each audit record has an `annotation` field:

- `human` (88 records): the products analysed in the paper.
- `ai` (970 records): labelled by a model only, not reviewed by a person, and not used in the paper.

In each record, `spans` lists the annotated instructions: `text`, `start`/`end`
(character offsets into the prompt body), `dimension` (`D1`–`D8`), `score`
(`+1` protective, `-1` problematic) and `note` (the reason).
