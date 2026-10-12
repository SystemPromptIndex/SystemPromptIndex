#!/usr/bin/env python3
"""
Annotator Quality Analysis
===========================
Compares annotation behavior across all 6 annotators to identify
potential quality issues in non-expert annotators.

Analyzes:
  1. Basic statistics per annotator
  2. LLM span acceptance/rejection rates
  3. Human-added span rates
  4. Dimension distribution patterns
  5. Score polarity distribution
  6. Note length as a proxy for annotation depth
  7. Outlier detection vs. group norms
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
import statistics

SCRIPT_DIR = Path(__file__).parent
MERGED_FILE = SCRIPT_DIR / "merged_all_annotations.json"
FINAL_DIR = SCRIPT_DIR.parent / "outputs" / "final_result"

DIMS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]
DIM_NAMES = {
    "D1": "Identity Transparency",
    "D2": "Truthfulness & Info Integrity",
    "D3": "Privacy & Data Protection",
    "D4": "Tool/Action Safety",
    "D5": "User Agency & Manipulation",
    "D6": "Unsafe Request Handling",
    "D7": "Harm Prevention & User Safety",
    "D8": "Fairness, Inclusion & Neutrality",
}

EXPERT_ANNOTATORS = {"expert_1", "expert_2", "expert_3"}
ALL_FILES = sorted(FINAL_DIR.glob("annotations_*.json"))


def load_raw_annotations():
    """Load individual annotator files to get pre-merge data (including rejected spans)."""
    annotators = {}
    for f in ALL_FILES:
        with f.open() as fh:
            data = json.load(fh)
        reviewer = data["metadata"]["reviewer"]
        if reviewer == "expert_3":
            continue
        annotators[reviewer] = data
    return annotators


def load_merged():
    with MERGED_FILE.open() as f:
        return json.load(f)


def analyze_raw_acceptance(annotators: dict):
    """Per-annotator: how many LLM spans accepted vs rejected, how many human-added."""
    print("=" * 80)
    print("1. LLM SPAN ACCEPTANCE / REJECTION RATES (per annotator)")
    print("=" * 80)

    results = {}
    for reviewer, data in sorted(annotators.items()):
        total_llm = 0
        accepted_llm = 0
        rejected_llm = 0
        human_added = 0
        total_kept = 0

        for pid, ann in data["annotations"].items():
            for span in ann.get("spans", []):
                source = span.get("source", "llm")
                is_rejected = span.get("rejected", False)

                if source == "llm":
                    total_llm += 1
                    if is_rejected:
                        rejected_llm += 1
                    else:
                        accepted_llm += 1
                        total_kept += 1
                elif source == "human":
                    human_added += 1
                    total_kept += 1

        reject_rate = rejected_llm / total_llm * 100 if total_llm else 0
        human_rate = human_added / total_kept * 100 if total_kept else 0

        results[reviewer] = {
            "prompts": len(data["annotations"]),
            "total_llm": total_llm,
            "accepted": accepted_llm,
            "rejected": rejected_llm,
            "reject_rate": reject_rate,
            "human_added": human_added,
            "total_kept": total_kept,
            "human_rate": human_rate,
        }

        is_expert = "***" if reviewer in EXPERT_ANNOTATORS else "   "
        print(f"\n  {is_expert} {reviewer} (prompts: {len(data['annotations'])}, range: {data['metadata'].get('range_from')}-{data['metadata'].get('range_to')})")
        print(f"      LLM spans total:   {total_llm}")
        print(f"      Accepted:          {accepted_llm}  ({accepted_llm/total_llm*100:.1f}%)" if total_llm else "")
        print(f"      Rejected:          {rejected_llm}  ({reject_rate:.1f}%)")
        print(f"      Human-added:       {human_added}  ({human_rate:.1f}% of kept)")
        print(f"      Total kept:        {total_kept}")

    print(f"\n  --- Summary ---")
    expert_reject = [v["reject_rate"] for k, v in results.items() if k in EXPERT_ANNOTATORS]
    other_reject = [v["reject_rate"] for k, v in results.items() if k not in EXPERT_ANNOTATORS]
    expert_human = [v["human_rate"] for k, v in results.items() if k in EXPERT_ANNOTATORS]
    other_human = [v["human_rate"] for k, v in results.items() if k not in EXPERT_ANNOTATORS]

    print(f"  Expert avg reject rate:  {statistics.mean(expert_reject):.1f}%")
    print(f"  Others avg reject rate:  {statistics.mean(other_reject):.1f}%")
    print(f"  Expert avg human-added:  {statistics.mean(expert_human):.1f}%")
    print(f"  Others avg human-added:  {statistics.mean(other_human):.1f}%")

    return results


def analyze_dimension_distribution(annotators: dict):
    """Per-annotator dimension distribution of kept spans."""
    print("\n" + "=" * 80)
    print("2. DIMENSION DISTRIBUTION OF KEPT SPANS (per annotator)")
    print("=" * 80)

    all_dist = {}
    for reviewer, data in sorted(annotators.items()):
        dim_counts = Counter()
        total = 0
        for pid, ann in data["annotations"].items():
            for span in ann.get("spans", []):
                if span.get("rejected"):
                    continue
                dim = span.get("dimension", "?")
                if dim in DIMS:
                    dim_counts[dim] += 1
                    total += 1

        dist = {d: dim_counts[d] / total * 100 if total else 0 for d in DIMS}
        all_dist[reviewer] = dist

        is_expert = "***" if reviewer in EXPERT_ANNOTATORS else "   "
        print(f"\n  {is_expert} {reviewer} (total kept: {total})")
        for d in DIMS:
            bar = "#" * int(dist[d] / 2)
            print(f"      {d}: {dim_counts[d]:4d} ({dist[d]:5.1f}%)  {bar}")

    print(f"\n  --- Deviation from group mean ---")
    group_mean = {}
    for d in DIMS:
        vals = [all_dist[r][d] for r in all_dist]
        group_mean[d] = statistics.mean(vals)

    for reviewer in sorted(all_dist.keys()):
        is_expert = "***" if reviewer in EXPERT_ANNOTATORS else "   "
        deviations = []
        for d in DIMS:
            dev = all_dist[reviewer][d] - group_mean[d]
            deviations.append(abs(dev))
        avg_dev = statistics.mean(deviations)
        print(f"  {is_expert} {reviewer}: avg absolute deviation = {avg_dev:.2f}pp")
        for d in DIMS:
            dev = all_dist[reviewer][d] - group_mean[d]
            if abs(dev) > 3:
                flag = "HIGH" if abs(dev) > 5 else "moderate"
                print(f"        {d}: {dev:+.1f}pp ({flag})")


def analyze_polarity(annotators: dict):
    """Per-annotator positive vs negative score distribution."""
    print("\n" + "=" * 80)
    print("3. SCORE POLARITY DISTRIBUTION (per annotator)")
    print("=" * 80)

    for reviewer, data in sorted(annotators.items()):
        pos = 0
        neg = 0
        for pid, ann in data["annotations"].items():
            for span in ann.get("spans", []):
                if span.get("rejected"):
                    continue
                score = span.get("score", 0)
                if score > 0:
                    pos += 1
                elif score < 0:
                    neg += 1

        total = pos + neg
        neg_rate = neg / total * 100 if total else 0
        is_expert = "***" if reviewer in EXPERT_ANNOTATORS else "   "
        print(f"  {is_expert} {reviewer}: positive={pos}, negative={neg}, neg_rate={neg_rate:.1f}%, total={total}")


def analyze_per_dim_polarity(annotators: dict):
    """Per-annotator, per-dimension positive/negative breakdown."""
    print("\n" + "=" * 80)
    print("4. PER-DIMENSION POLARITY (per annotator)")
    print("=" * 80)

    all_data = {}
    for reviewer, data in sorted(annotators.items()):
        dim_pol = {d: {"pos": 0, "neg": 0} for d in DIMS}
        for pid, ann in data["annotations"].items():
            for span in ann.get("spans", []):
                if span.get("rejected"):
                    continue
                dim = span.get("dimension", "?")
                score = span.get("score", 0)
                if dim in DIMS:
                    if score > 0:
                        dim_pol[dim]["pos"] += 1
                    elif score < 0:
                        dim_pol[dim]["neg"] += 1
        all_data[reviewer] = dim_pol

    for d in DIMS:
        print(f"\n  {d} ({DIM_NAMES[d]}):")
        for reviewer in sorted(all_data.keys()):
            p = all_data[reviewer][d]["pos"]
            n = all_data[reviewer][d]["neg"]
            total = p + n
            neg_rate = n / total * 100 if total else 0
            is_expert = "***" if reviewer in EXPERT_ANNOTATORS else "   "
            print(f"    {is_expert} {reviewer:20s}: pos={p:3d}, neg={n:3d}, neg%={neg_rate:5.1f}%")


def analyze_note_quality(annotators: dict):
    """Analyze note lengths as proxy for annotation thoughtfulness."""
    print("\n" + "=" * 80)
    print("5. NOTE LENGTH ANALYSIS (proxy for annotation depth)")
    print("=" * 80)

    for reviewer, data in sorted(annotators.items()):
        note_lengths = []
        empty_notes = 0
        for pid, ann in data["annotations"].items():
            for span in ann.get("spans", []):
                if span.get("rejected"):
                    continue
                note = span.get("note", "")
                note_lengths.append(len(note))
                if not note.strip():
                    empty_notes += 1

        if not note_lengths:
            continue

        is_expert = "***" if reviewer in EXPERT_ANNOTATORS else "   "
        print(f"\n  {is_expert} {reviewer}:")
        print(f"      Total kept spans:  {len(note_lengths)}")
        print(f"      Empty notes:       {empty_notes} ({empty_notes/len(note_lengths)*100:.1f}%)")
        print(f"      Avg note length:   {statistics.mean(note_lengths):.0f} chars")
        print(f"      Median note len:   {statistics.median(note_lengths):.0f} chars")
        print(f"      Min / Max:         {min(note_lengths)} / {max(note_lengths)}")


def analyze_spans_per_prompt(annotators: dict):
    """Spans per prompt — are some annotators keeping too many or too few?"""
    print("\n" + "=" * 80)
    print("6. SPANS PER PROMPT (per annotator)")
    print("=" * 80)

    for reviewer, data in sorted(annotators.items()):
        spans_per_prompt = []
        for pid, ann in data["annotations"].items():
            kept = sum(1 for s in ann.get("spans", []) if not s.get("rejected"))
            spans_per_prompt.append(kept)

        if not spans_per_prompt:
            continue

        is_expert = "***" if reviewer in EXPERT_ANNOTATORS else "   "
        print(f"\n  {is_expert} {reviewer} ({len(spans_per_prompt)} prompts):")
        print(f"      Avg spans/prompt:  {statistics.mean(spans_per_prompt):.1f}")
        print(f"      Median:            {statistics.median(spans_per_prompt):.1f}")
        print(f"      Std dev:           {statistics.stdev(spans_per_prompt):.1f}" if len(spans_per_prompt) > 1 else "")
        print(f"      Min / Max:         {min(spans_per_prompt)} / {max(spans_per_prompt)}")


def analyze_reviewed_rate(annotators: dict):
    """Check if annotators actually reviewed all spans (reviewed=true)."""
    print("\n" + "=" * 80)
    print("7. REVIEW COMPLETENESS (did annotator mark spans as reviewed?)")
    print("=" * 80)

    for reviewer, data in sorted(annotators.items()):
        total = 0
        reviewed = 0
        for pid, ann in data["annotations"].items():
            for span in ann.get("spans", []):
                total += 1
                if span.get("reviewed"):
                    reviewed += 1

        rate = reviewed / total * 100 if total else 0
        is_expert = "***" if reviewer in EXPERT_ANNOTATORS else "   "
        flag = " ⚠️  INCOMPLETE" if rate < 100 else ""
        print(f"  {is_expert} {reviewer}: {reviewed}/{total} reviewed ({rate:.1f}%){flag}")


def analyze_rejection_by_dimension(annotators: dict):
    """Which dimensions do annotators reject most?"""
    print("\n" + "=" * 80)
    print("8. REJECTION PATTERNS BY DIMENSION (per annotator)")
    print("=" * 80)

    for reviewer, data in sorted(annotators.items()):
        dim_total = Counter()
        dim_rejected = Counter()
        for pid, ann in data["annotations"].items():
            for span in ann.get("spans", []):
                if span.get("source") == "llm":
                    dim = span.get("dimension", "?")
                    dim_total[dim] += 1
                    if span.get("rejected"):
                        dim_rejected[dim] += 1

        is_expert = "***" if reviewer in EXPERT_ANNOTATORS else "   "
        print(f"\n  {is_expert} {reviewer}:")
        for d in DIMS:
            t = dim_total[d]
            r = dim_rejected[d]
            rate = r / t * 100 if t else 0
            bar = "!" * int(rate / 5)
            print(f"      {d}: {r:3d}/{t:3d} rejected ({rate:5.1f}%)  {bar}")


def main():
    annotators = load_raw_annotations()
    print(f"Loaded {len(annotators)} annotator files: {', '.join(sorted(annotators.keys()))}")
    print(f"Expert annotators (marked with ***): {', '.join(sorted(EXPERT_ANNOTATORS - {'expert_3'}))}")
    print()

    analyze_raw_acceptance(annotators)
    analyze_dimension_distribution(annotators)
    analyze_polarity(annotators)
    analyze_per_dim_polarity(annotators)
    analyze_note_quality(annotators)
    analyze_spans_per_prompt(annotators)
    analyze_reviewed_rate(annotators)
    analyze_rejection_by_dimension(annotators)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
