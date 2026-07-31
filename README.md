# System Prompt Index

The public dataset behind [systempromptindex.com](https://systempromptindex.com):
**1,017 system prompts** collected from real AI products and open-source agent
projects, each audited against the eight AISPA assurance dimensions.

Paper: [arXiv:2607.28617](https://arxiv.org/abs/2607.28617)

---

## What is in here

```
prompts/<vendor>/<product>.md     the prompt text, with YAML front matter
audits/<vendor>/<product>.json    the audit for that prompt
data/prompts.json                 every prompt in one file
data/audits.json                  every audit in one file
dimensions.json                   the eight dimensions and their definitions
```

Per-file and aggregate views hold the same records. Browse the tree on GitHub,
or load the two files under `data/` if you are working with the corpus
programmatically. `id` is the path under `prompts/` and `audits/`, so a record
in the aggregate always points at its own files.

## The eight dimensions

| | |
|---|---|
| **D1** | Identity Transparency |
| **D2** | Truthfulness & Information Integrity |
| **D3** | Privacy & Data Protection |
| **D4** | Tool/Action Safety |
| **D5** | User Agency & Manipulation Prevention |
| **D6** | Unsafe Request Handling |
| **D7** | Harm Prevention & User Safety |
| **D8** | Fairness, Inclusion & Neutrality |

`Misc` collects entries that matter but sit outside the eight.

## Audit format

```jsonc
{
  "id": "Anthropic/Claude_Opus_4_6",
  "company": "Anthropic",
  "product": "Claude Opus 4.6",
  "audit_type": "human-reviewed",   // or "automated"
  "reviewer": "human",              // or "auto"
  "scores": { "D1": 2, "D2": 1, ... },
  "protective_entries": 31,
  "problematic_entries": 2,
  "by_dimension": {
    "protective":  { "D1": 4, ... },
    "problematic": { "D1": 0, ... }
  },
  "spans": [
    {
      "text": "the exact instruction this finding is about",
      "start": 1204, "end": 1391,
      "dimension": "D3",
      "score": 1,                   // +1 protective, -1 problematic
      "note": "why it was scored this way",
      "risky": false,               // borderline: user agency vs. platform safety
      "source": "llm"               // llm | human | cross_version_unify | cross_version_review
    }
  ]
}
```

`start` and `end` are character offsets into the prompt body — the text after
the front matter in the matching `prompts/` file.

### How the audits were produced

Every prompt was audited span by span: a reviewer marks the exact instruction,
assigns it to a dimension, scores it protective or problematic, and writes a
short justification.

- **88 prompts** are `human-reviewed`. These are the set analysed in the paper.
  Reviewers worked from the same rubric and their spans were reconciled across
  product versions.
- **929 prompts** are `automated`. These extend the corpus well past what the
  paper covers and have not been through human reconciliation.

`source` on a span records *how* that particular finding arrived — a language
model, a human reviewer, or propagation across versions of the same product.
Automated findings should be treated as a starting point, not a verdict: the
paper's own benchmark section shows that automated auditors recall problematic
spans well but over-flag them, so precision is the weak axis.

Individual reviewers and the specific models used are not recorded here.

## Where the prompts come from

The prompts are published system prompts, gathered from public collections. We
did not extract them ourselves. Credit to the projects that assembled them:

- [TheBigPromptLibrary](https://github.com/0xeb/TheBigPromptLibrary)
- [system_prompts_leaks](https://github.com/asgeirtj/system_prompts_leaks)
- [awesome-ai-system-prompts](https://github.com/dontriskit/awesome-ai-system-prompts)
- [CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S)
- [chatgpt_system_prompt](https://github.com/LouisShark/chatgpt_system_prompt)
- [system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools)

Prompt text belongs to whoever wrote it and is reproduced here for research.
We claim nothing over it. The audits — spans, scores, notes, and the dimension
definitions — are ours, and you are free to use them with attribution.

A prompt's presence in this index is not a claim that it is authentic, current,
or officially released. Vendors change prompts without notice, and the corpus
includes agent-framework and open-source project prompts alongside consumer
products.

## Citing

```bibtex
@article{lin2026aispa,
  title={AISPA: Artificial Intelligence System Prompt Assurance -- User-Centric System Prompt Auditing for Large Language Model Applications},
  author={Lin, Xiangning and Zhu, Shenzhe and Yang, Shu and Zhang, Zhenyu and Zhang, Haoqian and Zhao, Yipeng and Qian, Chengxuan and Wang, Tianwei and Zhang, Ziheng and Yuan, Zhenlong and Wang, Dingcheng and Wu, Juncheng and Si, Yuan and Liu, Jiaxin and Bi, Baolong and Mahari, Robert and South, Tobin and Greenwood, Dazza and He, Zexue and Bommasani, Rishi and Kazinnik, Sophia and Haupt, Andreas and Marro, Samuele and Brynjolfsson, Erik and Pentland, Alex and Pei, Jiaxin},
  journal={arXiv preprint arXiv:2607.28617},
  year={2026}
}
```

## Contributing

Missing a prompt, or think an audit is wrong? Open an issue or a pull request.
For a disputed span, point at the span and say what you would score it instead —
disagreement about a specific instruction is more useful than a general
objection.
