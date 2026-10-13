#!/usr/bin/env python3
"""
Compare Opus vs Gemini Pre-Annotation on Anthropic Prompts
============================================================
For each of the 9 Anthropic prompts pre-annotated by both models, pair spans
within the same dimension by character-interval IoU (Jaccard) ≥ threshold,
then report:

  • Per-dimension agreement counts and score consistency
  • Per-prompt summary
  • Full JSON of agree / Opus-only / Gemini-only spans

Pairing is greedy-best-match: all (Opus, Gemini) pairs in the same dimension
are ranked by IoU descending, and each span is consumed at most once.

Usage:
  python compare_opus_gemini_anthropic.py
  python compare_opus_gemini_anthropic.py --iou 0.3
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

OPUS_DIR = Path(__file__).parent.parent / "data" / "preannotation"
GEMINI_DIR = Path(__file__).parent.parent / "data" / "gemini_preannotation_anthropic"
OUTPUT_JSON = Path(__file__).parent.parent / "data" / "opus_vs_gemini_anthropic.json"
OUTPUT_TXT = Path(__file__).parent.parent / "data" / "opus_vs_gemini_anthropic_report.txt"

ANTHROPIC_FILENAMES = [
    "20240712-Claude3.5-Sonnet.md",
    "20250225-Claude3.7-Sonnet.md",
    "20250603-Claude-Sonnet4.md",
    "20251028-Claude-Sonnet4.5.md",
    "Claude Code 2.0.txt",
    "Claude_Opus_4.6.txt",
    "Prompt.txt",
    "claude-code.md",
    "claude-cowork.md",
]

DIMS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]


def iou(a_start, a_end, b_start, b_end):
    inter = max(0, min(a_end, b_end) - max(a_start, b_start))
    if inter == 0:
        return 0.0
    union = (a_end - a_start) + (b_end - b_start) - inter
    return inter / max(union, 1)


def load_by_filename(directory: Path) -> dict:
    """Index pre-annotation JSONs by the filename stored inside metadata."""
    out = {}
    for p in directory.glob("*.json"):
        if p.name == "batch_summary.json":
            continue
        try:
            j = json.load(p.open("r", encoding="utf-8"))
        except Exception:
            continue
        fn = j.get("metadata", {}).get("prompt", {}).get("filename")
        if fn:
            out[fn] = j
    return out


def pair_spans(opus_spans: list, gem_spans: list, threshold: float):
    """Greedy-best-match pair (o_idx, g_idx, iou) within one dimension."""
    candidates = []
    for i, o in enumerate(opus_spans):
        for j, g in enumerate(gem_spans):
            score = iou(o["start"], o["end"], g["start"], g["end"])
            if score >= threshold:
                candidates.append((score, i, j))
    candidates.sort(reverse=True)

    used_o, used_g = set(), set()
    pairs = []
    for score, i, j in candidates:
        if i in used_o or j in used_g:
            continue
        used_o.add(i)
        used_g.add(j)
        pairs.append((i, j, score))

    unmatched_o = [i for i in range(len(opus_spans)) if i not in used_o]
    unmatched_g = [j for j in range(len(gem_spans)) if j not in used_g]
    return pairs, unmatched_o, unmatched_g


def compare_prompt(opus: dict, gem: dict, threshold: float):
    """Compare one prompt's pre-annotation. Returns per-dim results + summary."""
    per_dim = {}
    for dim in DIMS:
        o_spans = opus.get("dimensions", {}).get(dim, {}).get("spans", [])
        g_spans = gem.get("dimensions", {}).get(dim, {}).get("spans", [])

        pairs, unmatched_o, unmatched_g = pair_spans(o_spans, g_spans, threshold)

        agree = []
        score_agree = 0
        score_disagree = 0
        for i, j, score in pairs:
            o_score = o_spans[i].get("score")
            g_score = g_spans[j].get("score")
            if o_score == g_score:
                score_agree += 1
            else:
                score_disagree += 1
            agree.append({
                "iou": round(score, 3),
                "opus": {k: o_spans[i].get(k) for k in ("start", "end", "text", "score", "note")},
                "gemini": {k: g_spans[j].get(k) for k in ("start", "end", "text", "score", "note")},
                "score_match": o_score == g_score,
            })

        opus_only = [o_spans[i] for i in unmatched_o]
        gemini_only = [g_spans[j] for j in unmatched_g]

        per_dim[dim] = {
            "opus_count": len(o_spans),
            "gemini_count": len(g_spans),
            "agree_count": len(pairs),
            "opus_only_count": len(unmatched_o),
            "gemini_only_count": len(unmatched_g),
            "score_agree": score_agree,
            "score_disagree": score_disagree,
            "agree": agree,
            "opus_only": opus_only,
            "gemini_only": gemini_only,
        }
    return per_dim


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iou", type=float, default=0.3,
                        help="IoU threshold for pairing (default 0.3)")
    args = parser.parse_args()

    opus_by_fn = load_by_filename(OPUS_DIR)
    gem_by_fn = load_by_filename(GEMINI_DIR)

    all_results = {}
    for fn in ANTHROPIC_FILENAMES:
        if fn not in opus_by_fn or fn not in gem_by_fn:
            print(f"[skip] {fn}  (opus={fn in opus_by_fn}, gemini={fn in gem_by_fn})")
            continue
        all_results[fn] = compare_prompt(opus_by_fn[fn], gem_by_fn[fn], args.iou)

    # ─── Aggregate ────────────────────────────────────────────────────────────
    dim_agg = {d: Counter() for d in DIMS}
    for fn, per_dim in all_results.items():
        for dim, r in per_dim.items():
            for k in ("opus_count", "gemini_count", "agree_count",
                      "opus_only_count", "gemini_only_count",
                      "score_agree", "score_disagree"):
                dim_agg[dim][k] += r[k]

    # Precision = agree / gemini_total, Recall = agree / opus_total (Opus as reference)
    lines = []
    lines.append(f"Opus vs Gemini 3.1 Pro — Anthropic prompts (IoU ≥ {args.iou})")
    lines.append("=" * 78)
    lines.append(f"Prompts compared: {len(all_results)} / 9")
    lines.append("")
    lines.append("Per-Dimension Agreement (Opus reference)")
    lines.append("-" * 78)
    lines.append(f"{'Dim':<4}{'Opus':>6}{'Gem':>6}{'Agree':>7}{'O-only':>8}{'G-only':>8}"
                 f"{'Prec':>8}{'Rec':>8}{'F1':>8}{'ScoreOK':>9}")
    totals = Counter()
    for dim in DIMS:
        c = dim_agg[dim]
        o, g, a = c["opus_count"], c["gemini_count"], c["agree_count"]
        oo, go = c["opus_only_count"], c["gemini_only_count"]
        sa, sd = c["score_agree"], c["score_disagree"]
        prec = a / g if g else 0.0
        rec = a / o if o else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        score_rate = sa / a if a else 0.0
        lines.append(f"{dim:<4}{o:>6}{g:>6}{a:>7}{oo:>8}{go:>8}"
                     f"{prec:>7.1%}{rec:>7.1%}{f1:>7.1%}{score_rate:>8.1%}")
        for k, v in c.items():
            totals[k] += v
    lines.append("-" * 78)
    o, g, a = totals["opus_count"], totals["gemini_count"], totals["agree_count"]
    oo, go = totals["opus_only_count"], totals["gemini_only_count"]
    sa, sd = totals["score_agree"], totals["score_disagree"]
    prec = a / g if g else 0.0
    rec = a / o if o else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    score_rate = sa / a if a else 0.0
    lines.append(f"{'ALL':<4}{o:>6}{g:>6}{a:>7}{oo:>8}{go:>8}"
                 f"{prec:>7.1%}{rec:>7.1%}{f1:>7.1%}{score_rate:>8.1%}")
    lines.append("")
    lines.append("Legend:")
    lines.append("  Opus/Gem    = spans each model produced for that dim")
    lines.append("  Agree       = pairs with IoU ≥ threshold & same dim")
    lines.append("  O-only      = Opus spans with no Gemini match (Opus-flagged, Gemini-missed)")
    lines.append("  G-only      = Gemini spans with no Opus match (Gemini-flagged, Opus-missed)")
    lines.append("  Prec/Rec/F1 = treating Opus as ground truth")
    lines.append("  ScoreOK     = among paired spans, fraction where +/- score matches")
    lines.append("")

    # Per-prompt breakdown
    lines.append("Per-Prompt Summary")
    lines.append("-" * 78)
    lines.append(f"{'prompt':<40}{'Opus':>6}{'Gem':>6}{'Agree':>7}{'O-only':>8}{'G-only':>8}{'ScoreOK':>9}")
    for fn, per_dim in all_results.items():
        opus_n = sum(r["opus_count"] for r in per_dim.values())
        gem_n = sum(r["gemini_count"] for r in per_dim.values())
        agree_n = sum(r["agree_count"] for r in per_dim.values())
        oo_n = sum(r["opus_only_count"] for r in per_dim.values())
        go_n = sum(r["gemini_only_count"] for r in per_dim.values())
        sa_n = sum(r["score_agree"] for r in per_dim.values())
        score_rate = sa_n / agree_n if agree_n else 0.0
        lines.append(f"{fn[:40]:<40}{opus_n:>6}{gem_n:>6}{agree_n:>7}{oo_n:>8}{go_n:>8}{score_rate:>8.1%}")

    report = "\n".join(lines)
    print(report)
    OUTPUT_TXT.write_text(report, encoding="utf-8")
    print(f"\n[wrote] {OUTPUT_TXT}")

    # Full JSON dump
    payload = {
        "meta": {
            "iou_threshold": args.iou,
            "prompts": list(all_results.keys()),
        },
        "aggregate": {dim: dict(dim_agg[dim]) for dim in DIMS},
        "by_prompt": all_results,
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"[wrote] {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
