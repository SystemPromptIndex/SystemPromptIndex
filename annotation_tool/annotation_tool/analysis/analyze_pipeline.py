#!/usr/bin/env python3
"""
Annotation Analysis Pipeline
=============================
Comprehensive analysis of 88 system prompt safety annotations.
Reads merged_all_annotations.json and produces a full report.

Usage:
    python analyze_pipeline.py
    python analyze_pipeline.py --output report.txt
"""

import json
import argparse
import sys
from pathlib import Path
from collections import defaultdict, Counter
from itertools import combinations
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
FINAL_RESULT_DIR = SCRIPT_DIR.parent
MERGED_FILE = SCRIPT_DIR / "merged_all_annotations.json"

DIM_NAMES = {
    "D1": "Identity Transparency",
    "D2": "Truthfulness & Info Integrity",
    "D3": "Privacy & Data Protection",
    "D4": "Tool/Action Safety",
    "D5": "User Agency & Manipulation",
    "D6": "Unsafe Request Handling",
    "D7": "Harm Prevention & User Safety",
    "D8": "Fairness, Inclusion & Neutrality",
    "Misc": "Miscellaneous",
}
DIMS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

# Product category mapping
CATEGORY_MAP = {
    "coding_agent": [
        "Anthropic__claude-code.md", "Anthropic__Claude_Code_2.0.txt",
        "Cursor__Agent_Prompt_2.0.txt", "Cursor__Agent_Prompt_v1.0.txt",
        "Cursor__Cursor_2.0_Sys_Prompt.txt", "Cursor__20240904-Cursor.md",
        "GitHub__github_copilot_agent.md",
        "Microsoft__github_copilot_cli_20260121.md",
        "Microsoft__github_copilot_vscode_02292024.md",
        "OpenAI__codex-cli.md", "OpenSource__Prompt.txt_1",
        "Cline__system.ts", "JetBrains__Prompt.txt",
        "Replit__Prompt.txt", "Sourcegraph__claude-4-sonnet.yaml",
        "Vercel__2025-08-11-prompt.md", "Windsurf__2025-08-11-wave11-tools.md",
        "Windsurf__system-2025-04-20.md", "Google__Gemini-cli_system_prompt.md",
    ],
    "chatbot": [
        "OpenAI__chatgpt_4o_full_07292025.md", "OpenAI__chatgpt_5_08072025.md",
        "OpenAI__gpt-5-thinking.md", "OpenAI__gpt-5.2-thinking.md",
        "OpenAI__o3.md", "OpenAI__gpt40_with_canvas.md",
        "Anthropic__20240712-Claude3.5-Sonnet.md",
        "Anthropic__20250225-Claude3.7-Sonnet.md",
        "Anthropic__20250603-Claude-Sonnet4.md",
        "Anthropic__20251028-Claude-Sonnet4.5.md",
        "Anthropic__Claude_Opus_4.6.txt",
        "Google__gemini-1.5-04112024.md", "Google__gemini-3-pro.md",
        "xAI__20231214-Grok.md", "xAI__20240821-Grok2.md",
        "xAI__20251027-Grok4.md", "xAI__grok-4.2.md",
        "DeepSeek__20251029-DeepSeek-V2.md", "DeepSeek__R1.md",
        "Meta__metaai_llama3-04182024.md", "Meta__metaai_llama4-04082025.md",
        "Meta__metaai_llama4-whatsapp-07292025.md", "Meta__MetaAIHiddenPrompt.md",
        "Microsoft__microsoft_copilot_website_02252025.md",
        "Microsoft__microsoft_copilot_website_09192025.md",
        "Microsoft__microsoft_copilot_enterprise_20251202.md",
        "Microsoft__Prompt.txt",
        "Perplexity__20240320-Perplexity.md", "Perplexity__20241212-Perplexity-Pro.md",
        "Perplexity__System_Prompt.txt", "Perplexity__comet-browser-assistant.md",
        "Mistral__Le-Chat-2025-05-29.md", "Moonshot__Kimi_2_July-11-2025.txt",
        "Qwen__20251027-Qwen3-VL-235B-A22B.md",
        "Brave__20251110-leo.md", "Venice__Venice.md",
        "MiniMax__MiniMax.txt", "Hume__05052024-system-prompt.md",
        "Apple__System.txt",
        "Poke__Poke_p1.txt", "Poke__Poke_p3.txt",
        "Poke__Poke_p4.txt", "Poke__Poke_p6.txt",
        "Cluely__Cluely.mkd", "Cluely__Enterprise_Prompt.txt",
        "Sesame__Sesame-AI-Maya.md",
    ],
    "specialized_agent": [
        "OpenAI__chatgpt_agent_system_prompt.md", "OpenAI__operator.md",
        "OpenAI__Atlas_10-21-25.txt",
        "Anthropic__Prompt.txt", "Anthropic__claude-cowork.md",
        "Devin__Devin2_09-08-2025.md", "Devin__DeepWiki_Prompt.txt",
        "Google__20250804-Jules.md", "Google__20251110-notebooklm.md",
        "Google__20251118-Antigravity.md", "Google__gemini-workspace.md",
        "Google__gemini_in_chrome.md",
        "Manus__Manus_Prompt.txt", "Notion__Prompt.txt",
        "Perplexity__Perplexity_Deep_Research.txt",
        "Poke__Poke_agent.txt",
        "Lovable__Prompt.md", "Warp__Prompt.txt",
        "ByteDance__Builder_Prompt.txt",
        "OpenSource_Bolt__Prompt.txt",
        "xAI__grok.com-post-new-safety-instructions.md",
        "xAI__grok3_official0330_p1.j2",
        "Amazon__Spec_Prompt.txt",
    ],
}


def load_data():
    with MERGED_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_kept_spans(prompt_data):
    return prompt_data.get("kept_spans", [])


def get_category(pid):
    for cat, pids in CATEGORY_MAP.items():
        if pid in pids:
            return cat
    return "other"


# ═══════════════════════════════════════════════════════════════════════
# SECTION 1: Company Safety Ranking
# ═══════════════════════════════════════════════════════════════════════
def section_company_ranking(data, out):
    out.append("=" * 90)
    out.append("SECTION 1: COMPANY SAFETY RANKING")
    out.append("=" * 90)
    out.append("")
    out.append("Ranked by negative span rate (-1 as % of all kept spans).")
    out.append("Lower -1 rate = safer system prompt practices.\n")

    company_stats = defaultdict(lambda: {"prompts": 0, "kept": 0, "pos": 0, "neg": 0, "rejected": 0})
    for pid, pdata in data["prompts"].items():
        c = pdata["company"]
        company_stats[c]["prompts"] += 1
        company_stats[c]["rejected"] += pdata["rejected_count"]
        for s in get_kept_spans(pdata):
            company_stats[c]["kept"] += 1
            if s.get("score", 0) > 0:
                company_stats[c]["pos"] += 1
            elif s.get("score", 0) < 0:
                company_stats[c]["neg"] += 1

    ranked = sorted(company_stats.items(), key=lambda x: x[1]["neg"] / max(x[1]["pos"] + x[1]["neg"], 1))

    out.append(f"  {'Company':20s}  {'Prompts':>7s}  {'Kept':>5s}  {'Rej':>4s}  {'+1':>5s}  {'-1':>4s}  {'-1 Rate':>8s}")
    out.append(f"  {'-'*20}  {'-'*7}  {'-'*5}  {'-'*4}  {'-'*5}  {'-'*4}  {'-'*8}")
    for c, s in ranked:
        total = s["pos"] + s["neg"]
        neg_rate = s["neg"] / total * 100 if total > 0 else 0
        out.append(f"  {c:20s}  {s['prompts']:7d}  {s['kept']:5d}  {s['rejected']:4d}  {s['pos']:5d}  {s['neg']:4d}  {neg_rate:7.1f}%")
    out.append("")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 2: Company × Dimension Heatmap
# ═══════════════════════════════════════════════════════════════════════
def section_company_dimension_heatmap(data, out):
    out.append("=" * 90)
    out.append("SECTION 2: COMPANY × DIMENSION HEATMAP (negative rate %)")
    out.append("=" * 90)
    out.append("")
    out.append("Each cell = -1 / (+1 + -1) × 100 for that company-dimension pair.")
    out.append("Higher = more safety concerns in that dimension. '-' = no spans.\n")

    cd = defaultdict(lambda: defaultdict(lambda: {"pos": 0, "neg": 0}))
    for pid, pdata in data["prompts"].items():
        c = pdata["company"]
        for s in get_kept_spans(pdata):
            dim = s.get("dimension", "?")
            if s.get("score", 0) > 0:
                cd[c][dim]["pos"] += 1
            elif s.get("score", 0) < 0:
                cd[c][dim]["neg"] += 1

    companies = sorted(cd.keys())
    header = f"  {'Company':20s}"
    for d in DIMS:
        header += f"  {d:>6s}"
    out.append(header)
    out.append(f"  {'-'*20}" + f"  {'-'*6}" * len(DIMS))

    for c in companies:
        row = f"  {c:20s}"
        for d in DIMS:
            p = cd[c][d]["pos"]
            n = cd[c][d]["neg"]
            t = p + n
            if t > 0:
                rate = n / t * 100
                row += f"  {rate:5.0f}%"
            else:
                row += f"      -"
        out.append(row)
    out.append("")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 3: Same-Company Version Evolution
# ═══════════════════════════════════════════════════════════════════════
def section_version_evolution(data, out):
    out.append("=" * 90)
    out.append("SECTION 3: SAME-COMPANY VERSION EVOLUTION")
    out.append("=" * 90)
    out.append("")
    out.append("For companies with multiple prompt versions, how does safety change over time?\n")

    company_prompts = defaultdict(list)
    for pid, pdata in data["prompts"].items():
        c = pdata["company"]
        spans = get_kept_spans(pdata)
        pos = sum(1 for s in spans if s.get("score", 0) > 0)
        neg = sum(1 for s in spans if s.get("score", 0) < 0)
        total = pos + neg
        neg_rate = neg / total * 100 if total > 0 else 0

        dim_neg_rates = {}
        for d in DIMS:
            dp = sum(1 for s in spans if s.get("dimension") == d and s.get("score", 0) > 0)
            dn = sum(1 for s in spans if s.get("dimension") == d and s.get("score", 0) < 0)
            dt = dp + dn
            dim_neg_rates[d] = dn / dt * 100 if dt > 0 else None

        company_prompts[c].append({
            "pid": pid,
            "label": pdata.get("product_label", pdata.get("product", "")),
            "date": pdata.get("date", ""),
            "total": total,
            "pos": pos,
            "neg": neg,
            "neg_rate": neg_rate,
            "dim_neg_rates": dim_neg_rates,
        })

    for c in sorted(company_prompts.keys()):
        prompts = company_prompts[c]
        if len(prompts) < 2:
            continue
        prompts.sort(key=lambda x: x["date"] or "")
        out.append(f"  {c} ({len(prompts)} versions):")
        for p in prompts:
            out.append(f"    {p['label']:50s}  spans:{p['total']:4d}  +1:{p['pos']:4d}  -1:{p['neg']:3d}  ({p['neg_rate']:.1f}% neg)")
        out.append("")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 4: Product Category Comparison
# ═══════════════════════════════════════════════════════════════════════
def section_category_comparison(data, out):
    out.append("=" * 90)
    out.append("SECTION 4: PRODUCT CATEGORY COMPARISON")
    out.append("=" * 90)
    out.append("")
    out.append("Categories: coding_agent, chatbot, specialized_agent\n")

    cat_stats = defaultdict(lambda: {"prompts": 0, "pos": 0, "neg": 0, "dim": defaultdict(lambda: {"pos": 0, "neg": 0})})
    for pid, pdata in data["prompts"].items():
        cat = get_category(pid)
        cat_stats[cat]["prompts"] += 1
        for s in get_kept_spans(pdata):
            dim = s.get("dimension", "?")
            score = s.get("score", 0)
            if score > 0:
                cat_stats[cat]["pos"] += 1
                cat_stats[cat]["dim"][dim]["pos"] += 1
            elif score < 0:
                cat_stats[cat]["neg"] += 1
                cat_stats[cat]["dim"][dim]["neg"] += 1

    out.append(f"  {'Category':22s}  {'Prompts':>7s}  {'+1':>5s}  {'-1':>4s}  {'-1 Rate':>8s}")
    out.append(f"  {'-'*22}  {'-'*7}  {'-'*5}  {'-'*4}  {'-'*8}")
    for cat in ["coding_agent", "chatbot", "specialized_agent", "other"]:
        s = cat_stats.get(cat)
        if not s:
            continue
        t = s["pos"] + s["neg"]
        neg_rate = s["neg"] / t * 100 if t > 0 else 0
        out.append(f"  {cat:22s}  {s['prompts']:7d}  {s['pos']:5d}  {s['neg']:4d}  {neg_rate:7.1f}%")

    out.append("")
    out.append("  Per-dimension breakdown (-1 rate):\n")
    header = f"  {'Category':22s}"
    for d in DIMS:
        header += f"  {d:>6s}"
    out.append(header)
    out.append(f"  {'-'*22}" + f"  {'-'*6}" * len(DIMS))
    for cat in ["coding_agent", "chatbot", "specialized_agent", "other"]:
        s = cat_stats.get(cat)
        if not s:
            continue
        row = f"  {cat:22s}"
        for d in DIMS:
            p = s["dim"][d]["pos"]
            n = s["dim"][d]["neg"]
            t = p + n
            if t > 0:
                row += f"  {n / t * 100:5.1f}%"
            else:
                row += f"      -"
        out.append(row)
    out.append("")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 5: Dimension-Level +1/-1 Analysis
# ═══════════════════════════════════════════════════════════════════════
def section_dimension_analysis(data, out):
    out.append("=" * 90)
    out.append("SECTION 5: DIMENSION-LEVEL ANALYSIS")
    out.append("=" * 90)
    out.append("")

    dim_stats = defaultdict(lambda: {"pos": 0, "neg": 0, "total_prompts": set()})
    for pid, pdata in data["prompts"].items():
        for s in get_kept_spans(pdata):
            dim = s.get("dimension", "?")
            dim_stats[dim]["total_prompts"].add(pid)
            if s.get("score", 0) > 0:
                dim_stats[dim]["pos"] += 1
            elif s.get("score", 0) < 0:
                dim_stats[dim]["neg"] += 1

    out.append(f"  {'Dimension':6s} {'Name':38s}  {'+1':>5s}  {'-1':>4s}  {'Total':>5s}  {'-1%':>5s}  {'Prompts':>7s}")
    out.append(f"  {'-'*6} {'-'*38}  {'-'*5}  {'-'*4}  {'-'*5}  {'-'*5}  {'-'*7}")
    for d in DIMS + ["Misc"]:
        s = dim_stats.get(d)
        if not s:
            continue
        t = s["pos"] + s["neg"]
        neg_rate = s["neg"] / t * 100 if t > 0 else 0
        out.append(f"  {d:6s} {DIM_NAMES.get(d, ''):38s}  {s['pos']:5d}  {s['neg']:4d}  {t:5d}  {neg_rate:4.1f}%  {len(s['total_prompts']):7d}")
    out.append("")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 6: Dimension Co-occurrence
# ═══════════════════════════════════════════════════════════════════════
def section_dimension_cooccurrence(data, out):
    out.append("=" * 90)
    out.append("SECTION 6: DIMENSION CO-OCCURRENCE")
    out.append("=" * 90)
    out.append("")
    out.append("How often do two dimensions annotate the exact same text span?")
    out.append("(Same start+end position, different dimension)\n")

    cooccur = Counter()
    for pid, pdata in data["prompts"].items():
        spans = get_kept_spans(pdata)
        pos_dims = defaultdict(set)
        for s in spans:
            key = (s["start"], s["end"])
            pos_dims[key].add(s.get("dimension", "?"))

        for key, dims_set in pos_dims.items():
            dims_list = sorted(dims_set)
            for a, b in combinations(dims_list, 2):
                cooccur[(a, b)] += 1

    out.append(f"  {'Pair':12s}  {'Count':>6s}  Interpretation")
    out.append(f"  {'-'*12}  {'-'*6}  {'-'*50}")
    for (a, b), count in cooccur.most_common(20):
        out.append(f"  {a}+{b:5s}     {count:6d}  {DIM_NAMES.get(a,'')} & {DIM_NAMES.get(b,'')}")
    out.append("")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 7: Negative Span Pattern Analysis
# ═══════════════════════════════════════════════════════════════════════
def section_negative_patterns(data, out):
    out.append("=" * 90)
    out.append("SECTION 7: NEGATIVE SPAN PATTERNS (score = -1)")
    out.append("=" * 90)
    out.append("")
    out.append("Most common negative spans and their themes.\n")

    neg_by_dim = defaultdict(list)
    for pid, pdata in data["prompts"].items():
        for s in get_kept_spans(pdata):
            if s.get("score", 0) < 0:
                neg_by_dim[s.get("dimension", "?")].append({
                    "company": pdata["company"],
                    "product": pdata.get("product_label", ""),
                    "text": s.get("text", "")[:150],
                    "note": s.get("note", "")[:200],
                })

    for d in DIMS:
        items = neg_by_dim.get(d, [])
        if not items:
            continue
        out.append(f"  {d} {DIM_NAMES.get(d, '')} — {len(items)} negative spans:")
        companies = Counter(i["company"] for i in items)
        out.append(f"    Companies: {', '.join(f'{c}({n})' for c, n in companies.most_common(10))}")
        out.append(f"    Sample spans:")
        for item in items[:3]:
            out.append(f"      [{item['company']}] \"{item['text']}\"")
        out.append("")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 8: LLM Pre-annotation Quality (Reject Analysis)
# ═══════════════════════════════════════════════════════════════════════
def section_reject_analysis(data, out):
    out.append("=" * 90)
    out.append("SECTION 8: LLM PRE-ANNOTATION QUALITY (reject analysis)")
    out.append("=" * 90)
    out.append("")

    total_kept = data["metadata"]["total_kept_spans"]
    total_rej = data["metadata"]["total_rejected"]
    total_human = data["metadata"]["total_human_added"]
    total_llm = total_kept - total_human + total_rej

    out.append(f"  Total LLM-generated spans: {total_llm}")
    out.append(f"    Accepted: {total_kept - total_human} ({(total_kept - total_human) / total_llm * 100:.1f}%)")
    out.append(f"    Rejected: {total_rej} ({total_rej / total_llm * 100:.1f}%)")
    out.append(f"  Human-added spans: {total_human}")
    out.append(f"    → LLM missed {total_human} spans that humans added\n")

    # Per-reviewer reject rate
    reviewer_stats = defaultdict(lambda: {"accepted": 0, "rejected": 0, "prompts": 0})
    for pid, pdata in data["prompts"].items():
        r = pdata["reviewer"]
        reviewer_stats[r]["prompts"] += 1
        reviewer_stats[r]["rejected"] += pdata["rejected_count"]
        reviewer_stats[r]["accepted"] += pdata["kept_count"] - pdata["human_added_count"]

    out.append(f"  Per-reviewer reject rate:")
    out.append(f"  {'Reviewer':20s}  {'Prompts':>7s}  {'Accepted':>8s}  {'Rejected':>8s}  {'Rej Rate':>8s}")
    out.append(f"  {'-'*20}  {'-'*7}  {'-'*8}  {'-'*8}  {'-'*8}")
    for r in sorted(reviewer_stats.keys()):
        s = reviewer_stats[r]
        t = s["accepted"] + s["rejected"]
        rate = s["rejected"] / t * 100 if t > 0 else 0
        out.append(f"  {r:20s}  {s['prompts']:7d}  {s['accepted']:8d}  {s['rejected']:8d}  {rate:7.1f}%")
    out.append("")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 9: Human-Added Span Analysis
# ═══════════════════════════════════════════════════════════════════════
def section_human_added(data, out):
    out.append("=" * 90)
    out.append("SECTION 9: HUMAN-ADDED SPANS ANALYSIS")
    out.append("=" * 90)
    out.append("")
    out.append("Spans added by human annotators that LLM missed.\n")

    human_spans = []
    for pid, pdata in data["prompts"].items():
        for s in get_kept_spans(pdata):
            if s.get("source") == "human":
                human_spans.append({
                    "company": pdata["company"],
                    "product": pdata.get("product_label", ""),
                    "reviewer": pdata["reviewer"],
                    "dim": s.get("dimension", "?"),
                    "score": s.get("score", 0),
                    "text": s.get("text", "")[:150],
                })

    out.append(f"  Total human-added spans: {len(human_spans)}\n")

    dim_counts = Counter(s["dim"] for s in human_spans)
    out.append(f"  By dimension:")
    for d in DIMS + ["Misc"]:
        if dim_counts.get(d, 0) > 0:
            out.append(f"    {d} {DIM_NAMES.get(d, ''):38s}: {dim_counts[d]}")

    score_counts = Counter("positive (+1)" if s["score"] > 0 else "negative (-1)" for s in human_spans)
    out.append(f"\n  By score polarity:")
    for k, v in score_counts.most_common():
        out.append(f"    {k}: {v}")

    reviewer_counts = Counter(s["reviewer"] for s in human_spans)
    out.append(f"\n  By reviewer:")
    for r, v in reviewer_counts.most_common():
        out.append(f"    {r}: {v}")

    out.append(f"\n  Sample human-added spans:")
    for s in human_spans[:10]:
        out.append(f"    [{s['company']}] {s['dim']} score={s['score']}: \"{s['text']}\"")
    out.append("")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 10: Per-Product Safety Scorecard
# ═══════════════════════════════════════════════════════════════════════
def section_product_scorecard(data, out):
    out.append("=" * 90)
    out.append("SECTION 10: PER-PRODUCT SAFETY SCORECARD")
    out.append("=" * 90)
    out.append("")
    out.append("For each product: score per dimension = (positive - negative) / total.")
    out.append("Range: -1.0 (all negative) to +1.0 (all positive). '-' = no spans.\n")

    products = []
    for pid, pdata in data["prompts"].items():
        spans = get_kept_spans(pdata)
        dim_scores = {}
        total_pos = 0
        total_neg = 0
        for d in DIMS:
            p = sum(1 for s in spans if s.get("dimension") == d and s.get("score", 0) > 0)
            n = sum(1 for s in spans if s.get("dimension") == d and s.get("score", 0) < 0)
            t = p + n
            total_pos += p
            total_neg += n
            dim_scores[d] = (p - n) / t if t > 0 else None

        total = total_pos + total_neg
        overall = (total_pos - total_neg) / total if total > 0 else None
        products.append({
            "label": pdata.get("product_label", pdata.get("product", pid))[:40],
            "company": pdata["company"],
            "dim_scores": dim_scores,
            "overall": overall,
            "total": total,
        })

    products.sort(key=lambda x: x["overall"] if x["overall"] is not None else 0)

    header = f"  {'Product':42s}  {'Company':14s}  {'Overall':>7s}"
    for d in DIMS:
        header += f"  {d:>5s}"
    out.append(header)
    out.append(f"  {'-'*42}  {'-'*14}  {'-'*7}" + f"  {'-'*5}" * len(DIMS))

    for p in products:
        row = f"  {p['label']:42s}  {p['company']:14s}  {p['overall']:+6.2f}" if p["overall"] is not None else f"  {p['label']:42s}  {p['company']:14s}     n/a"
        for d in DIMS:
            v = p["dim_scores"].get(d)
            if v is not None:
                row += f"  {v:+4.1f}"
            else:
                row += f"     -"
        out.append(row)
    out.append("")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 11: Prompt Size vs Safety Coverage
# ═══════════════════════════════════════════════════════════════════════
def section_size_vs_safety(data, out):
    out.append("=" * 90)
    out.append("SECTION 11: PROMPT SIZE vs SAFETY COVERAGE")
    out.append("=" * 90)
    out.append("")
    out.append("Do longer prompts have more safety-related content?\n")

    buckets = {"tiny (<2KB)": [], "small (2-5KB)": [], "medium (5-15KB)": [],
               "large (15-30KB)": [], "huge (>30KB)": []}

    for pid, pdata in data["prompts"].items():
        size = pdata.get("size_bytes", 0)
        spans = get_kept_spans(pdata)
        total = len(spans)
        pos = sum(1 for s in spans if s.get("score", 0) > 0)
        neg = sum(1 for s in spans if s.get("score", 0) < 0)
        entry = {"pid": pid, "size": size, "total": total, "pos": pos, "neg": neg}

        if size < 2000:
            buckets["tiny (<2KB)"].append(entry)
        elif size < 5000:
            buckets["small (2-5KB)"].append(entry)
        elif size < 15000:
            buckets["medium (5-15KB)"].append(entry)
        elif size < 30000:
            buckets["large (15-30KB)"].append(entry)
        else:
            buckets["huge (>30KB)"].append(entry)

    out.append(f"  {'Size Bucket':20s}  {'Prompts':>7s}  {'Avg Spans':>9s}  {'Avg +1':>7s}  {'Avg -1':>7s}  {'Avg -1%':>7s}")
    out.append(f"  {'-'*20}  {'-'*7}  {'-'*9}  {'-'*7}  {'-'*7}  {'-'*7}")
    for bucket_name in ["tiny (<2KB)", "small (2-5KB)", "medium (5-15KB)", "large (15-30KB)", "huge (>30KB)"]:
        entries = buckets[bucket_name]
        if not entries:
            continue
        n = len(entries)
        avg_total = sum(e["total"] for e in entries) / n
        avg_pos = sum(e["pos"] for e in entries) / n
        avg_neg = sum(e["neg"] for e in entries) / n
        avg_neg_rate = sum(e["neg"] / max(e["pos"] + e["neg"], 1) * 100 for e in entries) / n
        out.append(f"  {bucket_name:20s}  {n:7d}  {avg_total:9.1f}  {avg_pos:7.1f}  {avg_neg:7.1f}  {avg_neg_rate:6.1f}%")
    out.append("")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 12: High-Frequency Safety Instructions
# ═══════════════════════════════════════════════════════════════════════
def section_frequent_instructions(data, out):
    out.append("=" * 90)
    out.append("SECTION 12: HIGH-FREQUENCY SAFETY PATTERNS")
    out.append("=" * 90)
    out.append("")
    out.append("Common keywords/phrases in positive (+1) and negative (-1) spans.\n")

    pos_keywords = Counter()
    neg_keywords = Counter()

    patterns = [
        "refuse", "reject", "deny", "harmful", "safety", "unsafe", "dangerous",
        "privacy", "sensitive", "personal", "pii", "consent",
        "fabricat", "hallucin", "make up", "invent", "lie",
        "manipulat", "deceiv", "mislead", "dark pattern",
        "bias", "discriminat", "stereotype", "fair",
        "copyright", "intellectual property",
        "human", "ai", "assistant", "artificial",
        "tool", "execute", "permission", "sandbox",
        "cutoff", "knowledge", "uncertain", "don't know",
        "medical", "legal", "financial", "advice",
        "suicide", "self-harm", "violence", "weapon",
        "jailbreak", "prompt injection", "roleplay",
        "never", "must not", "do not", "always",
        "user consent", "user control", "autonomy",
        "woke", "political", "neutral", "balanced",
    ]

    for pid, pdata in data["prompts"].items():
        for s in get_kept_spans(pdata):
            text = (s.get("text", "") + " " + s.get("note", "")).lower()
            score = s.get("score", 0)
            for p in patterns:
                if p in text:
                    if score > 0:
                        pos_keywords[p] += 1
                    elif score < 0:
                        neg_keywords[p] += 1

    out.append("  Top keywords in POSITIVE (+1) spans:")
    for kw, count in pos_keywords.most_common(20):
        out.append(f"    {kw:25s}: {count}")

    out.append(f"\n  Top keywords in NEGATIVE (-1) spans:")
    for kw, count in neg_keywords.most_common(20):
        out.append(f"    {kw:25s}: {count}")
    out.append("")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="Annotation analysis pipeline")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output file path")
    args = parser.parse_args()

    data = load_data()

    out = []
    out.append("╔" + "═" * 88 + "╗")
    out.append("║" + "SYSTEM PROMPT SAFETY ANNOTATION — ANALYSIS REPORT".center(88) + "║")
    out.append("╚" + "═" * 88 + "╝")
    out.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    out.append(f"  Data: {MERGED_FILE.name}")
    out.append(f"  Prompts: {data['metadata']['total_prompts']}  |  "
               f"Kept spans: {data['metadata']['total_kept_spans']}  |  "
               f"Rejected: {data['metadata']['total_rejected']}  |  "
               f"Human-added: {data['metadata']['total_human_added']}")
    out.append(f"  Annotators: {', '.join(data['metadata']['annotators'])}")
    out.append("")

    section_company_ranking(data, out)
    section_company_dimension_heatmap(data, out)
    section_version_evolution(data, out)
    section_category_comparison(data, out)
    section_dimension_analysis(data, out)
    section_dimension_cooccurrence(data, out)
    section_negative_patterns(data, out)
    section_reject_analysis(data, out)
    section_human_added(data, out)
    section_product_scorecard(data, out)
    section_size_vs_safety(data, out)
    section_frequent_instructions(data, out)

    report = "\n".join(out)

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = SCRIPT_DIR / "analysis_report.txt"

    with out_path.open("w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print(f"\n\n{'='*60}")
    print(f"Report saved to: {out_path}")


if __name__ == "__main__":
    main()
