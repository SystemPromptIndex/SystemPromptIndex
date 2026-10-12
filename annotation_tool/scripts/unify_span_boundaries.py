#!/usr/bin/env python3
"""
Unify span boundaries across same-company same-paragraph prompts.

ONLY adjusts span start/end boundaries. NEVER copies labels between versions.

For each shared paragraph:
1. Pick the version with the most span boundaries as reference
2. For each other version, re-cut its OWN labels to match reference boundaries
3. Each label stays with its own version — no cross-version label copying

Example:
  Reference (Claude 3.7) has boundaries: [0-100, 100-300, 300-500]
  Target (Sonnet 4) has one span [0-500] with D6=-1

  Result: Sonnet 4 gets three spans [0-100 D6=-1], [100-300 D6=-1], [300-500 D6=-1]
  The label D6=-1 is spread to all sub-spans, but NO new labels are introduced.

Usage:
    python scripts/unify_span_boundaries.py --dry-run
    python scripts/unify_span_boundaries.py
"""

import json
import argparse
import copy
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).parent.parent
MERGED = ROOT / "annotation_tool_89" / "analysis" / "merged_all_annotations.json"
AUDIT = ROOT / "data" / "audit_prompts.json"


def load_prompt_texts():
    with AUDIT.open() as f:
        audit = json.load(f)
    texts = {}
    for p in audit:
        if not p.get("content"):
            continue
        pid = f"{p['company']}__{p['filename']}"
        texts[pid] = p["content"]
        texts[pid.replace(" ", "_")] = p["content"]
    return texts


def get_paragraphs(text, min_len=50):
    return [c.strip() for c in text.split("\n\n") if len(c.strip()) >= min_len]


def get_spans_covering(spans, para_start, para_end):
    return [s for s in spans if s.get("start", 0) < para_end and s.get("end", 0) > para_start]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    prompt_texts = load_prompt_texts()
    with MERGED.open() as f:
        data = json.load(f)
    original = copy.deepcopy(data)

    by_company = defaultdict(list)
    for pid, p in data["prompts"].items():
        by_company[p["company"]].append(pid)

    total_paras = 0
    total_adjusted = 0
    log = []

    for comp, pids in sorted(by_company.items()):
        if len(pids) < 2:
            continue
        pids_with_text = [pid for pid in pids if pid in prompt_texts]
        if len(pids_with_text) < 2:
            continue

        para_to_pids = defaultdict(set)
        for pid in pids_with_text:
            for para in get_paragraphs(prompt_texts[pid]):
                para_to_pids[para].add(pid)

        for para, para_pids in para_to_pids.items():
            if len(para_pids) < 2:
                continue

            # Collect span boundaries per version (relative to paragraph)
            version_info = {}
            for pid in para_pids:
                pt = prompt_texts[pid]
                para_start = pt.find(para)
                if para_start < 0:
                    continue
                para_end = para_start + len(para)
                covering = get_spans_covering(data["prompts"][pid]["kept_spans"], para_start, para_end)
                version_info[pid] = {
                    "para_start": para_start,
                    "covering": covering,
                    "boundaries": sorted(set(
                        (s["start"] - para_start, s["end"] - para_start)
                        for s in covering
                    )),
                }

            if len(version_info) < 2:
                continue

            # Check if boundaries already consistent
            all_bounds = [frozenset(v["boundaries"]) for v in version_info.values()]
            if len(set(all_bounds)) <= 1:
                continue

            # Pick reference: most unique boundaries
            ref_pid = max(version_info.keys(),
                key=lambda pid: len(version_info[pid]["boundaries"]))
            ref_bounds = version_info[ref_pid]["boundaries"]

            if not ref_bounds:
                continue

            total_paras += 1
            ref_label = data["prompts"][ref_pid]["product_label"]
            log.append(f"\n  [{comp}] \"{para[:80]}...\"")
            log.append(f"    Ref: {ref_label} ({len(ref_bounds)} boundaries)")

            for pid, vi in version_info.items():
                if pid == ref_pid:
                    continue

                target_label = data["prompts"][pid]["product_label"]
                para_start = vi["para_start"]
                old_covering = vi["covering"]
                old_ids = set(id(s) for s in old_covering)
                prompt = data["prompts"][pid]

                # For each OLD span, split it according to reference boundaries
                new_spans = []
                for old_span in old_covering:
                    old_rel_start = old_span["start"] - para_start
                    old_rel_end = old_span["end"] - para_start
                    old_dim = old_span["dimension"]
                    old_score = old_span.get("score", 0)
                    old_note = old_span.get("note", "")
                    old_source = old_span.get("source", "llm")

                    # Find which reference boundaries overlap with this old span
                    for ref_rs, ref_re in ref_bounds:
                        # Intersection
                        new_rs = max(old_rel_start, ref_rs)
                        new_re = min(old_rel_end, ref_re)
                        if new_rs >= new_re:
                            continue

                        abs_start = para_start + new_rs
                        abs_end = para_start + new_re
                        new_text = para[max(0, new_rs):new_re] if new_re <= len(para) else para[max(0, new_rs):]

                        new_spans.append({
                            "start": abs_start,
                            "end": abs_end,
                            "text": new_text,
                            "dimension": old_dim,
                            "score": old_score,
                            "note": old_note,
                            "source": old_source,
                            "reviewed": True,
                        })

                # Deduplicate: same (start, end, dim, score) → keep one
                seen = set()
                deduped = []
                for s in new_spans:
                    key = (s["start"], s["end"], s["dimension"], s["score"])
                    if key not in seen:
                        seen.add(key)
                        deduped.append(s)
                new_spans = deduped

                # Check if anything changed
                old_set = set(
                    (s["start"], s["end"], s["dimension"], s.get("score"))
                    for s in old_covering
                )
                new_set = set(
                    (s["start"], s["end"], s["dimension"], s["score"])
                    for s in new_spans
                )

                if old_set == new_set:
                    continue

                # Replace
                prompt["kept_spans"] = [s for s in prompt["kept_spans"] if id(s) not in old_ids]
                prompt["kept_spans"].extend(new_spans)
                prompt["kept_spans"].sort(key=lambda s: (s.get("start", 0), s.get("end", 0)))

                total_adjusted += abs(len(new_set) - len(old_set)) + len(new_set ^ old_set)
                log.append(f"    {target_label}: {len(old_set)} → {len(new_set)} spans")

    # Rebuild counts
    total_kept = 0
    for pid, prompt in data["prompts"].items():
        prompt["kept_count"] = len(prompt["kept_spans"])
        prompt["human_added_count"] = sum(1 for s in prompt["kept_spans"] if s.get("source") == "human")
        summary = {}
        for s in prompt["kept_spans"]:
            dim = s.get("dimension", "?")
            if dim not in summary:
                summary[dim] = {"positive": 0, "negative": 0, "total": 0}
            summary[dim]["total"] += 1
            if s.get("score", 0) > 0:
                summary[dim]["positive"] += 1
            elif s.get("score", 0) < 0:
                summary[dim]["negative"] += 1
        prompt["dimension_summary"] = summary
        total_kept += len(prompt["kept_spans"])
    data["metadata"]["total_kept_spans"] = total_kept

    old_kept = original["metadata"]["total_kept_spans"]
    new_kept = total_kept

    print(f"Paragraphs unified: {total_paras}")
    print(f"Spans adjusted: {total_adjusted}")
    print(f"Kept spans: {old_kept} → {new_kept} (delta: {new_kept - old_kept:+d})")

    # Verify: no new labels introduced
    for pid in data["prompts"]:
        old_labels = set(
            (s["dimension"], s.get("score"))
            for s in original["prompts"][pid]["kept_spans"]
        )
        new_labels = set(
            (s["dimension"], s.get("score"))
            for s in data["prompts"][pid]["kept_spans"]
        )
        introduced = new_labels - old_labels
        if introduced:
            print(f"  WARNING: New labels introduced in {pid}: {introduced}")

    for line in log:
        print(line)

    if args.dry_run:
        print(f"\n[DRY RUN] No files written.")
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = MERGED.with_name(f"merged_all_annotations_pre_unify_{ts}.json")
        with backup.open("w", encoding="utf-8") as f:
            json.dump(original, f, indent=2, ensure_ascii=False)
        print(f"\n  Backup: {backup}")
        with MERGED.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  Written: {MERGED}")


if __name__ == "__main__":
    main()
