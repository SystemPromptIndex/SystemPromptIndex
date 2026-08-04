---
id: "paper-orchestra/paper-orchestra_-_citation_f1_prompt"
company: "paper-orchestra"
product: "paper-orchestra - citation f1 prompt"
category: "research"
annotation: "ai"
source_file: "citation-f1-prompt.md"
---

# Citation F1 — P0/P1 Partition prompt

**Source: arXiv:2604.05018, Appendix F.3, page 58 (verbatim).**

Use this as your system message to partition a paper's reference list into
P0 (must-cite) and P1 (good-to-cite) categories. Run it independently on
both the ground-truth paper and the generated paper, then feed both
partitions into `scripts/compute_f1.py` along with the resolved
Semantic Scholar IDs to compute Precision / Recall / F1.

---

```
You are an expert academic reviewer. Read the following paper text and
analyze its references.
Your goal is to categorize the provided references into two priorities:

Priority Levels

  - P0 (Must-Cite): Core citations strictly necessary for the paper. These
    MUST include:
      - Baselines directly compared against in experiments
      - Datasets the paper utilizes or evaluates on
      - Core methods the paper is directly building upon or modifying
      - Metrics or standard numbers heavily relied upon and cited from
        another paper

  - P1 (Good-To-Have): Supplemental citations. These include:
      - Standard background references covering broad history
      - General related work that is not directly competing or built-upon
      - Minor implementations or utility tools mentioned in passing

Paper Text:
{paper_text}

References List:
{references_str}

Output Format

Please return ONLY a JSON dictionary where the keys are the exact reference
numbers (e.g., "1", "2") and the values are either "P0" or "P1". Example
output:

```json
{{
    "1": "P0",
    "2": "P1",
    "3": "P0"
}}
```
```

---

## Substitution

| Placeholder | Source |
|---|---|
| `{paper_text}` | The full LaTeX or markdown text of the paper |
| `{references_str}` | The numbered reference list (extracted from `\bibliography{...}` or the References section) |

The model returns a JSON dict; the host agent saves it as
`gt_partition.json` (for the ground-truth paper) or `gen_partition.json`
(for the generated paper).

## How F1 is computed

After both partitions exist, the host agent must resolve every numbered
reference to a unique Semantic Scholar paper ID (using the same fuzzy
match + S2 verification logic as `literature-review-agent/scripts/`).
Then:

```
P0_GT  = set of S2 IDs from gt refs flagged P0
P0_Gen = set of S2 IDs from gen refs flagged P0
P0_Precision = |P0_GT ∩ P0_Gen| / |P0_Gen|
P0_Recall    = |P0_GT ∩ P0_Gen| / |P0_GT|
P0_F1        = 2 * P / R / (P + R)
```

Same for P1. Overall F1 uses the union of P0 and P1.

The deterministic computation lives in `scripts/compute_f1.py`.
