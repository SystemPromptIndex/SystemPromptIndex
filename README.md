# System prompt audit data

Anonymised supplementary material for a submission under review. It contains the
audited system prompts, the span-level annotations, and the full definitions of
the eight auditing dimensions.

## Which records are in the paper

Each audit record has an `annotation` field.

| `annotation` | Records | What it means |
|:--|--:|:--|
| `human` | 88 | The products analysed in the paper. Spans were proposed by an LLM pre-annotator or added by a person, screened by trained annotators, and adjudicated by three experts. |
| `ai` | 970 | Labelled by a model only and not reviewed by a person. Not used for any result in the paper. |

The 88 human-audited records cover 35 organisations and hold 1,818 unique spans
and 2,420 (span, dimension) entries: 2,346 protective (+1) and 74 problematic
(-1). These are the figures reported in the paper.

**[PAPER_SUBSET.md](PAPER_SUBSET.md) lists all 88 with links to each audit and prompt.**

To select them programmatically:

```python
import glob, json

audits = [json.load(open(f)) for f in glob.glob("audits/*/*.json")]
paper = [a for a in audits if a["annotation"] == "human"]
assert len(paper) == 88
```

```bash
jq -s '[.[] | select(.annotation=="human")] | length' audits/*/*.json
```

## Layout

```
prompts/<org>/<product>.md     prompt text, with YAML front matter
audits/<org>/<product>.json    the audit for that prompt
dimensions.json                the eight dimensions: definitions and examples
PAPER_SUBSET.md                the 88 human-audited products
```

One prompt, one audit, same path under both trees. `id` is that path, so a record
always says where its own files are.

## The eight dimensions

| | | |
|:--|:--|:--|
| `D1` | Identity Transparency | Is it honest about being an AI? |
| `D2` | Truthfulness & Information Integrity | Does it avoid asserting what it can't support? |
| `D3` | Privacy & Data Protection | What does it do with what the user tells it? |
| `D4` | Tool/Action Safety | What may it do on the user's behalf? |
| `D5` | User Agency & Manipulation Prevention | Does it steer the user, or serve them? |
| `D6` | Unsafe Request Handling | What does it refuse, and how? |
| `D7` | Harm Prevention & User Safety | Does it avoid enabling harm and de-escalate risk? |
| `D8` | Fairness, Inclusion & Neutrality | Who does it treat differently? |

Full definitions, with protective and problematic examples for each, are in
`dimensions.json`. They are the dimension definitions used in the annotation
guidelines.

## Audit schema

Each file in `audits/` has the prompt's metadata plus a `spans` array. One element
is one (span, dimension) entry; a span that bears on several dimensions appears
once per dimension, with the same `start` and `end`.

| Field | Meaning |
|:--|:--|
| `text`, `start`, `end` | The exact instruction, and its character offsets into the prompt body |
| `dimension` | `D1`–`D8` |
| `score` | `+1` protective, `-1` problematic |
| `note` | Why it was scored that way |
| `risky` | Borderline case: user agency weighed against platform safety |

Offsets index the prompt body, that is, the text after the front matter in the
matching `prompts/` file.

At the prompt level, `scores`, `by_dimension`, `protective_entries` and
`problematic_entries` summarise the spans.

## Provenance

These are published system prompts gathered from public collections; they were
not extracted for this work. Credit to the projects that assembled them:
[TheBigPromptLibrary](https://github.com/0xeb/TheBigPromptLibrary) ·
[system_prompts_leaks](https://github.com/asgeirtj/system_prompts_leaks) ·
[awesome-ai-system-prompts](https://github.com/dontriskit/awesome-ai-system-prompts) ·
[CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S) ·
[chatgpt_system_prompt](https://github.com/LouisShark/chatgpt_system_prompt) ·
[system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools)

Prompt text belongs to whoever wrote it and is reproduced for research. Inclusion
is not a claim that a prompt is authentic, current, or officially released.
