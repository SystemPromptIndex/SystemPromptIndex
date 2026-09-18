# Cross-model check of the Round-1 pre-annotation

Round 1 of the audit used one LLM pre-annotator. To check whether its labels are specific to that model, a second model from a different provider (Gemini-3.1-Pro) was given every Round-1 candidate span and asked to assign dimensions and polarities, without access to the original labels.

`second_model_labels.jsonl` has one line per candidate span: 3,251 spans from 89 prompts. 32 of them (`in_audited_set: false`) belong to one prompt whose review was not completed and which is not part of the released dataset; the other 3,219 belong to the 88 audited products.

| Field | Meaning |
|:--|:--|
| `id` | the product, matching `audits/<id>.json` and `prompts/<id>.md` |
| `in_audited_set` | whether the product is among the 88 released ones |
| `start`, `end`, `text` | the candidate span (character offsets into the prompt body as it was pre-annotated) |
| `round1_labels` | dimensions and scores proposed by the pre-annotator in Round 1, before human review |
| `second_model_labels` | dimensions and scores assigned independently by the second model |

These are Round-1 candidates, not the final dataset: many were later rejected by annotators or experts, and the final labels are the ones in `audits/`.

## Agreement on the 88 audited products

| | All | Anthropic prompts | Other prompts |
|:--|--:|--:|--:|
| Candidate spans | 3,219 | 627 | 2,592 |
| Same set of dimensions | 36.6% | 35.6% | 36.8% |
| Overlapping dimensions | 54.5% | 56.6% | 54.0% |
| No shared dimension | 8.9% | 7.8% | 9.2% |
| Polarity agreement on shared (span, dimension) pairs | 93.8% (3,756 pairs) | 97.8% (757 pairs) | 92.9% (2,999 pairs) |
| Protective entries, second model / pre-annotator | 0.97 | 1.00 | 0.96 |

Polarity agreement is computed over the (span, dimension) pairs that both models labelled. The check covers the labels given to candidate spans; it does not cover the choice of which spans to propose, which was made by the pre-annotator alone.
