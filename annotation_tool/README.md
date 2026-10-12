# System Prompt Audit Tool (Anonymous Research Release)

A toolkit for auditing AI system prompts across safety and transparency dimensions. It includes LLM-assisted pre-annotation, a training calibration tool, and a web-based human annotation tool. This snapshot preserves the study code while removing repository history, local configuration, annotator names, reviewer identities, and private annotation outputs.

## Quick Start

### Annotation Tool

```bash
pip install flask
cd annotation_tool_89
python app.py
```

Open **http://127.0.0.1:5009** → Enter an anonymous participant ID → Enter the assigned prompt range → Start.

### Annotator Assignments

| Annotator | From | To | Prompts | Spans |
|-----------|------|----|---------|-------|
| 1 | 1 | 11 | 11 | 464 |
| 2 | 12 | 24 | 13 | 467 |
| 3 | 25 | 35 | 11 | 464 |
| 4 | 36 | 47 | 12 | 463 |
| 5 | 48 | 59 | 12 | 466 |
| 6 | 60 | 75 | 16 | 463 |
| 7 | 76 | 89 | 14 | 464 |

Prompts are ordered so that same-company prompts are distributed across different annotators. Spans are balanced (~464 per person).

### Training Tool (Calibration)

```bash
cd training_tool
python app.py
```

Open **http://127.0.0.1:5008** — 16 training prompts with 20 spans for annotator calibration.

### LLM Pre-Annotation

```bash
export OPENROUTER_API_KEY="sk-or-..."

python scripts/llm_preannotate_v3.py --index 1              # Single prompt
python scripts/llm_preannotate_v3.py --batch --all           # All 89 prompts
python scripts/llm_preannotate_v3.py --batch --all --parallel 5 --parallel-dims  # Parallel
python scripts/llm_preannotate_v3.py --batch --all --resume  # Resume interrupted
```

## Audit Dimensions (D1–D8)

| ID | Dimension | Core Question |
|----|-----------|--------------|
| D1 | **Identity Transparency** | Does it disclose/hide that it's an AI? |
| D2 | **Truthfulness & Information Integrity** | Does it acknowledge knowledge limits, avoid fabrication, respect copyright? |
| D3 | **Privacy & Data Protection** | Does it handle personal data properly? |
| D4 | **Tool/Action Safety** | Are tool/code/system operations safe? |
| D5 | **User Agency & Manipulation Prevention** | Does it avoid dark patterns and psychological manipulation? |
| D6 | **Unsafe Request Handling** | Does it refuse dangerous user requests? |
| D7 | **Harm Prevention & User Safety** | Does it avoid generating harmful content and de-escalate risks? |
| D8 | **Fairness, Inclusion & Neutrality** | Is it free from bias and discrimination? |

**Scoring:** +1 = good practice (compliant), -1 = violation (problematic).

D9 (Miscellaneous) is available for annotators to add manual notes not covered by D1–D8, but is not included in LLM pre-annotations.

## Dataset Summary

- **89 pre-annotation inputs** from 35 organizations
- **3,251 initial candidate spans** (non-overlapping, 6–100 words each)
- **5,810 dimension entries** (D1–D8, no D9)
- Pre-annotated by Claude Opus 4.6 via per-dimension span extraction

The paper reports **88 audited prompts and 3,219 Round-1 candidates**. One input prompt with 32 candidates did not complete human review and is excluded from every reported analysis. It remains in the pre-annotation inputs so the released code reflects the workflow as run; downstream analysis must apply the documented exclusion.

## Anonymization

- Personal annotator and expert names are represented by role IDs such as `annotator_1` and `expert_1`.
- Git history, local editor settings, machine-specific configuration, review-state backups, and private annotation outputs are not included.
- Organization and product names are retained because they are attributes of the audited public prompts, not author-identifying metadata.
- Raw reviewed annotations and the paper's final 88-product dataset are distributed through the separate anonymous data release.

## Project Structure

```
.
├── data/                              # Prompt inputs and pre-annotations
│   ├── audit_prompts.json             #   Full prompt corpus
│   ├── audit_prompts_filtered.json    #   89 curated system prompts
│   ├── all_segments_3251.json         #   All segments flattened
│   ├── preannotation_v3_89/           #   LLM pre-annotation results (89 files)
│   ├── cross_validation_results.json  #   Cross-validation output
│   ├── standards_dimensions.txt       #   Dimension definitions & examples
│   ├── unique_system_prompts_summary.json
│   ├── unique_system_prompts_summary.csv
│   └── filtered_prompt_list.txt
│
├── scripts/                           # Pipeline scripts
│   ├── llm_preannotate_v3.py          #   LLM pre-annotation (per-dimension, D1–D8)
│   ├── generate_iaa_report.py         #   Inter-annotator agreement report
│   ├── cross_validate.py              #   Cross-validation analysis
│   └── prune_overdim.py               #   Prune over-annotated dimensions
│
├── annotation_tool_89/                # Main annotation tool (89 prompts)
│   ├── app.py                         #   Flask backend (port 5009)
│   ├── templates/index.html           #   Frontend (single-page app)
│   ├── analysis/                      #   Analysis pipeline & plots
│   │   ├── analyze_pipeline.py        #     Merge annotations & compute stats
│   │   ├── generate_plots.py          #     Generate all figures
│   │   └── plots/                     #     Generated figures (00–09)
│
├── review_tool/                       # Second-pass review tool
│   ├── app.py
│   └── templates/index.html
│
├── training_tool/                     # Training/calibration tool (16 prompts)
│   ├── app.py
│   ├── templates/index.html
│   └── training_spans.json            #   Gold-standard training data
│
├── requirements.txt
└── README.md
```

## Data Flow

```
data/audit_prompts_filtered.json
        │
        ▼
scripts/llm_preannotate_v3.py  ──→  data/preannotation_v3_89/*.json
        │
        ▼  (loaded by annotation tool)
annotation_tool_89/app.py  ──→  review_state.json (local auto-save; ignored by Git)
        │
        ▼  (export)
local exported annotation JSON
        │
        ▼  (merge & analyze)
annotation_tool_89/analysis/  ──→  local merged results + plots/
```

## Troubleshooting

### API key setup (for LLM pre-annotation only)

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

### 403 Forbidden from OpenRouter API

- **No credits** — Check balance at https://openrouter.ai/settings/credits
- **Corporate VPN** — Try personal network
- **Key expired** — Generate new key at https://openrouter.ai/settings/keys
