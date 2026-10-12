#!/usr/bin/env python3
"""
Regenerate negative_spans_review.json from the latest merged_all_annotations.json.
Run this after apply_review_results.py to get an updated negative span list.
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
MERGED = ROOT / "annotation_tool_89" / "analysis" / "merged_all_annotations.json"
OUTPUT = ROOT / "annotation_tool_89" / "analysis" / "negative_spans_review.json"


def main():
    with MERGED.open("r", encoding="utf-8") as f:
        data = json.load(f)

    neg = []
    for pid, p in data["prompts"].items():
        for idx, s in enumerate(p["kept_spans"]):
            if s.get("score") == -1:
                neg.append({
                    "id": len(neg),
                    "prompt_id": pid,
                    "company": p.get("company", ""),
                    "product_label": p.get("product_label", ""),
                    "category": p.get("category", ""),
                    "dimension": s["dimension"],
                    "score": s["score"],
                    "source": s.get("source", ""),
                    "text": s["text"],
                    "note": s.get("note", ""),
                    "start": s.get("start", 0),
                    "end": s.get("end", 0),
                    "merged_from_count": s.get("merged_from_count", 0),
                    "span_index_in_prompt": idx,
                })

    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(neg, f, indent=2, ensure_ascii=False)

    print(f"Regenerated: {len(neg)} negative spans → {OUTPUT.name}")


if __name__ == "__main__":
    main()
