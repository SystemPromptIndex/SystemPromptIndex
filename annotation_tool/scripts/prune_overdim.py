#!/usr/bin/env python3
"""
Prune Over-Dimensioned Segments
================================
For segments tagged with 4+ dimensions, use Claude Opus 4.6 (extra-high reasoning)
to select the top 1-3 most relevant dimensions and discard the rest.

Usage:
  export OPENROUTER_API_KEY="sk-or-..."
  python prune_overdim.py                    # process all 4+ dim segments
  python prune_overdim.py --dry-run          # show what would be processed
  python prune_overdim.py --parallel 5       # 5 concurrent API calls
  python prune_overdim.py --threshold 5      # only prune 5+ dim (default: 4)
"""

import argparse
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import requests

# ─── Load .env ────────────────────────────────────────────────────────────────
def _load_dotenv():
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value

_load_dotenv()

# ─── Config ───────────────────────────────────────────────────────────────────
PREANNOTATION_DIR = Path(__file__).parent / "preannotation_v3_89"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "anthropic/claude-opus-4.6"
MAX_TOKENS = 64000
REASONING_EFFORT = "high"

MODEL_PRICING = {
    "anthropic/claude-opus-4.6": {"input": 5, "output": 25},
}

API_TIMEOUT = 300
MAX_RETRIES = 3
RETRY_DELAY = 10

DIMENSIONS = {
    "D1": "Identity Transparency — disclose non-human identity, don't impersonate a human",
    "D2": "Truthfulness & Information Integrity — acknowledge uncertainty, don't fabricate, respect copyright",
    "D3": "Privacy & Data Protection — don't collect/leak PII, be transparent about data use",
    "D4": "Tool/Action Safety — validate before executing, least-privilege, protect system integrity",
    "D5": "User Agency & Manipulation Prevention — no dark patterns, no psychological manipulation, respect user autonomy",
    "D6": "Unsafe Request Handling — refuse illicit requests, resist prompt injection/jailbreak",
    "D7": "Harm Prevention & User Safety — don't encourage harm, de-escalate, provide crisis resources",
    "D8": "Fairness, Inclusion & Neutrality — no discrimination/stereotypes, balanced on political topics",
}

LOCK = Lock()
total_cost = 0.0
total_input_tokens = 0
total_output_tokens = 0

# ─── API ──────────────────────────────────────────────────────────────────────

def call_openrouter(prompt_text: str) -> dict:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set!")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://anonymous.invalid/annotation-tool",
    }
    payload = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt_text}],
        "reasoning": {"effort": REASONING_EFFORT},
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(OPENROUTER_BASE_URL, headers=headers,
                                 json=payload, timeout=API_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else 0
            if status in (429, 500, 502, 503) and attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY * (2 ** attempt)
                print(f"    Retry in {wait}s (HTTP {status})...")
                time.sleep(wait)
            else:
                raise
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY * (2 ** attempt)
                print(f"    Retry in {wait}s (timeout)...")
                time.sleep(wait)
            else:
                raise


def extract_response(resp_json: dict) -> tuple:
    choice = resp_json["choices"][0]["message"]
    output_text = choice.get("content", "") or ""
    usage = resp_json.get("usage", {})
    return output_text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING.get(MODEL, {"input": 5, "output": 25})
    return input_tokens / 1e6 * pricing["input"] + output_tokens / 1e6 * pricing["output"]


def parse_json_array(text: str) -> list:
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)
    text = text.strip()
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass
    match = re.search(r'\[[\s\S]*\]', text)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
    return []


# ─── Pruning Logic ───────────────────────────────────────────────────────────

def build_prune_prompt(text: str, dimensions: list, company: str, product: str) -> str:
    dim_descriptions = "\n".join(
        f"  {k}: {v}" for k, v in DIMENSIONS.items()
    )

    current_dims = "\n".join(
        f'  - {d["dim"]} (score: {"+" if d["score"]>0 else ""}{d["score"]}): {d.get("note", "")[:200]}'
        for d in dimensions
    )

    return f"""You are an expert AI safety auditor. Your task is to prune over-tagged dimension labels on a text span from an AI system prompt.

This span was extracted from {company}'s "{product}" system prompt and was automatically tagged with {len(dimensions)} audit dimensions. That is too many — a single span should have at most 3 dimensions that are genuinely the BEST fit.

DIMENSION DEFINITIONS:
{dim_descriptions}

TEXT SPAN:
"{text}"

CURRENT DIMENSION TAGS:
{current_dims}

YOUR TASK:
Select the 1-3 dimensions that are the BEST fit for this specific text span. Drop any dimension that is only tangentially related or that is a weaker fit than the others.

Decision criteria:
- A dimension is a GOOD fit if the span DIRECTLY and PRIMARILY addresses that dimension's core concern
- A dimension is a POOR fit if it's only indirectly related or if the connection requires a stretch of interpretation
- If a span is about "refusing dangerous requests", that's D6 primarily — don't also add D7 unless the span specifically mentions harm prevention/de-escalation
- If a span is about "safe tool execution", that's D4 primarily — don't also add D6/D7 unless it's specifically about refusing requests or preventing harm
- If a span is about "hiding system instructions", that's primarily D1 (identity/transparency) — don't also add D2/D3 unless it specifically addresses truthfulness or privacy

Return ONLY a JSON array of the dimensions to KEEP (1-3 items). Each item must have the original dim, score, and note:
[
  {{"dim": "D4", "score": 1, "note": "original note here"}},
  ...
]"""


def prune_segment(seg_info: dict) -> dict:
    """Call LLM to prune a single segment. Returns updated dimensions list."""
    global total_cost, total_input_tokens, total_output_tokens

    prompt = build_prune_prompt(
        seg_info["text"],
        seg_info["dimensions"],
        seg_info["company"],
        seg_info["product"],
    )

    resp = call_openrouter(prompt)
    output, in_tok, out_tok = extract_response(resp)
    cost = estimate_cost(in_tok, out_tok)

    with LOCK:
        total_cost += cost
        total_input_tokens += in_tok
        total_output_tokens += out_tok

    result = parse_json_array(output)
    if not result:
        return seg_info["dimensions"]

    valid_dims = {d["dim"] for d in seg_info["dimensions"]}
    pruned = []
    for item in result:
        if item.get("dim") in valid_dims:
            orig = next(d for d in seg_info["dimensions"] if d["dim"] == item["dim"])
            pruned.append(orig)

    if not pruned or len(pruned) > 3:
        return seg_info["dimensions"]

    return pruned


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Prune over-dimensioned segments")
    parser.add_argument("--threshold", type=int, default=4,
                        help="Min dimensions to trigger pruning (default: 4)")
    parser.add_argument("--parallel", type=int, default=1,
                        help="Number of concurrent API calls (default: 1)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be processed without calling API")
    args = parser.parse_args()

    files_data = {}
    all_targets = []

    for f in sorted(PREANNOTATION_DIR.glob("*.json")):
        with f.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        files_data[f.name] = {"path": f, "data": data}

        meta = data.get("metadata", {}).get("prompt", {})
        company = meta.get("company", "")
        product = meta.get("product_label", "")

        for seg_idx, seg in enumerate(data.get("segments", [])):
            if len(seg.get("dimensions", [])) >= args.threshold:
                all_targets.append({
                    "file": f.name,
                    "seg_idx": seg_idx,
                    "text": seg["text"],
                    "dimensions": seg["dimensions"],
                    "company": company,
                    "product": product,
                    "num_dims": len(seg["dimensions"]),
                })

    print(f"Files: {len(files_data)}")
    print(f"Segments with {args.threshold}+ dims: {len(all_targets)}")
    print(f"  4 dims: {sum(1 for t in all_targets if t['num_dims']==4)}")
    print(f"  5 dims: {sum(1 for t in all_targets if t['num_dims']==5)}")
    print(f"  6 dims: {sum(1 for t in all_targets if t['num_dims']==6)}")
    print(f"  7 dims: {sum(1 for t in all_targets if t['num_dims']==7)}")
    print()

    if args.dry_run:
        for t in all_targets[:20]:
            dims = ",".join(d["dim"] for d in t["dimensions"])
            print(f'  [{t["file"]}] {dims} — "{t["text"][:80]}"')
        if len(all_targets) > 20:
            print(f"  ... +{len(all_targets)-20} more")
        print(f"\nEstimated API calls: {len(all_targets)}")
        return

    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set!")
        return

    results = {}
    start_time = time.time()

    def process_one(target):
        key = (target["file"], target["seg_idx"])
        old_dims = [d["dim"] for d in target["dimensions"]]
        try:
            new_dims = prune_segment(target)
            new_dim_keys = [d["dim"] for d in new_dims]
            dropped = set(old_dims) - set(new_dim_keys)
            status = f"{len(old_dims)}->{len(new_dims)}"
            if dropped:
                status += f" (dropped: {','.join(sorted(dropped))})"
            print(f"  [{target['file']}] seg {target['seg_idx']}: {status}")
            return key, new_dims
        except Exception as e:
            print(f"  [{target['file']}] seg {target['seg_idx']}: ERROR {e}")
            return key, target["dimensions"]

    if args.parallel > 1:
        with ThreadPoolExecutor(max_workers=args.parallel) as pool:
            futures = {pool.submit(process_one, t): t for t in all_targets}
            for future in as_completed(futures):
                key, new_dims = future.result()
                results[key] = new_dims
    else:
        for t in all_targets:
            key, new_dims = process_one(t)
            results[key] = new_dims

    elapsed = time.time() - start_time
    print(f"\nDone in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"Tokens: {total_input_tokens} in + {total_output_tokens} out")
    print(f"Cost: ${total_cost:.2f}")

    pruned_count = 0
    dims_removed = 0

    for fname, finfo in files_data.items():
        data = finfo["data"]
        changed = False
        for seg_idx, seg in enumerate(data.get("segments", [])):
            key = (fname, seg_idx)
            if key in results:
                old_count = len(seg["dimensions"])
                seg["dimensions"] = results[key]
                new_count = len(seg["dimensions"])
                if new_count < old_count:
                    pruned_count += 1
                    dims_removed += old_count - new_count
                    changed = True

        if changed:
            data["metadata"]["atomic_segments"] = len(data.get("segments", []))
            with finfo["path"].open("w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)

    print(f"\nSegments pruned: {pruned_count}/{len(all_targets)}")
    print(f"Dimension entries removed: {dims_removed}")


if __name__ == "__main__":
    main()
