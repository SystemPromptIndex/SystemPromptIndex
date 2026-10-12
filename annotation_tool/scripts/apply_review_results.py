#!/usr/bin/env python3
"""
Apply review results back to merged_all_annotations.json.

Two review types:
1. Negative spans: "agree" keeps, "disagree" removes
2. Cross-version conflicts: align ALL versions to the user's final_labels L
   - Add missing spans
   - Remove extra spans
   - Modify wrong labels

Usage:
    python scripts/apply_review_results.py review_results_2026-03-07.json --dry-run
    python scripts/apply_review_results.py review_results_2026-03-07.json
"""

import json
import argparse
import copy
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
MERGED = ROOT / "annotation_tool_89" / "analysis" / "merged_all_annotations.json"
AUDIT = ROOT / "data" / "audit_prompts.json"


def load_prompt_texts():
    """Load original prompt texts for finding start/end of new spans."""
    if not AUDIT.exists():
        return {}
    with AUDIT.open("r", encoding="utf-8") as f:
        audit = json.load(f)
    texts = {}
    for p in audit:
        fn = p.get("filename", "")
        company = p.get("company", "")
        pid = f"{company}__{fn}"
        if p.get("content"):
            texts[pid] = p["content"]
    return texts


def find_text_position(prompt_text, sentence):
    """Find start/end of a sentence in the original prompt text."""
    idx = prompt_text.find(sentence)
    if idx >= 0:
        return idx, idx + len(sentence)
    clean = sentence.strip()
    idx = prompt_text.find(clean)
    if idx >= 0:
        return idx, idx + len(clean)
    return None, None


def apply_negative_reviews(merged, neg_reviews, log):
    removed = 0
    for nr in neg_reviews:
        if nr.get("review_status") != "disagree":
            continue
        pid = nr["prompt_id"]
        if pid not in merged["prompts"]:
            continue
        prompt = merged["prompts"][pid]
        text = nr["text"]
        dim = nr["dimension"]
        score = nr["score"]
        before = len(prompt["kept_spans"])
        prompt["kept_spans"] = [
            s for s in prompt["kept_spans"]
            if not (s["text"] == text and s["dimension"] == dim and s.get("score") == score)
        ]
        diff = before - len(prompt["kept_spans"])
        if diff > 0:
            removed += diff
            log.append(f"  REMOVE [{pid}]: {dim}(s={score}) \"{text[:80]}\"")
    return removed


def apply_conflict_decisions(merged, conf_reviews, prompt_texts, log):
    """
    For each conflict with final_labels L:
    Find all same-company prompts containing the shared text.
    For each such prompt, ensure its spans match L exactly:
      - Add spans in L but missing from prompt
      - Remove spans in prompt but not in L
      - Keep spans that already match
    """
    MAX_LEN_DIFF = 50
    groups_applied = 0
    spans_added = 0
    spans_removed = 0
    spans_kept = 0
    skipped_no_text = 0

    for cr in conf_reviews:
        final_labels = cr.get("final_labels", [])
        if not final_labels:
            continue

        company = cr["company"]
        overlap_text = cr.get("overlap_text", "").strip()
        if not overlap_text:
            continue

        final_set = set((l["dim"], l["score"]) for l in final_labels)
        groups_applied += 1
        labels_str = ", ".join(f"{l['dim']}={'+1' if l['score'] > 0 else '-1'}" for l in final_labels)
        log.append(f"\n  UNIFY [{company}] → [{labels_str}]")
        log.append(f"    Text: \"{overlap_text[:100]}\"")

        for pid, prompt in merged["prompts"].items():
            if prompt["company"] != company:
                continue

            # Check if this prompt contains the shared text
            # Method 1: check existing spans
            matching_spans = []
            for si, span in enumerate(prompt["kept_spans"]):
                span_text = span["text"].strip()
                if overlap_text in span_text or span_text in overlap_text:
                    if abs(len(span_text) - len(overlap_text)) <= MAX_LEN_DIFF:
                        matching_spans.append((si, span))

            # Method 2: check original prompt text
            has_text_in_prompt = False
            pt = prompt_texts.get(pid, "")
            if pt:
                has_text_in_prompt = overlap_text in pt

            if not matching_spans and not has_text_in_prompt:
                continue

            # Current labels for this text in this prompt
            current_set = set((s["dimension"], s.get("score")) for _, s in matching_spans)

            if current_set == final_set:
                spans_kept += len(matching_spans)
                continue

            # Labels to ADD (in L but not in current)
            to_add = final_set - current_set
            # Labels to REMOVE (in current but not in L)
            to_remove = current_set - final_set
            # Labels to KEEP
            to_keep = current_set & final_set

            spans_kept += len(to_keep)

            # REMOVE extra spans (only exact/near-exact matches, not larger spans)
            if to_remove:
                indices_to_remove = []
                for si, span in matching_spans:
                    key = (span["dimension"], span.get("score"))
                    if key in to_remove:
                        indices_to_remove.append(si)
                        spans_removed += 1
                        log.append(f"    DELETE [{pid}]: {span['dimension']}(s={span.get('score')})")

                for si in sorted(indices_to_remove, reverse=True):
                    prompt["kept_spans"].pop(si)
                # Update matching_spans indices after deletion
                matching_spans = [(si, s) for si, s in enumerate(prompt["kept_spans"])
                    if (overlap_text in s["text"].strip() or s["text"].strip() in overlap_text)
                    and abs(len(s["text"].strip()) - len(overlap_text)) <= MAX_LEN_DIFF]

            # ADD missing spans
            if to_add:
                ref_span = None
                if matching_spans:
                    ref_span = matching_spans[0][1]
                if not ref_span and pt:
                    start, end = find_text_position(pt, overlap_text)
                    if start is not None:
                        ref_span = {"text": overlap_text, "start": start, "end": end}
                if not ref_span:
                    skipped_no_text += 1
                    log.append(f"    SKIP [{pid}]: cannot find text position (no original text)")
                    continue

                for dim, score in to_add:
                    # Check if a LARGER span already covers this text with same (dim, score)
                    already_covered = False
                    for existing in prompt["kept_spans"]:
                        if existing["dimension"] == dim and existing.get("score") == score:
                            et = existing["text"].strip()
                            if overlap_text in et or et in overlap_text:
                                already_covered = True
                                break
                    if already_covered:
                        spans_kept += 1
                        log.append(f"    KEEP [{pid}]: {dim}(s={score}) (already in larger span)")
                        continue

                    new_span = {
                        "dimension": dim,
                        "score": score,
                        "start": ref_span.get("start", 0),
                        "end": ref_span.get("end", 0),
                        "text": ref_span.get("text", overlap_text),
                        "note": "Added by cross-version unification",
                        "source": "human",
                        "reviewed": True,
                    }
                    prompt["kept_spans"].append(new_span)
                    spans_added += 1
                    log.append(f"    ADD [{pid}]: {dim}(s={score})")

            # Re-sort spans by start position
            prompt["kept_spans"].sort(key=lambda s: (s.get("start", 0), s.get("end", 0)))

    return groups_applied, spans_added, spans_removed, spans_kept, skipped_no_text


def rebuild_summaries(merged):
    total_kept = 0
    total_human = 0
    for pid, prompt in merged["prompts"].items():
        spans = prompt["kept_spans"]
        prompt["kept_count"] = len(spans)
        prompt["human_added_count"] = sum(1 for s in spans if s.get("source") == "human")
        summary = {}
        for s in spans:
            dim = s.get("dimension", "?")
            if dim not in summary:
                summary[dim] = {"positive": 0, "negative": 0, "total": 0}
            summary[dim]["total"] += 1
            if s.get("score", 0) > 0:
                summary[dim]["positive"] += 1
            elif s.get("score", 0) < 0:
                summary[dim]["negative"] += 1
        prompt["dimension_summary"] = summary
        total_kept += len(spans)
        total_human += prompt["human_added_count"]
    merged["metadata"]["total_kept_spans"] = total_kept
    merged["metadata"]["total_human_added"] = total_human


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("review_file")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", help="Output path (default: overwrite merged)")
    args = parser.parse_args()

    with open(args.review_file, "r", encoding="utf-8") as f:
        review = json.load(f)

    neg = review.get("negative_spans", [])
    conf = review.get("cross_version_conflicts", [])
    prompt_texts = load_prompt_texts()

    print(f"Review file: {args.review_file}")
    print(f"  Negative spans: {len(neg)}")
    print(f"    agree: {sum(1 for r in neg if r.get('review_status')=='agree')}")
    print(f"    disagree (will remove): {sum(1 for r in neg if r.get('review_status')=='disagree')}")
    print(f"    discuss: {sum(1 for r in neg if r.get('review_status')=='discuss')}")
    print(f"    unreviewed: {sum(1 for r in neg if r.get('review_status','unreviewed')=='unreviewed')}")
    print(f"  Conflicts: {len(conf)}")
    print(f"    with final_labels: {sum(1 for r in conf if r.get('final_labels'))}")
    print(f"    all ok: {sum(1 for r in conf if r.get('review_status')=='agree')}")
    print(f"  Original prompt texts available: {len(prompt_texts)}")

    with MERGED.open("r", encoding="utf-8") as f:
        merged = json.load(f)
    original = copy.deepcopy(merged)
    log = []

    log.append("=" * 60)
    log.append("NEGATIVE SPAN REMOVALS")
    log.append("=" * 60)
    removed = apply_negative_reviews(merged, neg, log)

    log.append("")
    log.append("=" * 60)
    log.append("CROSS-VERSION UNIFICATION")
    log.append("=" * 60)
    applied, added, deleted, kept, skipped = apply_conflict_decisions(merged, conf, prompt_texts, log)

    rebuild_summaries(merged)

    old_kept = original["metadata"]["total_kept_spans"]
    new_kept = merged["metadata"]["total_kept_spans"]

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"  Negative spans removed: {removed}")
    print(f"  Conflict groups applied: {applied}")
    print(f"    Spans added: {added}")
    print(f"    Spans removed: {deleted}")
    print(f"    Spans unchanged: {kept}")
    print(f"    Skipped (no original text): {skipped}")
    print(f"  Total kept spans: {old_kept} → {new_kept} (delta: {new_kept - old_kept:+d})")

    print(f"\n{'='*60}")
    print(f"DETAILED LOG")
    print(f"{'='*60}")
    for line in log:
        print(line)

    if args.dry_run:
        print(f"\n[DRY RUN] No files written.")
    else:
        out_path = Path(args.output) if args.output else MERGED
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = MERGED.with_name(f"merged_all_annotations_pre_apply_{ts}.json")
        with backup.open("w", encoding="utf-8") as f:
            json.dump(original, f, indent=2, ensure_ascii=False)
        print(f"\n  Backup: {backup}")
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
        print(f"  Written: {out_path}")


if __name__ == "__main__":
    main()
