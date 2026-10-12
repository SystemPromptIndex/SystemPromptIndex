#!/usr/bin/env python3
"""
Generate analysis plots from merged annotation data.

Usage:
    python generate_plots.py
"""

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
MERGED_FILE = SCRIPT_DIR / "merged_all_annotations.json"
PLOT_DIR = SCRIPT_DIR / "plots"
PLOT_DIR.mkdir(exist_ok=True)

DIM_NAMES = {
    "D1": "Identity\nTransparency",
    "D2": "Truthfulness &\nInfo Integrity",
    "D3": "Privacy &\nData Protection",
    "D4": "Tool/Action\nSafety",
    "D5": "User Agency &\nManipulation",
    "D6": "Unsafe Request\nHandling",
    "D7": "Harm Prevention\n& User Safety",
    "D8": "Fairness &\nNeutrality",
}
DIM_SHORT = {
    "D1": "D1 Identity", "D2": "D2 Truthfulness", "D3": "D3 Privacy",
    "D4": "D4 Tool Safety", "D5": "D5 User Agency", "D6": "D6 Unsafe Req",
    "D7": "D7 Harm Prev", "D8": "D8 Fairness",
}
DIMS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

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

sns.set_theme(style="whitegrid", font_scale=1.1)

# Unified yellow->green gradient palette
M_LIGHT = "#FFFDF8"
M_YELLOW = "#F8EFA6"
M_YELLOW_DEEP = "#EFD96D"
M_GREEN = "#A8D8A8"
M_GREEN_DEEP = "#6FBF73"
M_OLIVE = "#8FAF63"
M_BEIGE = "#F9F2E8"
M_DARK = "#5B6A52"

PALETTE_POS_NEG = [M_GREEN_DEEP, M_YELLOW_DEEP]
PALETTE_CATS = [M_GREEN, M_YELLOW_DEEP, M_GREEN_DEEP, M_OLIVE]

CMAP_POS = LinearSegmentedColormap.from_list("yg_pos", [M_LIGHT, M_YELLOW, M_GREEN])
CMAP_NEG = LinearSegmentedColormap.from_list("yg_neg", [M_LIGHT, M_YELLOW_DEEP, M_OLIVE])
CMAP_NEUTRAL = LinearSegmentedColormap.from_list("yg_neutral", [M_LIGHT, M_YELLOW, M_GREEN_DEEP])
# Translucent yellow -> green -> blue for better separation while keeping a light feel.
CMAP_YGB = LinearSegmentedColormap.from_list(
    "ygb_soft",
    ["#E7C547", "#72B36B", "#4F8EDC"],
)


def load_data():
    with MERGED_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_prompt_date(date_str):
    """Parse mixed compact and standard date formats to datetime."""
    s = (date_str or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    if len(s) == 8 and s.isdigit():
        try:
            if s.startswith("20"):
                return datetime.strptime(s, "%Y%m%d")
            return datetime.strptime(s, "%m%d%Y")
        except ValueError:
            return None
    return None


def get_category(pid):
    for cat, pids in CATEGORY_MAP.items():
        if pid in pids:
            return cat
    return "other"


# ═══════════════════════════════════════════════════════════════════════
# Plot 1: Company Safety Ranking (horizontal bar)
# ═══════════════════════════════════════════════════════════════════════
def plot_company_ranking(data):
    rows = []
    for pid, pdata in data["prompts"].items():
        c = pdata["company"]
        for s in pdata.get("kept_spans", []):
            rows.append({"company": c, "score": s.get("score", 0)})
    df = pd.DataFrame(rows)

    company_stats = df.groupby("company")["score"].agg(
        total="count",
        pos=lambda x: (x > 0).sum(),
        neg=lambda x: (x < 0).sum(),
    ).reset_index()
    company_stats["pos_rate"] = company_stats["pos"] / company_stats["total"] * 100
    company_stats["neg_rate"] = company_stats["neg"] / company_stats["total"] * 100
    company_stats["balance"] = (company_stats["pos"] - company_stats["neg"]) / company_stats["total"] * 100
    company_stats = company_stats.sort_values("balance", ascending=True)

    fig, ax = plt.subplots(figsize=(11, 12))
    y = np.arange(len(company_stats))

    # Diverging bars: positive to right, negative to left
    ax.barh(y, company_stats["pos_rate"], color=M_GREEN, edgecolor="white", label="+1 rate")
    ax.barh(y, -company_stats["neg_rate"], color=M_YELLOW_DEEP, edgecolor="white", label="-1 rate")

    ax.set_yticks(y)
    ax.set_yticklabels(company_stats["company"])
    ax.axvline(0, color=M_DARK, linewidth=1.0, alpha=0.6)
    ax.set_xlim(-80, 100)
    ax.set_xlabel("Rate (%)  (left = negative, right = positive)", fontsize=13)
    ax.set_title(
        "Company Safety Profile (Positive + Negative Together)\n"
        "(color is score polarity, company is y-axis label)",
        fontsize=15,
        fontweight="bold",
    )
    ax.legend(loc="lower right", frameon=False)

    # Show safety balance near each row
    for yi, bal in zip(y, company_stats["balance"]):
        ax.text(82, yi, f"bal {bal:+.1f}", va="center", ha="right", fontsize=8, color=M_DARK)

    ax.xaxis.set_major_formatter(mtick.PercentFormatter())
    plt.tight_layout()
    fig.savefig(PLOT_DIR / "01_company_ranking.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  01_company_ranking.png")


# ═══════════════════════════════════════════════════════════════════════
# Plot 2: Company × Dimension Heatmap
# ═══════════════════════════════════════════════════════════════════════
def plot_company_dim_heatmap(data):
    cd = defaultdict(lambda: defaultdict(lambda: {"pos": 0, "neg": 0}))
    for pid, pdata in data["prompts"].items():
        c = pdata["company"]
        for s in pdata.get("kept_spans", []):
            dim = s.get("dimension", "?")
            if dim not in DIMS:
                continue
            if s.get("score", 0) > 0:
                cd[c][dim]["pos"] += 1
            elif s.get("score", 0) < 0:
                cd[c][dim]["neg"] += 1

    companies = sorted(cd.keys(), key=lambda c: sum(
        cd[c][d]["neg"] / max(cd[c][d]["pos"] + cd[c][d]["neg"], 1) for d in DIMS
    ) / len(DIMS))

    pos_matrix = []
    neg_matrix = []
    for c in companies:
        pos_row = []
        neg_row = []
        for d in DIMS:
            p = cd[c][d]["pos"]
            n = cd[c][d]["neg"]
            t = p + n
            pos_row.append(p / t * 100 if t > 0 else np.nan)
            neg_row.append(n / t * 100 if t > 0 else np.nan)
        pos_matrix.append(pos_row)
        neg_matrix.append(neg_row)

    pos_df = pd.DataFrame(pos_matrix, index=companies, columns=[DIM_SHORT[d] for d in DIMS])
    neg_df = pd.DataFrame(neg_matrix, index=companies, columns=[DIM_SHORT[d] for d in DIMS])

    fig, axes = plt.subplots(1, 2, figsize=(16, 14), sharey=True)
    sns.heatmap(pos_df, annot=True, fmt=".0f", cmap=CMAP_POS,
                vmin=0, vmax=100, linewidths=0.5, ax=axes[0],
                cbar_kws={"label": "Positive Rate (%)", "shrink": 0.65},
                mask=pos_df.isna())
    axes[0].set_title(
        "Company × Dimension: Positive Rate (%)\n(color encodes rate, not company ID)",
        fontsize=13,
        fontweight="bold",
    )
    axes[0].set_yticklabels(axes[0].get_yticklabels(), rotation=0)

    sns.heatmap(neg_df, annot=True, fmt=".0f", cmap=CMAP_NEG,
                vmin=0, vmax=100, linewidths=0.5, ax=axes[1],
                cbar_kws={"label": "Negative Rate (%)", "shrink": 0.65},
                mask=neg_df.isna())
    axes[1].set_title(
        "Company × Dimension: Negative Rate (%)\n(color encodes rate, not company ID)",
        fontsize=13,
        fontweight="bold",
    )
    plt.tight_layout()
    fig.savefig(PLOT_DIR / "02_company_dimension_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  02_company_dimension_heatmap.png")


# ═══════════════════════════════════════════════════════════════════════
# Plot 3: Dimension Overview (stacked bar)
# ═══════════════════════════════════════════════════════════════════════
def plot_dimension_overview(data):
    dim_stats = defaultdict(lambda: {"pos": 0, "neg": 0})
    for pid, pdata in data["prompts"].items():
        for s in pdata.get("kept_spans", []):
            dim = s.get("dimension", "?")
            if dim not in DIMS:
                continue
            if s.get("score", 0) > 0:
                dim_stats[dim]["pos"] += 1
            elif s.get("score", 0) < 0:
                dim_stats[dim]["neg"] += 1

    dims_sorted = sorted(DIMS, key=lambda d: dim_stats[d]["neg"] / max(dim_stats[d]["pos"] + dim_stats[d]["neg"], 1), reverse=True)

    pos_vals = [dim_stats[d]["pos"] for d in dims_sorted]
    neg_vals = [dim_stats[d]["neg"] for d in dims_sorted]
    labels = [DIM_SHORT[d] for d in dims_sorted]

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(dims_sorted))
    w = 0.6
    ax.bar(x, pos_vals, w, label="Positive (+1)", color=M_GREEN, edgecolor="white")
    ax.bar(x, neg_vals, w, bottom=pos_vals, label="Negative (-1)", color=M_YELLOW_DEEP, edgecolor="white")

    for i, d in enumerate(dims_sorted):
        total = dim_stats[d]["pos"] + dim_stats[d]["neg"]
        neg_rate = dim_stats[d]["neg"] / total * 100
        ax.text(i, total + 5, f"{neg_rate:.1f}%", ha="center", fontsize=10, fontweight="bold", color=M_OLIVE)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylabel("Span Count")
    ax.set_title(
        "Dimension Overview: Positive vs Negative Spans\n"
        "(bar color = score polarity; x-axis = dimension)",
        fontsize=14,
        fontweight="bold",
    )
    ax.legend(loc="upper right")
    plt.tight_layout()
    fig.savefig(PLOT_DIR / "03_dimension_overview.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  03_dimension_overview.png")


# ═══════════════════════════════════════════════════════════════════════
# Plot 4: Category Comparison (grouped bar)
# ═══════════════════════════════════════════════════════════════════════
def plot_category_comparison(data):
    cat_dim = defaultdict(lambda: defaultdict(lambda: {"pos": 0, "neg": 0}))
    for pid, pdata in data["prompts"].items():
        cat = get_category(pid)
        for s in pdata.get("kept_spans", []):
            dim = s.get("dimension", "?")
            if dim not in DIMS:
                continue
            if s.get("score", 0) > 0:
                cat_dim[cat][dim]["pos"] += 1
            elif s.get("score", 0) < 0:
                cat_dim[cat][dim]["neg"] += 1

    cats = ["coding_agent", "chatbot", "specialized_agent"]
    cat_labels = ["Coding Agent", "Chatbot", "Specialized Agent"]

    x = np.arange(len(DIMS))
    width = 0.25
    fig, ax = plt.subplots(figsize=(14, 6))

    for i, (cat, label) in enumerate(zip(cats, cat_labels)):
        balance = []
        for d in DIMS:
            p = cat_dim[cat][d]["pos"]
            n = cat_dim[cat][d]["neg"]
            t = p + n
            balance.append(((p - n) / t * 100) if t > 0 else 0)
        ax.bar(x + i * width, balance, width, label=label, color=PALETTE_CATS[i], edgecolor="white")

    ax.set_xticks(x + width)
    ax.set_xticklabels([DIM_SHORT[d] for d in DIMS], rotation=15, ha="right")
    ax.axhline(0, color=M_DARK, linewidth=1.0, alpha=0.6)
    ax.set_ylabel("Safety Balance (%) = (+1 - -1) / total")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_title("Product Category × Dimension: Safety Balance\n(positive means more good spans than bad spans)", fontsize=14, fontweight="bold")
    ax.legend()
    plt.tight_layout()
    fig.savefig(PLOT_DIR / "04_category_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  04_category_comparison.png")


# ═══════════════════════════════════════════════════════════════════════
# Plot 5: Dimension Co-occurrence Heatmap
# ═══════════════════════════════════════════════════════════════════════
def plot_cooccurrence(data):
    from itertools import combinations
    cooccur = Counter()
    for pid, pdata in data["prompts"].items():
        pos_dims = defaultdict(set)
        for s in pdata.get("kept_spans", []):
            key = (s["start"], s["end"])
            dim = s.get("dimension", "?")
            if dim in DIMS:
                pos_dims[key].add(dim)
        for key, dims_set in pos_dims.items():
            for a, b in combinations(sorted(dims_set), 2):
                cooccur[(a, b)] += 1

    matrix = np.zeros((len(DIMS), len(DIMS)))
    for i, d1 in enumerate(DIMS):
        for j, d2 in enumerate(DIMS):
            if i == j:
                matrix[i][j] = 0
            elif i < j:
                matrix[i][j] = cooccur.get((d1, d2), 0)
            else:
                matrix[i][j] = cooccur.get((d2, d1), 0)

    df = pd.DataFrame(matrix, index=[DIM_SHORT[d] for d in DIMS], columns=[DIM_SHORT[d] for d in DIMS])

    fig, ax = plt.subplots(figsize=(10, 8))
    mask = np.eye(len(DIMS), dtype=bool)
    sns.heatmap(df, annot=True, fmt=".0f", cmap=CMAP_NEUTRAL, linewidths=0.5,
                ax=ax, mask=mask, cbar_kws={"label": "Co-occurrence Count", "shrink": 0.7})
    ax.set_title(
        "Dimension Co-occurrence\n"
        "(color encodes co-occurrence count, not company)",
        fontsize=14,
        fontweight="bold",
    )
    plt.tight_layout()
    fig.savefig(PLOT_DIR / "05_dimension_cooccurrence.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  05_dimension_cooccurrence.png")


# ═══════════════════════════════════════════════════════════════════════
# Plot 6: Prompt Size vs Safety
# ═══════════════════════════════════════════════════════════════════════
def plot_size_vs_safety(data):
    rows = []
    for pid, pdata in data["prompts"].items():
        size = pdata.get("size_bytes", 0)
        spans = pdata.get("kept_spans", [])
        pos = sum(1 for s in spans if s.get("score", 0) > 0)
        neg = sum(1 for s in spans if s.get("score", 0) < 0)
        total = pos + neg
        neg_rate = neg / total * 100 if total > 0 else 0
        pos_rate = pos / total * 100 if total > 0 else 0
        balance = (pos - neg) / total * 100 if total > 0 else 0
        rows.append({
            "size_kb": size / 1024,
            "neg_rate": neg_rate,
            "pos_rate": pos_rate,
            "balance": balance,
            "total_spans": total,
            "company": pdata["company"],
            "label": pdata.get("product_label", "")[:30],
        })

    df = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(12, 7))
    scatter = ax.scatter(
        df["size_kb"],
        df["balance"],
        s=df["total_spans"] * 2,
        c=df["pos_rate"],
        cmap=CMAP_YGB,
        alpha=0.82,
        edgecolors="#F8FAFC",
        linewidths=0.9,
    )
    plt.colorbar(scatter, ax=ax, label="Positive Rate (%)", shrink=0.7)

    # Sparse + de-overlapped labeling:
    # pick a small set of key outliers and place labels in a spaced right-side column.
    low = df.nsmallest(6, "balance")
    high = df.nlargest(4, "balance")
    large = df.nlargest(6, "total_spans")
    labels_df = (
        pd.concat([low, high, large])
        .drop_duplicates(subset=["label", "company"])
        .copy()
    )
    labels_df["priority"] = labels_df["balance"].abs() + labels_df["total_spans"] * 0.25
    labels_df = labels_df.nlargest(10, "priority").sort_values("balance")

    if len(labels_df) > 0:
        y_min = min(-100, df["balance"].min() - 3)
        y_max = max(100, df["balance"].max() + 3)
        min_gap = 7.5
        y_targets = labels_df["balance"].tolist()

        # Forward pass: enforce minimum vertical distance.
        for i in range(1, len(y_targets)):
            if y_targets[i] - y_targets[i - 1] < min_gap:
                y_targets[i] = y_targets[i - 1] + min_gap

        # If overflow, shift down then backward pass.
        if y_targets and y_targets[-1] > y_max:
            shift = y_targets[-1] - y_max
            y_targets = [y - shift for y in y_targets]
            for i in range(len(y_targets) - 2, -1, -1):
                if y_targets[i + 1] - y_targets[i] < min_gap:
                    y_targets[i] = y_targets[i + 1] - min_gap
            if y_targets[0] < y_min:
                lift = y_min - y_targets[0]
                y_targets = [y + lift for y in y_targets]

        x_label = df["size_kb"].max() * 1.02
        for ((_, row), y_lab) in zip(labels_df.iterrows(), y_targets):
            tag = f"[{row['company']}] {row['label']}"
            ax.annotate(
                tag,
                xy=(row["size_kb"], row["balance"]),
                xytext=(x_label, y_lab),
                fontsize=7.2,
                alpha=0.9,
                va="center",
                ha="left",
                arrowprops=dict(arrowstyle="-", color="#64748B", lw=0.7, alpha=0.65),
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="#CBD5E1", alpha=0.78),
            )

    ax.set_xlabel("Prompt Size (KB)", fontsize=13)
    ax.set_ylabel("Safety Balance (%)", fontsize=13)
    ax.axhline(0, color=M_DARK, linewidth=1.0, alpha=0.6)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.grid(alpha=0.22, color="#94A3B8", linestyle="-", linewidth=0.7)
    ax.set_title(
        "Prompt Size vs Safety Balance\n"
        "(bubble size = total spans, color = positive rate; sparse labels for key outliers)",
        fontsize=14,
        fontweight="bold",
    )
    plt.tight_layout()
    fig.savefig(PLOT_DIR / "06_size_vs_safety.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  06_size_vs_safety.png")


# ═══════════════════════════════════════════════════════════════════════
# Plot 7: Product Scorecard (top/bottom)
# ═══════════════════════════════════════════════════════════════════════
def plot_product_scorecard(data):
    products = []
    for pid, pdata in data["prompts"].items():
        spans = pdata.get("kept_spans", [])
        pos = sum(1 for s in spans if s.get("score", 0) > 0)
        neg = sum(1 for s in spans if s.get("score", 0) < 0)
        total = pos + neg
        if total < 5:
            continue
        overall = (pos - neg) / total
        label = pdata.get("product_label", pid)[:35]
        products.append({"label": label, "company": pdata["company"], "overall": overall})

    products.sort(key=lambda x: x["overall"])

    bottom_15 = products[:15]
    top_15 = products[-15:]

    # Group same-company products together for easier comparison.
    bottom_15 = sorted(bottom_15, key=lambda x: (x["company"], x["overall"], x["label"]))
    top_15 = sorted(top_15, key=lambda x: (x["company"], -x["overall"], x["label"]))

    # Stable company colors across both subplots.
    companies_in_view = sorted({p["company"] for p in bottom_15 + top_15})
    company_colors = sns.color_palette("tab20", n_colors=max(3, len(companies_in_view)))
    company_color_map = {c: company_colors[i] for i, c in enumerate(companies_in_view)}

    def grouped_labels(items):
        return [f"[{p['company']}] {p['label']}" for p in items]

    def draw_company_separators(ax, items):
        for i in range(1, len(items)):
            if items[i]["company"] != items[i - 1]["company"]:
                ax.axhline(i - 0.5, color="#94A3B8", linewidth=0.8, alpha=0.4)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    colors_b = [company_color_map[p["company"]] for p in bottom_15]
    ax1.barh(grouped_labels(bottom_15), [p["overall"] for p in bottom_15], color=colors_b, edgecolor="white")
    draw_company_separators(ax1, bottom_15)
    ax1.set_xlabel("Safety Score")
    ax1.set_title(
        "Bottom 15 Products\n(most safety concerns; color = score tier)",
        fontsize=13,
        fontweight="bold",
    )
    ax1.axvline(x=0, color="black", linewidth=0.5)
    ax1.set_xlim(-1.1, 1.1)

    colors_t = [company_color_map[p["company"]] for p in top_15]
    ax2.barh(grouped_labels(top_15), [p["overall"] for p in top_15], color=colors_t, edgecolor="white")
    draw_company_separators(ax2, top_15)
    ax2.set_xlabel("Safety Score")
    ax2.set_title(
        "Top 15 Products\n(safest system prompts; color = score tier)",
        fontsize=13,
        fontweight="bold",
    )
    ax2.set_xlim(-1.1, 1.1)

    plt.suptitle("Product Safety Scorecard\n(score = (positive − negative) / total, range: −1 to +1)", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    fig.savefig(PLOT_DIR / "07_product_scorecard.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  07_product_scorecard.png")


# ═══════════════════════════════════════════════════════════════════════
# Plot 9: Version Evolution on Real Timeline
# ═══════════════════════════════════════════════════════════════════════

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _extract_date_from_label(label):
    """Try to parse '(Mon YYYY)' from product labels like 'Grok 3 Official (Mar 2025)'."""
    import re
    m = re.search(r"\(([A-Z][a-z]{2})\s+(\d{4})\)", label)
    if m:
        month_str = m.group(1).lower()
        year = int(m.group(2))
        month = MONTH_MAP.get(month_str)
        if month:
            return datetime(year, month, 15)
    return None


def plot_version_evolution(data):
    from datetime import timedelta
    from matplotlib.lines import Line2D

    company_series = defaultdict(list)
    for pid, pdata in data["prompts"].items():
        company = pdata.get("company", "")
        spans = pdata.get("kept_spans", [])
        pos = sum(1 for s in spans if s.get("score", 0) > 0)
        neg = sum(1 for s in spans if s.get("score", 0) < 0)
        total = pos + neg
        if total == 0:
            continue
        neg_rate = neg / total * 100

        parsed_date = parse_prompt_date(pdata.get("date", ""))
        if parsed_date is None:
            parsed_date = _extract_date_from_label(pdata.get("product_label", ""))

        label = pdata.get("product_label", pid)
        company_series[company].append({
            "label": label,
            "date": parsed_date,
            "neg_rate": neg_rate,
        })

    dated_companies = {}
    for c, versions in company_series.items():
        dated = [v for v in versions if v["date"] is not None]
        if len(dated) >= 3:
            dated.sort(key=lambda v: v["date"])
            dated_companies[c] = dated

    top_companies = sorted(dated_companies.items(), key=lambda kv: len(kv[1]), reverse=True)[:8]
    selected = dict(top_companies)
    if not selected:
        return

    fig, ax = plt.subplots(figsize=(16, 8.5))
    vivid_cycle = [
        "#E53935", "#FB8C00", "#EC407A", "#1E88E5",
        "#8E24AA", "#00ACC1", "#43A047", "#6D4C41",
    ]
    colors = vivid_cycle[:len(selected)]

    all_dates = []
    all_rates = []
    all_label_points = []

    for (company, versions), color in zip(selected.items(), colors):
        dates = [v["date"] for v in versions]
        rates = [v["neg_rate"] for v in versions]
        all_dates.extend(dates)
        all_rates.extend(rates)

        ax.plot(
            dates, rates,
            color=color, linewidth=2.4, zorder=2,
            label=f"{company} ({len(versions)})",
        )
        ax.scatter(
            dates, rates,
            color=color, s=55, zorder=3,
            edgecolors="white", linewidths=1.3,
        )

        for d, r, v in zip(dates, rates, versions):
            short = v["label"]
            if "(" in short:
                short = short[:short.index("(")].strip()
            if len(short) > 25:
                short = short[:23] + "…"
            all_label_points.append((d, r, short, color))

    # De-overlap version labels using a grid-based approach:
    # place labels alternating above/below the point.
    if all_label_points:
        all_label_points.sort(key=lambda p: (p[0], p[1]))
        placed = []
        for d, r, short, color in all_label_points:
            y_off = 9
            for pd, pr, _, _ in placed:
                if abs((d - pd).days) < 45 and abs(r - pr) < 8:
                    y_off = -14
                    break
            ax.annotate(
                short,
                xy=(d, r),
                xytext=(0, y_off),
                textcoords="offset points",
                fontsize=5.8, color=color, ha="center",
                va="bottom" if y_off > 0 else "top",
                alpha=0.88,
            )
            placed.append((d, r, short, color))

    # End-of-line company labels (right side).
    for (company, versions), color in zip(selected.items(), colors):
        last_d = versions[-1]["date"]
        last_r = versions[-1]["neg_rate"]
        ax.annotate(
            f"{company}: {last_r:.1f}%",
            xy=(last_d, last_r),
            xytext=(12, 0),
            textcoords="offset points",
            color=color, va="center", fontsize=8.5, fontweight="semibold",
        )

    if all_rates:
        y_min = max(0, min(all_rates) - 8)
        y_max = min(100, max(all_rates) + 8)
        if y_max - y_min < 25:
            mid = (y_max + y_min) / 2
            y_min = max(0, mid - 12.5)
            y_max = min(100, mid + 12.5)
        ax.set_ylim(y_min, y_max)

    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.autofmt_xdate(rotation=35, ha="right")

    if all_dates:
        span = max(all_dates) - min(all_dates)
        pad = span * 0.06
        if pad.days < 30:
            pad = timedelta(days=30)
        right_pad = span * 0.15
        if right_pad.days < 60:
            right_pad = timedelta(days=60)
        ax.set_xlim(min(all_dates) - pad, max(all_dates) + right_pad)

    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Negative Rate (%)", fontsize=12)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_title(
        "Version Evolution by Company (Negative Rate)\n"
        "each point = one system prompt version on real timeline; only companies with ≥3 dated versions",
        fontsize=13, fontweight="bold", color=M_DARK,
    )
    ax.grid(axis="both", linestyle="--", alpha=0.28, color="#64748B")
    ax.set_facecolor("#F8FAFC")
    for spine in ax.spines.values():
        spine.set_alpha(0.25)
    ax.legend(
        loc="center left", bbox_to_anchor=(1.01, 0.5),
        frameon=False, fontsize=8.5,
        title="Company (dated versions)",
    )
    plt.tight_layout()
    fig.savefig(PLOT_DIR / "09_version_evolution.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  09_version_evolution.png")


def plot_dataset_overview(data):
    prompts = data["prompts"]

    companies = Counter()
    categories = Counter()
    dates_parsed = []
    sizes_kb = []

    for pid, pdata in prompts.items():
        companies[pdata["company"]] += 1
        categories[get_category(pid)] += 1
        sizes_kb.append(pdata.get("size_bytes", 0) / 1024)
        dt = parse_prompt_date(pdata.get("date", ""))
        if dt is None:
            dt = _extract_date_from_label(pdata.get("product_label", ""))
        if dt is not None:
            dates_parsed.append(dt)

    fig, axes = plt.subplots(2, 2, figsize=(18, 13))
    fig.suptitle(
        f"Dataset Overview — {len(prompts)} System Prompts from {len(companies)} Companies",
        fontsize=16, fontweight="bold", color=M_DARK, y=0.98,
    )

    # --- (a) Company distribution ---
    ax = axes[0, 0]
    comp_sorted = companies.most_common()
    comp_names = [c for c, _ in comp_sorted]
    comp_counts = [n for _, n in comp_sorted]
    bars = ax.barh(comp_names[::-1], comp_counts[::-1], color=M_GREEN, edgecolor="white")
    for bar, cnt in zip(bars, comp_counts[::-1]):
        ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
                str(cnt), va="center", fontsize=8, color=M_DARK)
    ax.set_xlabel("Number of Prompts")
    ax.set_title("(a) Prompts per Company", fontsize=13, fontweight="bold")
    ax.set_xlim(0, max(comp_counts) * 1.2)

    # --- (b) Product category distribution ---
    ax = axes[0, 1]
    cat_labels_map = {
        "chatbot": "Chatbot",
        "coding_agent": "Coding Agent",
        "specialized_agent": "Specialized Agent",
        "other": "Other",
    }
    cat_order = ["chatbot", "coding_agent", "specialized_agent", "other"]
    cat_vals = [categories.get(c, 0) for c in cat_order]
    cat_labels = [cat_labels_map.get(c, c) for c in cat_order]
    cat_colors = [M_YELLOW_DEEP, M_GREEN, M_GREEN_DEEP, M_OLIVE]
    wedges, texts, autotexts = ax.pie(
        cat_vals, labels=cat_labels, autopct=lambda pct: f"{pct:.0f}%\n({int(round(pct / 100 * sum(cat_vals)))})",
        colors=cat_colors, startangle=90, textprops={"fontsize": 11},
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    for at in autotexts:
        at.set_fontsize(10)
        at.set_fontweight("bold")
    ax.set_title("(b) Product Category Distribution", fontsize=13, fontweight="bold")

    # --- (c) Temporal distribution ---
    ax = axes[1, 0]
    if dates_parsed:
        date_quarters = []
        for dt in dates_parsed:
            q = (dt.month - 1) // 3
            quarter_start = datetime(dt.year, q * 3 + 1, 1)
            date_quarters.append(quarter_start)
        q_counts = Counter(date_quarters)
        q_sorted = sorted(q_counts.keys())
        q_labels = [f"Q{(d.month - 1) // 3 + 1}\n{d.year}" for d in q_sorted]
        q_vals = [q_counts[d] for d in q_sorted]
        ax.bar(range(len(q_sorted)), q_vals, color=M_GREEN_DEEP, edgecolor="white")
        ax.set_xticks(range(len(q_sorted)))
        ax.set_xticklabels(q_labels, fontsize=9)
        for i, v in enumerate(q_vals):
            ax.text(i, v + 0.2, str(v), ha="center", fontsize=9, fontweight="bold", color=M_DARK)
    ax.set_ylabel("Number of Prompts")
    ax.set_title("(c) Temporal Distribution (by Quarter)", fontsize=13, fontweight="bold")
    undated = len(prompts) - len(dates_parsed)
    if undated > 0:
        ax.text(0.97, 0.95, f"{undated} undated", transform=ax.transAxes,
                ha="right", va="top", fontsize=9, color="#94A3B8", style="italic")

    # --- (d) Prompt size distribution ---
    ax = axes[1, 1]
    bins = [0, 2, 5, 15, 30, max(sizes_kb) + 1]
    bin_labels = ["<2 KB", "2-5 KB", "5-15 KB", "15-30 KB", ">30 KB"]
    bin_colors = [M_YELLOW, M_YELLOW_DEEP, M_GREEN, M_GREEN_DEEP, M_OLIVE]
    hist_vals = []
    for i in range(len(bins) - 1):
        cnt = sum(1 for s in sizes_kb if bins[i] <= s < bins[i + 1])
        hist_vals.append(cnt)
    bars = ax.bar(bin_labels, hist_vals, color=bin_colors, edgecolor="white")
    for bar, cnt in zip(bars, hist_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(cnt), ha="center", fontsize=10, fontweight="bold", color=M_DARK)
    ax.set_ylabel("Number of Prompts")
    ax.set_title("(d) Prompt Size Distribution", fontsize=13, fontweight="bold")
    median_kb = sorted(sizes_kb)[len(sizes_kb) // 2]
    ax.text(0.97, 0.95, f"median: {median_kb:.1f} KB", transform=ax.transAxes,
            ha="right", va="top", fontsize=9, color="#94A3B8", style="italic")

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(PLOT_DIR / "00_dataset_overview.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  00_dataset_overview.png")


def main():
    print("Loading data...")
    data = load_data()
    print(f"Loaded {data['metadata']['total_prompts']} prompts, {data['metadata']['total_kept_spans']} spans\n")
    print("Generating plots:")

    plot_dataset_overview(data)
    plot_company_ranking(data)
    plot_company_dim_heatmap(data)
    plot_dimension_overview(data)
    plot_category_comparison(data)
    plot_cooccurrence(data)
    plot_size_vs_safety(data)
    plot_product_scorecard(data)
    plot_version_evolution(data)

    print(f"\nAll plots saved to: {PLOT_DIR}/")


if __name__ == "__main__":
    main()
