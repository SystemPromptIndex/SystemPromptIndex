"""
Apply cross-version conflict review decisions to merged_all_annotations.json.

Principle: same company, different versions → same paragraph must have
identical spans and labels.

- Agree + final_labels: for ALL versions with this text, remove all matching
  spans, then add exactly the final_labels.
- Discuss: for ALL versions, remove all matching spans.

Usage: python scripts/apply_cross_version_review.py
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
REVIEW_FILE = BASE_DIR / "annotation_tool_89" / "analysis" / "review_results_2026-03-07.json"
MERGED_FILE = BASE_DIR / "annotation_tool_89" / "outputs" / "final_result" / "analysis" / "merged_all_annotations.json"
RAW_PROMPTS_FILE = BASE_DIR / "data" / "audit_prompts_filtered.json"

MATCH_PREFIX_LEN = 50


def _normalize_prefix(text):
    t = text.strip()
    t = re.sub(r"^[\*\-\•]\s+", "", t)
    t = re.sub(r"^\d+\.\s+", "", t)
    return t.strip()[:MATCH_PREFIX_LEN]


def load_prompt_contents():
    with RAW_PROMPTS_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    result = {}
    for p in raw:
        company = re.sub(r"[^a-zA-Z0-9]", "_", p.get("company", "unknown"))
        fn = re.sub(r"[^a-zA-Z0-9._-]", "_", p.get("filename", ""))
        pid = f"{company}__{fn}"
        if pid not in result:
            result[pid] = p.get("content", "")
    return result


def text_matches(span_text, overlap_text):
    sp = _normalize_prefix(span_text)
    op = _normalize_prefix(overlap_text)
    if not sp or not op:
        return False
    return sp in op or op in sp


def find_text_position(content, overlap_text):
    search = overlap_text[:80]
    idx = content.find(search)
    if idx < 0:
        search_stripped = re.sub(r"^[\*\-\•]\s+", "", overlap_text.strip())[:80]
        idx = content.find(search_stripped)
    if idx < 0:
        return None, None
    end_search = overlap_text.rstrip()[-40:] if len(overlap_text) > 40 else overlap_text
    end_search_stripped = re.sub(r"^[\*\-\•]\s+", "", end_search.strip())
    end_idx = content.find(end_search_stripped, idx)
    if end_idx >= 0:
        end_idx += len(end_search_stripped)
    else:
        end_idx = idx + len(overlap_text)
    return idx, end_idx


def main():
    with REVIEW_FILE.open("r", encoding="utf-8") as f:
        review = json.load(f)
    with MERGED_FILE.open("r", encoding="utf-8") as f:
        merged = json.load(f)

    prompt_contents = load_prompt_contents()
    conflicts = review["cross_version_conflicts"]
    prompts = merged["prompts"]

    agree_with_labels = [c for c in conflicts if c["review_status"] == "agree" and c.get("final_labels")]
    discuss_items = [c for c in conflicts if c["review_status"] == "discuss"]

    stats = {
        "spans_removed": 0,
        "spans_added": 0,
        "prompts_modified": set(),
        "conflicts_applied": 0,
        "discuss_applied": 0,
        "discuss_removed": 0,
        "skipped": [],
    }

    # --- Step 1: Agree + final_labels → unify all versions ---
    print(f"=== Applying {len(agree_with_labels)} agree+final_labels conflicts ===")
    for c in agree_with_labels:
        overlap_text = c["overlap_text"]
        final_labels = c["final_labels"]
        involved_pids = list(dict.fromkeys(a["prompt_id"] for a in c["annotations"]))

        for pid in involved_pids:
            if pid not in prompts:
                stats["skipped"].append(f"{pid} not in merged ({c['_id']})")
                continue

            kept = prompts[pid]["kept_spans"]

            # Find all matching spans and a reference for position
            match_indices = [i for i, s in enumerate(kept) if text_matches(s.get("text", ""), overlap_text)]

            if match_indices:
                ref = kept[match_indices[0]]
                start, end, text = ref["start"], ref["end"], ref["text"]
            else:
                content = prompt_contents.get(pid, "")
                start, end = find_text_position(content, overlap_text)
                if start is None:
                    stats["skipped"].append(f"text not found in {pid} ({c['_id']})")
                    continue
                text = content[start:end]

            # Remove ALL matching spans
            for idx in sorted(match_indices, reverse=True):
                kept.pop(idx)
                stats["spans_removed"] += 1

            # Add exactly the final_labels
            for lb in final_labels:
                kept.append({
                    "dimension": lb["dim"],
                    "score": lb["score"],
                    "start": start,
                    "end": end,
                    "text": text,
                    "note": "",
                    "source": "cross_version_review",
                    "reviewed": True,
                })
                stats["spans_added"] += 1

            stats["prompts_modified"].add(pid)
        stats["conflicts_applied"] += 1

    # --- Step 2: Discuss → delete from all versions ---
    print(f"=== Deleting spans for {len(discuss_items)} discuss conflicts ===")
    for c in discuss_items:
        overlap_text = c["overlap_text"]
        involved_pids = list(dict.fromkeys(a["prompt_id"] for a in c["annotations"]))

        for pid in involved_pids:
            if pid not in prompts:
                continue

            kept = prompts[pid]["kept_spans"]
            match_indices = [i for i, s in enumerate(kept) if text_matches(s.get("text", ""), overlap_text)]

            for idx in sorted(match_indices, reverse=True):
                kept.pop(idx)
                stats["discuss_removed"] += 1

            if match_indices:
                stats["prompts_modified"].add(pid)

        stats["discuss_applied"] += 1

    # --- Re-sort and update metadata ---
    for pid in stats["prompts_modified"]:
        kept = prompts[pid]["kept_spans"]
        kept.sort(key=lambda s: (s["start"], s.get("dimension", "")))
        prompts[pid]["kept_count"] = len(kept)

        dim_summary = {}
        for s in kept:
            d = s["dimension"]
            if d not in dim_summary:
                dim_summary[d] = {"positive": 0, "negative": 0, "zero": 0}
            if s["score"] > 0:
                dim_summary[d]["positive"] += 1
            elif s["score"] < 0:
                dim_summary[d]["negative"] += 1
            else:
                dim_summary[d]["zero"] += 1
        prompts[pid]["dimension_summary"] = dim_summary

    total_kept = sum(len(p.get("kept_spans", [])) for p in prompts.values())
    merged["metadata"]["total_kept_spans"] = total_kept
    merged["metadata"]["cross_version_review_applied"] = datetime.now().isoformat()

    # --- Backup and save ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = MERGED_FILE.parent / f"merged_all_annotations_pre_crossversion_{timestamp}.json"
    shutil.copy2(MERGED_FILE, backup)
    print(f"Backup: {backup.name}")

    with MERGED_FILE.open("w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"\n=== Results ===")
    print(f"Agree+labels applied: {stats['conflicts_applied']}")
    print(f"  Spans removed: {stats['spans_removed']}")
    print(f"  Spans added (unified): {stats['spans_added']}")
    print(f"Discuss applied: {stats['discuss_applied']}")
    print(f"  Spans removed: {stats['discuss_removed']}")
    print(f"Prompts modified: {len(stats['prompts_modified'])}")
    print(f"Total kept spans: {total_kept}")
    if stats["skipped"]:
        print(f"\nSkipped ({len(stats['skipped'])}):")
        for s in stats["skipped"]:
            print(f"  - {s}")


if __name__ == "__main__":
    main()
