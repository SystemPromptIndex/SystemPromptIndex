#!/usr/bin/env python3
"""
Find cross-version label conflicts: same company, different prompt versions,
spans with overlapping text but different labels.

Uses simple substring containment (A in B or B in A) for speed.
"""

import json
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR.parent
MERGED = ROOT / "annotation_tool_89" / "analysis" / "merged_all_annotations.json"
OUTPUT = ROOT / "annotation_tool_89" / "analysis" / "cross_version_conflicts.json"

MIN_TEXT_LEN = 30


def main():
    with MERGED.open() as f:
        data = json.load(f)

    by_company = defaultdict(list)
    for pid, p in data["prompts"].items():
        by_company[p["company"]].append((pid, p))

    conflicts = []
    seen = set()
    pairs_checked = 0

    for comp, prompts in by_company.items():
        if len(prompts) < 2:
            continue

        for i in range(len(prompts)):
            for j in range(i + 1, len(prompts)):
                pid_a, pa = prompts[i]
                pid_b, pb = prompts[j]

                for sa in pa["kept_spans"]:
                    ta = sa["text"].strip()
                    if len(ta) < MIN_TEXT_LEN:
                        continue

                    for sb in pb["kept_spans"]:
                        tb = sb["text"].strip()
                        if len(tb) < MIN_TEXT_LEN:
                            continue

                        pairs_checked += 1

                        # Check containment in either direction
                        if ta in tb:
                            overlap = ta
                        elif tb in ta:
                            overlap = tb
                        else:
                            continue

                        same_dim = sa["dimension"] == sb["dimension"]
                        same_score = sa.get("score") == sb.get("score")

                        if same_dim and same_score:
                            continue

                        ctype = "same_dim_diff_score" if same_dim else "diff_dim"

                        dedup = tuple(sorted([pid_a, pid_b])) + (
                            overlap[:60],
                            sa["dimension"],
                            sb["dimension"],
                            str(sa["score"]),
                            str(sb["score"]),
                        )
                        if dedup in seen:
                            continue
                        seen.add(dedup)

                        conflicts.append(
                            {
                                "company": comp,
                                "overlap_text": overlap[:500],
                                "overlap_len": len(overlap),
                                "conflict_type": ctype,
                                "dimension": sa["dimension"] if same_dim else f"{sa['dimension']} vs {sb['dimension']}",
                                "prompt_a": pa["product_label"],
                                "prompt_a_id": pid_a,
                                "dim_a": sa["dimension"],
                                "score_a": sa["score"],
                                "text_a": sa["text"][:500],
                                "note_a": sa.get("note", "")[:250],
                                "prompt_b": pb["product_label"],
                                "prompt_b_id": pid_b,
                                "dim_b": sb["dimension"],
                                "score_b": sb["score"],
                                "text_b": sb["text"][:500],
                                "note_b": sb.get("note", "")[:250],
                            }
                        )

    conflicts.sort(key=lambda x: (x["conflict_type"], x["company"], -x["overlap_len"]))

    same_dim = [c for c in conflicts if c["conflict_type"] == "same_dim_diff_score"]
    diff_dim = [c for c in conflicts if c["conflict_type"] == "diff_dim"]

    print(f"Span pairs checked: {pairs_checked:,}")
    print(f"Total conflicts: {len(conflicts)}")
    print(f"  same_dim_diff_score: {len(same_dim)}")
    print(f"  diff_dim: {len(diff_dim)}")

    print(f"\n{'='*70}")
    print(f"SAME DIMENSION, DIFFERENT SCORE ({len(same_dim)})")
    print(f"{'='*70}")
    for c in same_dim:
        print(f"\n  [{c['company']}] {c['dim_a']} | score: {c['score_a']} vs {c['score_b']}")
        print(f"    A: {c['prompt_a']}")
        print(f"    B: {c['prompt_b']}")
        print(f"    Overlap ({c['overlap_len']} chars): \"{c['overlap_text'][:120]}\"")

    print(f"\n{'='*70}")
    print(f"DIFFERENT DIMENSION ({len(diff_dim)})")
    print(f"{'='*70}")
    for c in diff_dim[:30]:
        print(f"\n  [{c['company']}] {c['dim_a']}(s={c['score_a']}) vs {c['dim_b']}(s={c['score_b']})")
        print(f"    A: {c['prompt_a']}")
        print(f"    B: {c['prompt_b']}")
        print(f"    Overlap ({c['overlap_len']} chars): \"{c['overlap_text'][:120]}\"")

    with OUTPUT.open("w") as f:
        json.dump({"total": len(conflicts), "conflicts": conflicts}, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {OUTPUT}")


if __name__ == "__main__":
    main()
