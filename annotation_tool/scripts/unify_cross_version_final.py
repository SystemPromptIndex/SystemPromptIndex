#!/usr/bin/env python3
"""
Final cross-version unification for annotations_restructured.json.

Ensures that for every shared paragraph (same text appearing in 2+ same-company
prompts), the span + label set is IDENTICAL across all versions.

Strategy per shared paragraph:
  1. Collect all spans (fully inside paragraph) from every version
  2. Cluster ranges within ±5 chars → snap to most common range
  3. Union all dimensions across versions for each cluster
  4. Remove redundant sub-range spans whose dims are a subset of a larger span
  5. Write the canonical set back to ALL versions

Creates a timestamped backup before writing.
"""

import json
import copy
from pathlib import Path
from collections import defaultdict
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
ANN_FILE = ROOT / "annotation_tool_89" / "analysis" / "annotations_restructured.json"
AUDIT_FILE = ROOT / "data" / "audit_prompts.json"

SOURCE_PRIORITY = {
    "human": 0,
    "cross_version_review": 1,
    "cross_version_unify": 2,
    "llm": 3,
}
RANGE_TOLERANCE = 5
MIN_PARA_LEN = 50


def best_source(sources):
    return min(sources, key=lambda s: SOURCE_PRIORITY.get(s, 99))


def load_prompt_texts():
    with AUDIT_FILE.open("r", encoding="utf-8") as f:
        audit = json.load(f)
    texts = {}
    for p in audit:
        if not p.get("content"):
            continue
        pid = f"{p['company']}__{p['filename']}"
        texts[pid] = p["content"]
        texts[pid.replace(" ", "_")] = p["content"]
    return texts


def get_paragraphs(text):
    return [c.strip() for c in text.split("\n\n") if len(c.strip()) >= MIN_PARA_LEN]


def make_span_key(text):
    if len(text) <= 200:
        return text
    return text[:200] + "..."


def collect_paragraph_spans(prompt_data, prompt_text, para):
    para_start = prompt_text.find(para)
    if para_start < 0:
        return [], -1
    para_end = para_start + len(para)
    spans = []
    for key, sd in prompt_data["spans"].items():
        if sd["start"] >= para_start and sd["end"] <= para_end:
            spans.append(
                {
                    "key": key,
                    "rel_start": sd["start"] - para_start,
                    "rel_end": sd["end"] - para_start,
                    "dims": {
                        dim: copy.deepcopy(info)
                        for dim, info in sd.get("dimensions", {}).items()
                    },
                }
            )
    return spans, para_start


def signature(spans):
    return frozenset(
        (
            (s["rel_start"], s["rel_end"]),
            frozenset((d, info["score"]) for d, info in s["dims"].items()),
        )
        for s in spans
    )


def build_canonical(all_version_spans, para_text):
    flat = []
    for spans in all_version_spans.values():
        flat.extend(spans)
    if not flat:
        return []

    sorted_flat = sorted(flat, key=lambda s: (s["rel_start"], s["rel_end"]))
    clusters = []
    for span in sorted_flat:
        placed = False
        for cluster in clusters:
            if (
                abs(span["rel_start"] - cluster["ref_start"]) <= RANGE_TOLERANCE
                and abs(span["rel_end"] - cluster["ref_end"]) <= RANGE_TOLERANCE
            ):
                cluster["members"].append(span)
                placed = True
                break
        if not placed:
            clusters.append(
                {
                    "ref_start": span["rel_start"],
                    "ref_end": span["rel_end"],
                    "members": [span],
                }
            )

    canonical = []
    for cluster in clusters:
        members = cluster["members"]
        range_counts = defaultdict(int)
        for m in members:
            range_counts[(m["rel_start"], m["rel_end"])] += 1
        best_range = max(
            range_counts.keys(), key=lambda r: (range_counts[r], r[1] - r[0])
        )

        unified_dims = {}
        for m in members:
            for dim, info in m["dims"].items():
                src = info.get("source", "llm")
                note = info.get("note", "")
                if dim not in unified_dims:
                    unified_dims[dim] = {
                        "score": info["score"],
                        "note": note,
                        "_sources": [src],
                        "_notes": [note],
                    }
                else:
                    unified_dims[dim]["_sources"].append(src)
                    unified_dims[dim]["_notes"].append(note)

        for dim, info in unified_dims.items():
            info["source"] = best_source(info.pop("_sources"))
            notes = info.pop("_notes")
            info["note"] = max(notes, key=len)

        canonical.append(
            {
                "rel_start": best_range[0],
                "rel_end": best_range[1],
                "text": para_text[best_range[0] : best_range[1]],
                "dims": unified_dims,
            }
        )

    # Remove redundant subsets: if span A ⊂ span B and dims(A) ⊆ dims(B), drop A
    to_remove = set()
    for i, a in enumerate(canonical):
        if i in to_remove:
            continue
        for j, b in enumerate(canonical):
            if i == j or j in to_remove:
                continue
            if a["rel_start"] >= b["rel_start"] and a["rel_end"] <= b["rel_end"]:
                a_dims = {(d, info["score"]) for d, info in a["dims"].items()}
                b_dims = {(d, info["score"]) for d, info in b["dims"].items()}
                if a_dims <= b_dims:
                    to_remove.add(i)
                    break
    canonical = [c for i, c in enumerate(canonical) if i not in to_remove]
    return canonical


def main():
    prompt_texts = load_prompt_texts()
    with ANN_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    original = copy.deepcopy(data)

    company_groups = defaultdict(list)
    for pid, p in data["prompts"].items():
        company_groups[p["company"]].append(pid)

    stats = {"checked": 0, "fixed": 0, "spans_removed": 0, "spans_added": 0}
    log = []

    for company, pids in sorted(company_groups.items()):
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
            stats["checked"] += 1

            version_spans = {}
            para_starts = {}
            for pid in sorted(para_pids):
                spans, ps = collect_paragraph_spans(
                    data["prompts"][pid], prompt_texts[pid], para
                )
                if ps < 0:
                    continue
                version_spans[pid] = spans
                para_starts[pid] = ps

            if len(version_spans) < 2:
                continue

            sigs = {pid: signature(spans) for pid, spans in version_spans.items()}
            if len(set(sigs.values())) <= 1:
                continue

            canonical = build_canonical(version_spans, para)

            for pid in sorted(version_spans.keys()):
                para_start = para_starts[pid]
                prompt = data["prompts"][pid]

                for s in version_spans[pid]:
                    if s["key"] in prompt["spans"]:
                        del prompt["spans"][s["key"]]
                        stats["spans_removed"] += 1

                for cs in canonical:
                    abs_start = para_start + cs["rel_start"]
                    abs_end = para_start + cs["rel_end"]
                    text = cs["text"]
                    key = make_span_key(text)

                    if key in prompt["spans"]:
                        existing = prompt["spans"][key]
                        if existing["start"] == abs_start and existing["end"] == abs_end:
                            existing["dimensions"] = copy.deepcopy(cs["dims"])
                            continue
                        key = make_span_key(text) + f" [{abs_start}]"

                    prompt["spans"][key] = {
                        "start": abs_start,
                        "end": abs_end,
                        "text": text,
                        "dimensions": copy.deepcopy(cs["dims"]),
                    }
                    stats["spans_added"] += 1

            stats["fixed"] += 1
            log.append(
                f"  [{company}] {para[:100].replace(chr(10), ' ')}..."
            )

    # --- Verify ---
    remaining = 0
    remaining_details = []
    for company, pids in sorted(company_groups.items()):
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
            sigs = set()
            for pid in sorted(para_pids):
                spans, _ = collect_paragraph_spans(
                    data["prompts"][pid], prompt_texts[pid], para
                )
                sigs.add(signature(spans))
            if len(sigs) > 1:
                remaining += 1
                remaining_details.append(
                    f"  [{company}] {para[:100].replace(chr(10), ' ')}..."
                )

    # --- Save ---
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    data["metadata"]["cross_version_final_unify_v2"] = datetime.now().isoformat()
    data["metadata"]["cross_version_final_unify_v2_fixed"] = stats["fixed"]
    data["metadata"]["cross_version_final_unify_v2_remaining"] = remaining

    backup = ANN_FILE.with_name(
        f"annotations_restructured_pre_final_unify_v2_{ts}.json"
    )
    with backup.open("w", encoding="utf-8") as f:
        json.dump(original, f, ensure_ascii=False, indent=2)

    with ANN_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*70}")
    print(f"CROSS-VERSION FINAL UNIFICATION RESULTS")
    print(f"{'='*70}")
    print(f"Shared paragraphs checked: {stats['checked']}")
    print(f"Paragraphs unified: {stats['fixed']}")
    print(f"Spans removed: {stats['spans_removed']}")
    print(f"Spans added: {stats['spans_added']}")
    print(f"Remaining inconsistencies: {remaining}")
    print(f"Backup: {backup.name}")

    if log:
        print(f"\nParagraphs fixed ({len(log)}):")
        for l in log:
            print(l)

    if remaining_details:
        print(f"\nStill inconsistent ({remaining}):")
        for d in remaining_details:
            print(d)


if __name__ == "__main__":
    main()
