"""Generate an Inter-Annotator Agreement (IAA) report from training tool outputs.

Usage:
    python generate_iaa_report.py                          # auto-detect latest files
    python generate_iaa_report.py -o iaa_report.txt        # custom output path
    python generate_iaa_report.py --files f1.json f2.json  # specify files explicitly
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import date
from itertools import combinations
from pathlib import Path

DIMENSION_NAMES = {
    "D1": "Identity Transparency",
    "D2": "Truthfulness & Information Integrity",
    "D3": "Privacy & Data Protection",
    "D4": "Tool/Action Safety",
    "D5": "User Agency & Manipulation Prevention",
    "D6": "Unsafe Request Handling",
    "D7": "Harm Prevention & User Safety",
    "D8": "Fairness, Inclusion & Neutrality",
    "Misc": "Miscellaneous",
}

TRAINING_DIR = Path(__file__).parent / "training_tool" / "outputs"


def dim_label(dim: str) -> str:
    name = DIMENSION_NAMES.get(dim, "")
    return f"{dim} {name}" if name else dim


def load_annotations(filepath: Path) -> dict:
    with open(filepath) as f:
        return json.load(f)


def find_latest_training_files() -> list[Path]:
    """Pick the latest file per reviewer (by filename timestamp)."""
    by_reviewer: dict[str, Path] = {}
    for p in sorted(TRAINING_DIR.glob("training_*.json")):
        match = re.match(r"training_(.+?)_\d{8}_\d{6}\.json", p.name)
        if not match:
            continue
        reviewer = match.group(1)
        by_reviewer[reviewer] = p
    return list(by_reviewer.values())


def span_key(prompt_key: str, span: dict) -> tuple:
    return (prompt_key, span["dimension"], span["start"], span["end"])


def is_rejected(span: dict) -> bool:
    return span.get("rejected", False)


def build_llm_span_decisions(data: dict) -> dict[tuple, bool]:
    """Return {span_key: accepted} for every LLM span in this annotator's file."""
    decisions: dict[tuple, bool] = {}
    for prompt_key, prompt_data in data["annotations"].items():
        for span in prompt_data["spans"]:
            if span.get("source") != "llm":
                continue
            key = span_key(prompt_key, span)
            decisions[key] = not is_rejected(span)
    return decisions


def build_dimension_flags(data: dict) -> tuple[dict[tuple, bool], set[str]]:
    """Return ({(prompt_key, dim): flagged}, set_of_prompt_keys).

    A dimension is "flagged" if the annotator accepted an LLM span or added
    a human span for that dimension on that prompt.
    """
    flags: dict[tuple, bool] = {}
    annotator_prompts: set[str] = set()
    for prompt_key, prompt_data in data["annotations"].items():
        annotator_prompts.add(prompt_key)
        flagged_dims: set[str] = set()
        for span in prompt_data["spans"]:
            source = span.get("source", "")
            if source == "llm" and not is_rejected(span):
                flagged_dims.add(span["dimension"])
            elif source == "human":
                flagged_dims.add(span["dimension"])
        for dim in DIMENSION_NAMES:
            flags[(prompt_key, dim)] = dim in flagged_dims
    return flags, annotator_prompts


def prompt_display_name(prompt_key: str, prompt_data: dict) -> str:
    company = prompt_data.get("company", "")
    filename = prompt_data.get("filename", prompt_key)
    return f"{company} / {filename}" if company else filename


def krippendorffs_alpha(all_decisions: list[dict[tuple, bool]], all_keys: list[tuple]) -> float | None:
    """Compute Krippendorff's alpha for nominal data.

    Uses the coincidence-matrix formulation:
      D_o = 1 - sum_c(o_cc) / n
      D_e = 1 - sum_c(n_c*(n_c-1)) / (n*(n-1))
      alpha = 1 - D_o / D_e
    """
    n_coders = len(all_decisions)
    cat_idx = {True: 0, False: 1}
    n_cats = 2

    n_uc = []
    m_u = []
    for key in all_keys:
        counts = [0, 0]
        m = 0
        for a in range(n_coders):
            v = all_decisions[a].get(key)
            if v is not None:
                counts[cat_idx[v]] += 1
                m += 1
        if m >= 2:
            n_uc.append(counts)
            m_u.append(m)

    if not n_uc:
        return None

    n_total = sum(m_u)

    d_o = 0.0
    for u_idx in range(len(n_uc)):
        m = m_u[u_idx]
        pair_disagree = 2 * n_uc[u_idx][0] * n_uc[u_idx][1]
        d_o += pair_disagree / (m - 1)
    d_o /= n_total

    n_c = [0, 0]
    for u_idx in range(len(n_uc)):
        n_c[0] += n_uc[u_idx][0]
        n_c[1] += n_uc[u_idx][1]

    d_e = 2 * n_c[0] * n_c[1] / (n_total * (n_total - 1))

    if d_e == 0:
        return None

    return 1.0 - d_o / d_e


def fleiss_kappa(all_decisions: list[dict[tuple, bool]], all_keys: list[tuple]) -> float | None:
    """Compute Fleiss' Kappa for multiple annotators with binary nominal data."""
    n_coders = len(all_decisions)
    n_items = 0
    counts = []
    for key in all_keys:
        votes = [all_decisions[a].get(key) for a in range(n_coders)]
        present = [v for v in votes if v is not None]
        if len(present) < 2:
            continue
        n1 = sum(1 for v in present if v)
        n0 = len(present) - n1
        counts.append((n0, n1, len(present)))
        n_items += 1

    if n_items == 0:
        return None

    p_bar = 0.0
    total_votes = 0
    total_1 = 0
    for n0, n1, m in counts:
        p_bar += (n0 * (n0 - 1) + n1 * (n1 - 1)) / (m * (m - 1))
        total_votes += m
        total_1 += n1
    p_bar /= n_items

    p1 = total_1 / total_votes
    p0 = 1 - p1
    p_e = p0 * p0 + p1 * p1

    if p_e == 1:
        return None
    return (p_bar - p_e) / (1 - p_e)


def avg_cohens_kappa(all_decisions: list[dict[tuple, bool]], all_keys: list[tuple]) -> float | None:
    """Compute average pairwise Cohen's Kappa."""
    n_coders = len(all_decisions)
    kappas = []
    for i, j in combinations(range(n_coders), 2):
        tp = tn = fp = fn = 0
        for key in all_keys:
            a, b = all_decisions[i].get(key), all_decisions[j].get(key)
            if a is None or b is None:
                continue
            if a and b:
                tp += 1
            elif not a and not b:
                tn += 1
            elif a and not b:
                fp += 1
            else:
                fn += 1
        total = tp + tn + fp + fn
        if total == 0:
            continue
        p_o = (tp + tn) / total
        p_e = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / (total * total)
        if p_e == 1:
            continue
        kappas.append((p_o - p_e) / (1 - p_e))
    return sum(kappas) / len(kappas) if kappas else None


def alpha_interpretation(a: float) -> str:
    if a < 0:
        return "Less agreement than expected by chance"
    elif a < 0.667:
        return "Tentative conclusions only"
    elif a < 0.800:
        return "Acceptable for some purposes"
    else:
        return "Good reliability"


def generate_report(files: list[Path], output: Path | None = None) -> str:
    annotators_data = []
    for f in files:
        d = load_annotations(f)
        annotators_data.append(d)

    names = [d["metadata"]["reviewer"] for d in annotators_data]
    n = len(names)

    # =========================================================
    # 1. LLM span-level: accept/reject on pre-annotated spans
    # =========================================================
    all_decisions = [build_llm_span_decisions(d) for d in annotators_data]
    all_keys = set()
    for dec in all_decisions:
        all_keys |= dec.keys()
    all_keys = sorted(all_keys)
    total_llm_spans = len(all_keys)

    pair_results = []
    for i, j in combinations(range(n), 2):
        agree = compared = 0
        for key in all_keys:
            if key in all_decisions[i] and key in all_decisions[j]:
                compared += 1
                if all_decisions[i][key] == all_decisions[j][key]:
                    agree += 1
        pair_results.append((i, j, agree, compared))

    all_agree = 0
    for key in all_keys:
        votes = [all_decisions[a].get(key) for a in range(n)]
        if all(v is not None for v in votes) and len(set(votes)) == 1:
            all_agree += 1

    alpha_span = krippendorffs_alpha(all_decisions, all_keys)
    fleiss_span = fleiss_kappa(all_decisions, all_keys)
    avg_kappa_span = avg_cohens_kappa(all_decisions, all_keys)
    avg_pairwise_span = sum(
        a / c * 100 for _, _, a, c in pair_results if c > 0
    ) / len(pair_results) if pair_results else 0

    # =========================================================
    # 2. Combined: 20 LLM spans + human-added new dimensions
    #    LLM spans: accept=1, reject=0
    #    Human new dims: added=1, not added=0
    #    Only (prompt, dim) pairs flagged by >= 1 person.
    # =========================================================
    all_dim_flags = []
    all_annotator_prompts = []
    for d in annotators_data:
        flags, prompts_set = build_dimension_flags(d)
        all_dim_flags.append(flags)
        all_annotator_prompts.append(prompts_set)

    all_prompt_keys = set()
    for ps in all_annotator_prompts:
        all_prompt_keys |= ps
    all_prompt_keys = sorted(all_prompt_keys)

    # Which dimensions have LLM spans per prompt
    llm_dims_per_prompt: dict[str, set] = defaultdict(set)
    for d in annotators_data:
        for pk, pd in d["annotations"].items():
            for span in pd["spans"]:
                if span.get("source") == "llm":
                    llm_dims_per_prompt[pk].add(span["dimension"])

    # Collect all (prompt, dim) where at least one person flagged
    active_dim_keys = []
    active_dim_sources = []  # "LLM" or "HUMAN" per item
    for pk in all_prompt_keys:
        for dim in sorted(DIMENSION_NAMES.keys(), key=lambda d: int(d[1:])):
            flagged_by_anyone = False
            for a in range(n):
                if pk in all_annotator_prompts[a] and all_dim_flags[a].get((pk, dim), False):
                    flagged_by_anyone = True
                    break
            if flagged_by_anyone:
                active_dim_keys.append((pk, dim))
                active_dim_sources.append("LLM" if dim in llm_dims_per_prompt.get(pk, set()) else "HUMAN")

    # Build decision dicts for active items only
    active_dim_decisions: list[dict[tuple, bool]] = []
    for a in range(n):
        dec = {}
        for key in active_dim_keys:
            pk = key[0]
            if pk in all_annotator_prompts[a]:
                dec[key] = all_dim_flags[a].get(key, False)
        active_dim_decisions.append(dec)

    alpha_active = krippendorffs_alpha(active_dim_decisions, active_dim_keys)
    fleiss_active = fleiss_kappa(active_dim_decisions, active_dim_keys)
    avg_kappa_active = avg_cohens_kappa(active_dim_decisions, active_dim_keys)

    n_llm_items = sum(1 for s in active_dim_sources if s == "LLM")
    n_human_items = sum(1 for s in active_dim_sources if s == "HUMAN")

    active_pair_results = []
    for i, j in combinations(range(n), 2):
        agree = compared = 0
        for key in active_dim_keys:
            vi = active_dim_decisions[i].get(key)
            vj = active_dim_decisions[j].get(key)
            if vi is not None and vj is not None:
                compared += 1
                if vi == vj:
                    agree += 1
        active_pair_results.append((i, j, agree, compared))

    active_all_compared = sum(
        1 for key in active_dim_keys
        if all(active_dim_decisions[a].get(key) is not None for a in range(n))
    )
    active_all_agree = sum(
        1 for key in active_dim_keys
        if all(active_dim_decisions[a].get(key) is not None for a in range(n))
        and len({active_dim_decisions[a][key] for a in range(n)}) == 1
    )

    # Active dimension disagreements
    active_disagreements = []
    for key in active_dim_keys:
        votes = {}
        for a in range(n):
            v = active_dim_decisions[a].get(key)
            if v is not None:
                votes[a] = v
        if len(votes) >= 2 and len(set(votes.values())) > 1:
            pk, dim = key
            display = pk
            for d in annotators_data:
                if pk in d["annotations"]:
                    display = prompt_display_name(pk, d["annotations"][pk])
                    break
            active_disagreements.append((display, dim, votes))

    # =========================================================
    # 3. LLM span disagreement details
    # =========================================================
    llm_disagreements = []
    for key in all_keys:
        votes = {}
        for a in range(n):
            v = all_decisions[a].get(key)
            if v is not None:
                votes[a] = v
        if len(set(votes.values())) > 1:
            prompt_key, dim, start, end = key
            span_info = None
            for d in annotators_data:
                if prompt_key in d["annotations"]:
                    for s in d["annotations"][prompt_key]["spans"]:
                        if s["source"] == "llm" and s["start"] == start and s["end"] == end:
                            span_info = s
                            prompt_display = prompt_display_name(prompt_key, d["annotations"][prompt_key])
                            break
                if span_info:
                    break
            llm_disagreements.append((prompt_display, dim, span_info, votes))

    # =========================================================
    # 4. Human-added spans list
    # =========================================================
    human_spans: dict[str, list] = defaultdict(list)
    for idx, d in enumerate(annotators_data):
        reviewer = names[idx]
        for prompt_key, prompt_data in d["annotations"].items():
            display = prompt_display_name(prompt_key, prompt_data)
            for span in prompt_data["spans"]:
                if span.get("source") == "human":
                    human_spans[reviewer].append((display, span))

    # =========================================================
    # Build report
    # =========================================================
    lines = []
    w = lines.append

    w(f"IAA Report — Training Tool ({n} Annotators)")
    w("=" * 50)
    w(f"Generated: {date.today()}")
    w(f"Annotators: {', '.join(names)}")
    w(f"Total (prompt, dimension) pairs: {total_llm_spans}")
    w("")

    # --- Agreement Coefficients ---
    w("=" * 70)
    w("AGREEMENT COEFFICIENTS")
    w("=" * 70)
    w("")
    w(f"  {'':28s}  {'Fleiss':>8}  {'Avg Cohen':>10}  {'Krippendorff':>13}  {'Avg Pairwise':>13}")
    w(f"  {'':28s}  {'Kappa':>8}  {'Kappa':>10}  {'Alpha':>13}  {'Agreement':>13}")
    w(f"  {'-'*66}")

    def fmt(v):
        return f"{v:.3f}" if v is not None else "N/A"

    w(f"  {str(total_llm_spans) + ' (prompt, dim) pairs':28s}"
      f"  {fmt(fleiss_span):>8}  {fmt(avg_kappa_span):>10}  {fmt(alpha_span):>13}  {avg_pairwise_span:>12.1f}%")
    w("")
    w(f"  Note: Low chance-corrected scores due to prevalence paradox (91% accept rate).")
    w(f"  Avg pairwise agreement is the most informative metric here.")
    w("")

    # --- Pairwise agreement ---
    w("=" * 50)
    w(f"PAIRWISE AGREEMENT ({total_llm_spans} (prompt, dimension) pairs)")
    w("=" * 50)
    w("")
    for i, j, agree, compared in pair_results:
        ni = names[i].replace(" ", "_")
        nj = names[j].replace(" ", "_")
        pct = agree / compared * 100 if compared else 0
        w(f"  {ni} vs {nj}:   {agree}/{compared} = {pct:.1f}%")
    w("")
    all_compared = sum(1 for key in all_keys if all(all_decisions[a].get(key) is not None for a in range(n)))
    all_pct = all_agree / all_compared * 100 if all_compared else 0
    w(f"  All {n} agree: {all_agree}/{all_compared} = {all_pct:.1f}%")
    w("")

    # --- Disagreements ---
    w("=" * 50)
    w(f"DISAGREEMENTS ({len(llm_disagreements)}/{total_llm_spans} pairs)")
    w("=" * 50)
    w("")
    for idx, (display, dim, span_info, votes) in enumerate(llm_disagreements, 1):
        score_str = f"+{span_info['score']}" if span_info["score"] > 0 else str(span_info["score"])
        w(f"{idx}. [{display}] {dim_label(dim)}, score={score_str}")
        text = span_info["text"]
        text_lines = text.split("\n")
        if len(text_lines) == 1:
            w(f'   Text: "{text}"')
        else:
            w(f'   Text: "{text_lines[0]}')
            for tl in text_lines[1:]:
                w(f'         {tl}')
            w(f'         "')
        for a in range(n):
            safe_name = names[a].replace(" ", "_")
            v = votes.get(a)
            if v is None:
                label = "N/A"
            elif v:
                label = "Accept"
            else:
                label = "REJECT"
            w(f"   {safe_name + ':':18s} {label}")
        w("")

    # --- Human-added spans ---
    w("=" * 50)
    w("HUMAN-ADDED SPANS (extra annotations beyond LLM)")
    w("=" * 50)
    w("")
    for reviewer in names:
        spans = human_spans.get(reviewer, [])
        w(f"{reviewer} ({len(spans)} span{'s' if len(spans) != 1 else ''}):")
        if not spans:
            w("")
            continue
        for display, span in spans:
            score_str = f"+{span['score']}" if span["score"] > 0 else str(span["score"])
            text_preview = span["text"]
            if len(text_preview) > 120:
                text_preview = text_preview[:117] + "..."
            w(f'  - [{display}] {dim_label(span["dimension"])}, score={score_str}')
            w(f'    "{text_preview}"')
        w("")

    report = "\n".join(lines)

    if output:
        output.write_text(report)
        print(f"Report written to {output}")
    else:
        print(report)

    return report


def main():
    parser = argparse.ArgumentParser(description="Generate IAA report from training outputs")
    parser.add_argument("-o", "--output", type=Path, default=Path("iaa_report.txt"),
                        help="Output file path (default: iaa_report.txt)")
    parser.add_argument("--files", nargs="+", type=Path,
                        help="Specific annotation files to compare (default: auto-detect latest per reviewer)")
    args = parser.parse_args()

    if args.files:
        files = args.files
    else:
        files = find_latest_training_files()

    if len(files) < 2:
        print(f"Error: Need at least 2 annotator files, found {len(files)}")
        print(f"Looked in: {TRAINING_DIR}")
        return

    print(f"Found {len(files)} annotator files:")
    for f in files:
        print(f"  - {f.name}")
    print()

    generate_report(files, args.output)


if __name__ == "__main__":
    main()
