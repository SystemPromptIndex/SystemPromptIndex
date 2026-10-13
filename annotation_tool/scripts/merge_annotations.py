#!/usr/bin/env python3
"""
Merge all annotation files from final_result into a single merged_all_annotations.json.

Selection policy (per prompt_id):
  1. Prefer fully reviewed annotations (reviewed_spans == total_spans)
  2. Among fully reviewed, prefer reviewers designated as experts.
  3. Then higher reviewed span count
  4. Then later completion time

After selection, adjacent kept spans with same dimension+score are merged
if the gap between them is <= GAP_THRESHOLD characters.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
FINAL_RESULT_DIR = ROOT_DIR / "annotation_tool" / "outputs" / "final_result"
ANALYSIS_DIR = ROOT_DIR / "annotation_tool" / "analysis"
AUDIT_PROMPTS_FILE = ROOT_DIR / "data" / "audit_prompts.json"
OUTPUT_FILE = ANALYSIS_DIR / "merged_all_annotations.json"

EXPERT_REVIEWERS = {"expert_1", "expert_2", "expert_3"}
GAP_THRESHOLD = 50

DIM_NAMES = {
    "D1": "Identity Transparency",
    "D2": "Truthfulness & Information Integrity",
    "D3": "Privacy & Data Protection",
    "D4": "Tool/Action Safety",
    "D5": "User Agency & Manipulation Prevention",
    "D6": "Unsafe Request Handling",
    "D7": "Harm Prevention & User Safety",
    "D8": "Fairness, Inclusion & Neutrality",
    "Misc": "Miscellaneous",
}


def load_audit_prompts():
    """Load audit_prompts.json to get prompt metadata (category, size_bytes, etc.)."""
    if not AUDIT_PROMPTS_FILE.exists():
        return {}
    with AUDIT_PROMPTS_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    lookup = {}
    for p in data:
        fn = p.get("filename", "")
        company = p.get("company", "")
        pid = f"{company}__{fn}"
        lookup[pid] = p
        lookup[fn] = p
    return lookup


def load_all_annotation_files():
    """Load all annotation files from final_result directory."""
    files = sorted(FINAL_RESULT_DIR.glob("annotations_*.json"))
    all_data = []
    for f in files:
        with f.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        data["_source_file"] = f.name
        all_data.append(data)
    return all_data


def is_fully_reviewed(ann_data, prompt_id):
    """Check if an annotation for a given prompt_id is fully reviewed."""
    spans = ann_data["annotations"][prompt_id]["spans"]
    total = len(spans)
    reviewed = sum(1 for s in spans if s.get("reviewed"))
    return reviewed == total and total > 0


def get_reviewed_count(ann_data, prompt_id):
    spans = ann_data["annotations"][prompt_id]["spans"]
    return sum(1 for s in spans if s.get("reviewed"))


def get_total_count(ann_data, prompt_id):
    return len(ann_data["annotations"][prompt_id]["spans"])


def select_best_annotation(candidates):
    """
    Select best annotation from candidates list.
    Each candidate: (ann_data, source_file)
    """
    def sort_key(c):
        ann_data, source_file, prompt_id = c
        reviewer = ann_data["metadata"]["reviewer"]
        completed_at = ann_data["metadata"].get("completed_at", "")
        fully_rev = is_fully_reviewed(ann_data, prompt_id)
        is_expert = reviewer in EXPERT_REVIEWERS
        reviewed_count = get_reviewed_count(ann_data, prompt_id)
        return (
            fully_rev,
            is_expert,
            reviewed_count,
            completed_at,
        )

    candidates.sort(key=sort_key, reverse=True)
    return candidates[0]


def merge_adjacent_spans(spans, gap_threshold=GAP_THRESHOLD):
    """Merge adjacent spans with same dimension+score if gap <= threshold."""
    if not spans:
        return spans

    by_dim_score = defaultdict(list)
    for s in spans:
        key = (s["dimension"], s.get("score", 0))
        by_dim_score[key].append(s)

    merged = []
    standalone_keys = set()

    for (dim, score), group in by_dim_score.items():
        group.sort(key=lambda x: x["start"])
        current = dict(group[0])
        merge_count = 1

        for i in range(1, len(group)):
            nxt = group[i]
            gap = nxt["start"] - current["end"]
            if 0 <= gap <= gap_threshold:
                current["end"] = nxt["end"]
                current["text"] = current["text"] + nxt["text"]
                if current.get("note") and nxt.get("note"):
                    current["note"] = current["note"] + " | " + nxt["note"]
                elif nxt.get("note"):
                    current["note"] = nxt["note"]
                merge_count += 1
            else:
                if merge_count > 1:
                    current["merged_from_count"] = merge_count
                merged.append(current)
                current = dict(nxt)
                merge_count = 1

        if merge_count > 1:
            current["merged_from_count"] = merge_count
        merged.append(current)

    merged.sort(key=lambda x: (x["start"], x["end"]))
    return merged


def build_dimension_summary(kept_spans):
    summary = {}
    for s in kept_spans:
        dim = s.get("dimension", "?")
        if dim not in summary:
            summary[dim] = {"positive": 0, "negative": 0, "total": 0}
        summary[dim]["total"] += 1
        if s.get("score", 0) > 0:
            summary[dim]["positive"] += 1
        elif s.get("score", 0) < 0:
            summary[dim]["negative"] += 1
    return summary


def main():
    print("Loading annotation files...")
    all_annotations = load_all_annotation_files()
    audit_lookup = load_audit_prompts()

    print(f"  Found {len(all_annotations)} annotation files")

    prompt_candidates = defaultdict(list)
    source_files = set()

    for ann_data in all_annotations:
        source_file = ann_data["_source_file"]
        source_files.add(source_file)
        for prompt_id in ann_data["annotations"]:
            prompt_candidates[prompt_id].append((ann_data, source_file, prompt_id))

    all_prompt_ids = sorted(prompt_candidates.keys())
    print(f"  Found {len(all_prompt_ids)} unique prompt_ids across all files")

    duplicate_prompt_ids = [pid for pid, cands in prompt_candidates.items() if len(cands) > 1]

    excluded = []
    selected_sources = set()
    prompts_output = {}
    total_kept = 0
    total_rejected = 0
    total_human = 0
    pre_merge_kept = 0
    annotators = set()

    for prompt_id in all_prompt_ids:
        candidates = prompt_candidates[prompt_id]
        best_ann, best_source, _ = select_best_annotation(candidates)
        reviewer = best_ann["metadata"]["reviewer"]
        completed_at = best_ann["metadata"].get("completed_at", "")

        if not is_fully_reviewed(best_ann, prompt_id):
            all_sources = []
            for ann, sf, _ in candidates:
                r = ann["metadata"]["reviewer"]
                cat = ann["metadata"].get("completed_at", "")
                rc = get_reviewed_count(ann, prompt_id)
                tc = get_total_count(ann, prompt_id)
                all_sources.append({
                    "source_file": sf,
                    "reviewer": r,
                    "completed_at": cat,
                    "fully_reviewed": False,
                    "reviewed_spans": rc,
                    "total_spans": tc,
                })
            best_src = all_sources[0]
            excluded.append({
                "prompt_id": prompt_id,
                "product_label": best_ann["annotations"][prompt_id].get("product_label", ""),
                "reason": "No fully reviewed annotation available in final_result.",
                "best_available_source": {
                    "source_file": best_src["source_file"],
                    "reviewer": best_src["reviewer"],
                    "completed_at": best_src["completed_at"],
                    "reviewed_spans": best_src["reviewed_spans"],
                    "total_spans": best_src["total_spans"],
                },
                "all_sources": all_sources,
            })
            continue

        selected_sources.add(best_source)
        annotators.add(reviewer)

        prompt_data = best_ann["annotations"][prompt_id]
        spans = prompt_data["spans"]

        kept_spans = [s for s in spans if not s.get("rejected")]
        rejected_count = sum(1 for s in spans if s.get("rejected"))
        human_added = sum(1 for s in kept_spans if s.get("source") == "human")

        pre_merge_kept += len(kept_spans)
        merged_spans = merge_adjacent_spans(kept_spans)

        total_kept += len(merged_spans)
        total_rejected += rejected_count
        total_human += human_added

        audit_meta = audit_lookup.get(prompt_id) or audit_lookup.get(prompt_data.get("filename", "")) or {}

        source_occurrences = []
        for ann, sf, _ in candidates:
            r = ann["metadata"]["reviewer"]
            cat = ann["metadata"].get("completed_at", "")
            rc = get_reviewed_count(ann, prompt_id)
            tc = get_total_count(ann, prompt_id)
            fr = rc == tc and tc > 0
            source_occurrences.append({
                "source_file": sf,
                "reviewer": r,
                "completed_at": cat,
                "fully_reviewed": fr,
                "reviewed_spans": rc,
                "total_spans": tc,
            })

        prompts_output[prompt_id] = {
            "prompt_id": prompt_id,
            "company": prompt_data.get("company", audit_meta.get("company", "")),
            "product": prompt_data.get("product", audit_meta.get("product", "")),
            "product_label": prompt_data.get("product_label", audit_meta.get("product_label", "")),
            "filename": prompt_data.get("filename", audit_meta.get("filename", "")),
            "category": audit_meta.get("category", prompt_data.get("category", "Other")),
            "date": audit_meta.get("date", ""),
            "size_bytes": audit_meta.get("size_bytes", 0),
            "reviewer": reviewer,
            "kept_spans": merged_spans,
            "kept_count": len(merged_spans),
            "rejected_count": rejected_count,
            "human_added_count": human_added,
            "dimension_summary": build_dimension_summary(merged_spans),
            "source_file": best_source,
            "source_completed_at": completed_at,
            "source_occurrences": source_occurrences,
        }

    output = {
        "metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "description": f"Merged annotation results from {len(annotators)} selected annotators across {len(prompts_output)} fully reviewed system prompts",
            "total_prompts": len(prompts_output),
            "total_unique_prompts_seen": len(all_prompt_ids),
            "total_kept_spans": total_kept,
            "total_rejected": total_rejected,
            "total_human_added": total_human,
            "annotators": sorted(annotators),
            "dimensions": DIM_NAMES,
            "excluded_prompts": [e["prompt_id"] for e in excluded],
            "excluded_prompt_details": excluded,
            "selection_policy": "Deduplicated by prompt_id. Prefer fully reviewed annotations, then designated expert reviewers, then higher reviewed span count, then later completion time.",
            "source_submission_files": sorted(source_files),
            "selected_source_files": sorted(selected_sources),
            "duplicate_prompt_ids": sorted(duplicate_prompt_ids),
            "span_merge_applied": True,
            "span_merge_gap_threshold": GAP_THRESHOLD,
            "span_merge_description": f'Adjacent spans with same dimension+score merged if gap <= {GAP_THRESHOLD} chars. Text concatenated, notes joined with " | ".',
            "pre_merge_total_kept_spans": pre_merge_kept,
        },
        "prompts": prompts_output,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Merge complete!")
    print(f"  Total prompts: {len(prompts_output)}")
    print(f"  Excluded prompts: {len(excluded)}")
    for e in excluded:
        print(f"    - {e['prompt_id']}: {e['reason']}")
    print(f"  Total kept spans (pre-merge): {pre_merge_kept}")
    print(f"  Total kept spans (post-merge): {total_kept}")
    print(f"  Total rejected: {total_rejected}")
    print(f"  Total human-added: {total_human}")
    print(f"  Annotators: {sorted(annotators)}")
    print(f"  Duplicate prompt_ids: {len(duplicate_prompt_ids)}")
    print(f"  Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
