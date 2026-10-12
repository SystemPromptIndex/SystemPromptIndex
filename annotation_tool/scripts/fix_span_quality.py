#!/usr/bin/env python3
"""
Fix span quality issues in annotations_restructured.json:

1. text_mismatch — stored text != actual content at [start:end] → re-read from source
2. starts_mid_word / ends_mid_word — extend boundary to nearest word boundary
3. starts_with_whitespace — trim leading/trailing whitespace, adjust start/end

After individual fixes, re-runs cross-version unification to keep consistency.
Creates a timestamped backup before writing.
"""

import json
import copy
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
ANN_FILE = ROOT / "annotation_tool_89" / "analysis" / "annotations_restructured.json"
AUDIT_FILE = ROOT / "data" / "audit_prompts.json"

WORD_BOUNDARY = re.compile(r"\s")


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


def make_span_key(text):
    if len(text) <= 200:
        return text
    return text[:200] + "..."


def main():
    prompt_texts = load_prompt_texts()
    with ANN_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    original = copy.deepcopy(data)

    stats = {
        "text_mismatch_fixed": 0,
        "mid_word_fixed": 0,
        "whitespace_trimmed": 0,
        "spans_rekeyed": 0,
    }
    log = []

    for pid, prompt in data["prompts"].items():
        full_text = prompt_texts.get(pid, "")
        if not full_text:
            continue

        new_spans = {}
        for span_key, span in list(prompt["spans"].items()):
            start = span["start"]
            end = span["end"]
            stored_text = span["text"]
            changed = False

            # --- Fix 1: text_mismatch — re-read from source ---
            actual_text = full_text[start:end]
            if actual_text != stored_text and actual_text.strip() != stored_text.strip():
                # Try to find stored_text near the position
                search_start = max(0, start - 50)
                search_end = min(len(full_text), end + 50)
                region = full_text[search_start:search_end]
                # Try exact find
                idx = region.find(stored_text.strip())
                if idx >= 0:
                    new_start = search_start + idx
                    new_end = new_start + len(stored_text.strip())
                    start = new_start
                    end = new_end
                    actual_text = full_text[start:end]
                    stats["text_mismatch_fixed"] += 1
                    changed = True
                    log.append(f"  text_mismatch: [{prompt['product_label']}] repositioned [{span['start']}-{span['end']}] → [{start}-{end}]")
                else:
                    # Can't find — just update text to match position
                    if actual_text.strip():
                        stats["text_mismatch_fixed"] += 1
                        changed = True
                        log.append(f"  text_mismatch: [{prompt['product_label']}] updated text at [{start}-{end}]")

            # --- Fix 2: starts_with_whitespace — trim ---
            actual_text = full_text[start:end]
            lstripped = actual_text.lstrip()
            rstripped = lstripped.rstrip()
            leading = len(actual_text) - len(lstripped)
            trailing = len(lstripped) - len(rstripped)
            if leading > 0 or trailing > 0:
                new_start = start + leading
                new_end = end - trailing
                if new_start < new_end and full_text[new_start:new_end].strip():
                    start = new_start
                    end = new_end
                    actual_text = full_text[start:end]
                    stats["whitespace_trimmed"] += 1
                    changed = True

            # --- Fix 3: mid_word boundaries — extend to word boundary ---
            # Check start: if char before start is alphanumeric AND char at start is alphanumeric
            if start > 0 and full_text[start - 1].isalnum() and full_text[start].isalnum():
                # Move start back to word boundary
                while start > 0 and full_text[start - 1].isalnum():
                    start -= 1
                actual_text = full_text[start:end]
                stats["mid_word_fixed"] += 1
                changed = True
                log.append(f"  mid_word_start: [{prompt['product_label']}] extended start to {start}")

            # Check end: if char at end-1 is alphanumeric AND char at end is alphanumeric
            if end < len(full_text) and full_text[end - 1].isalnum() and full_text[end].isalnum():
                # Move end forward to word boundary
                while end < len(full_text) and full_text[end].isalnum():
                    end += 1
                actual_text = full_text[start:end]
                stats["mid_word_fixed"] += 1
                changed = True
                log.append(f"  mid_word_end: [{prompt['product_label']}] extended end to {end}")

            # Update span
            final_text = full_text[start:end]
            span["start"] = start
            span["end"] = end
            span["text"] = final_text

            # Re-key if text changed
            new_key = make_span_key(final_text)
            if new_key != span_key:
                # Avoid collision
                if new_key in new_spans:
                    new_key = make_span_key(final_text) + f" [{start}]"
                new_spans[new_key] = span
                stats["spans_rekeyed"] += 1
            else:
                new_spans[span_key] = span

        prompt["spans"] = new_spans

    # --- Re-run cross-version unification to maintain consistency ---
    print("Re-running cross-version unification...")

    SOURCE_PRIORITY = {"human": 0, "cross_version_review": 1, "cross_version_unify": 2, "llm": 3}

    def best_source(sources):
        return min(sources, key=lambda s: SOURCE_PRIORITY.get(s, 99))

    def get_paragraphs(text):
        return [c.strip() for c in text.split("\n\n") if len(c.strip()) >= 50]

    def collect_paragraph_spans(prompt_data, prompt_text, para):
        para_start = prompt_text.find(para)
        if para_start < 0:
            return [], -1
        para_end = para_start + len(para)
        spans = []
        for key, sd in prompt_data["spans"].items():
            if sd["start"] >= para_start and sd["end"] <= para_end:
                spans.append({
                    "key": key,
                    "rel_start": sd["start"] - para_start,
                    "rel_end": sd["end"] - para_start,
                    "dims": {dim: copy.deepcopy(info) for dim, info in sd.get("dimensions", {}).items()},
                })
        return spans, para_start

    def signature(spans):
        return frozenset(
            ((s["rel_start"], s["rel_end"]), frozenset((d, info["score"]) for d, info in s["dims"].items()))
            for s in spans
        )

    company_groups = defaultdict(list)
    for pid, p in data["prompts"].items():
        company_groups[p["company"]].append(pid)

    unify_fixed = 0
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
            version_spans = {}
            para_starts = {}
            for pid in sorted(para_pids):
                spans, ps = collect_paragraph_spans(data["prompts"][pid], prompt_texts[pid], para)
                if ps < 0:
                    continue
                version_spans[pid] = spans
                para_starts[pid] = ps
            if len(version_spans) < 2:
                continue
            sigs = {pid: signature(spans) for pid, spans in version_spans.items()}
            if len(set(sigs.values())) <= 1:
                continue

            # Build canonical
            flat = []
            for spans in version_spans.values():
                flat.extend(spans)
            if not flat:
                continue
            sorted_flat = sorted(flat, key=lambda s: (s["rel_start"], s["rel_end"]))
            clusters = []
            for span in sorted_flat:
                placed = False
                for cluster in clusters:
                    if abs(span["rel_start"] - cluster["ref_start"]) <= 5 and abs(span["rel_end"] - cluster["ref_end"]) <= 5:
                        cluster["members"].append(span)
                        placed = True
                        break
                if not placed:
                    clusters.append({"ref_start": span["rel_start"], "ref_end": span["rel_end"], "members": [span]})

            canonical = []
            for cluster in clusters:
                range_counts = defaultdict(int)
                for m in cluster["members"]:
                    range_counts[(m["rel_start"], m["rel_end"])] += 1
                best_range = max(range_counts.keys(), key=lambda r: (range_counts[r], r[1] - r[0]))
                unified_dims = {}
                for m in cluster["members"]:
                    for dim, info in m["dims"].items():
                        src = info.get("source", "llm")
                        note = info.get("note", "")
                        if dim not in unified_dims:
                            unified_dims[dim] = {"score": info["score"], "note": note, "_sources": [src], "_notes": [note]}
                        else:
                            unified_dims[dim]["_sources"].append(src)
                            unified_dims[dim]["_notes"].append(note)
                for dim, info in unified_dims.items():
                    info["source"] = best_source(info.pop("_sources"))
                    notes = info.pop("_notes")
                    info["note"] = max(notes, key=len)
                canonical.append({"rel_start": best_range[0], "rel_end": best_range[1],
                                  "text": para[best_range[0]:best_range[1]], "dims": unified_dims})

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

            for pid in sorted(version_spans.keys()):
                para_start = para_starts[pid]
                prompt = data["prompts"][pid]
                for s in version_spans[pid]:
                    if s["key"] in prompt["spans"]:
                        del prompt["spans"][s["key"]]
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
                    prompt["spans"][key] = {"start": abs_start, "end": abs_end, "text": text,
                                            "dimensions": copy.deepcopy(cs["dims"])}
            unify_fixed += 1

    # --- Save ---
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    data["metadata"]["span_quality_fix"] = datetime.now().isoformat()
    data["metadata"]["span_quality_fix_stats"] = stats

    backup = ANN_FILE.with_name(f"annotations_restructured_pre_quality_fix_{ts}.json")
    with backup.open("w", encoding="utf-8") as f:
        json.dump(original, f, ensure_ascii=False, indent=2)
    with ANN_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*70}")
    print(f"SPAN QUALITY FIX RESULTS")
    print(f"{'='*70}")
    print(f"Text mismatches fixed: {stats['text_mismatch_fixed']}")
    print(f"Mid-word boundaries fixed: {stats['mid_word_fixed']}")
    print(f"Whitespace trimmed: {stats['whitespace_trimmed']}")
    print(f"Spans re-keyed: {stats['spans_rekeyed']}")
    print(f"Cross-version re-unified: {unify_fixed}")
    print(f"Backup: {backup.name}")

    if log:
        print(f"\nDetails ({len(log)}):")
        for l in log[:50]:
            print(l)
        if len(log) > 50:
            print(f"  ... and {len(log) - 50} more")


if __name__ == "__main__":
    main()
