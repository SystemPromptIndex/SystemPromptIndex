#!/usr/bin/env python3
"""
Gemini 3.1 Pro Pre-Annotation — Anthropic Prompts Only (Direct Google API)
===========================================================================
Same per-dimension span-extraction pipeline as llm_preannotate_v3.py, but
calling Google's Gemini API directly (not via OpenRouter). Scope: the 9
Anthropic prompts in the paper (everything under company=Anthropic in
audit_prompts_filtered.json, excluding research_lead_agent.md).

Outputs land in data/gemini_preannotation_anthropic/ with the same JSON
structure as data/preannotation_v3_89/ — diffable span-for-span.

Usage:
  export GEMINI_API_KEY="AIzaSy..."
  python gemini_preannotate_anthropic.py --dry-run
  python gemini_preannotate_anthropic.py --parallel 3 --parallel-dims
  python gemini_preannotate_anthropic.py --resume
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

import llm_preannotate_v3 as lp

GEMINI_MODEL = "gemini-3.1-pro-preview"
GEMINI_PRICING = {"input": 2, "output": 12}   # $/M tokens, Google list price
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Gemini 3.1 Pro: 1M input, 64K output. Thinking + output share this budget.
# Set higher than Opus's 16K to leave room for thinking tokens.
GEMINI_MAX_OUTPUT_TOKENS = 32000

DATA_FILE = Path(__file__).parent.parent / "data" / "audit_prompts_filtered.json"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "gemini_preannotation_anthropic"

EXCLUDE_FILENAMES = {"research_lead_agent.md"}


def gemini_call(prompt_text: str, model: str = None,
                max_tokens: int = None,
                reasoning_effort: str = None) -> dict:
    """Call Google's direct Gemini API. Shape-compatible drop-in for
    llm_preannotate_v3.call_openrouter — returns the raw response JSON."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set!")

    model = model or GEMINI_MODEL
    # Strip OpenRouter-style "google/" prefix if present
    if model.startswith("google/"):
        model = model[len("google/"):]
    max_tokens = max_tokens or GEMINI_MAX_OUTPUT_TOKENS

    url = f"{GEMINI_BASE_URL}/{model}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            # thinkingBudget=-1 means dynamic/unlimited — closest to Opus's
            # reasoning.effort="high" semantics.
            "thinkingConfig": {"thinkingBudget": -1, "includeThoughts": False},
        },
    }

    for attempt in range(lp.MAX_RETRIES):
        try:
            resp = requests.post(url,
                                 headers={"Content-Type": "application/json"},
                                 json=payload, timeout=lp.API_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else 0
            if status in (429, 500, 502, 503) and attempt < lp.MAX_RETRIES - 1:
                wait = lp.RETRY_DELAY * (2 ** attempt)
                print(f"    ⏳ HTTP {status}, retrying in {wait}s "
                      f"(attempt {attempt+1}/{lp.MAX_RETRIES})...")
                time.sleep(wait)
            else:
                # Include response body for easier debugging
                body = e.response.text[:400] if e.response is not None else ""
                raise RuntimeError(f"HTTP {status}: {body}") from e
        except requests.exceptions.Timeout:
            if attempt < lp.MAX_RETRIES - 1:
                wait = lp.RETRY_DELAY * (2 ** attempt)
                print(f"    ⏳ Timeout, retrying in {wait}s "
                      f"(attempt {attempt+1}/{lp.MAX_RETRIES})...")
                time.sleep(wait)
            else:
                raise


def gemini_extract_response(resp_json: dict) -> tuple:
    """Drop-in for llm_preannotate_v3.extract_response — returns
    (output_text, reasoning_text, input_tokens, output_tokens)."""
    candidates = resp_json.get("candidates", [])
    if not candidates:
        return "", "", 0, 0
    cand = candidates[0]
    content = cand.get("content", {}) or {}
    parts = content.get("parts", []) or []
    # Aggregate all text parts that are NOT marked as thoughts.
    output_parts = []
    thinking_parts = []
    for p in parts:
        if "text" not in p:
            continue
        if p.get("thought"):
            thinking_parts.append(p["text"])
        else:
            output_parts.append(p["text"])
    output_text = "".join(output_parts)
    reasoning_text = "".join(thinking_parts)

    um = resp_json.get("usageMetadata", {}) or {}
    input_tokens = um.get("promptTokenCount", 0)
    # For cost purposes, output = generated text + thinking tokens (both billed)
    candidates_tokens = um.get("candidatesTokenCount", 0)
    thoughts_tokens = um.get("thoughtsTokenCount", 0)
    output_tokens = candidates_tokens + thoughts_tokens
    return output_text, reasoning_text, input_tokens, output_tokens


def find_anthropic_indices() -> list:
    with DATA_FILE.open("r", encoding="utf-8") as f:
        prompts = json.load(f)
    indices = []
    for i, p in enumerate(prompts):
        if p.get("company") != "Anthropic":
            continue
        if p.get("filename") in EXCLUDE_FILENAMES:
            continue
        indices.append(i)
    return indices


def main():
    parser = argparse.ArgumentParser(
        description="Gemini 3.1 Pro pre-annotation on Anthropic prompts (direct API)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show plan without calling API")
    parser.add_argument("--resume", action="store_true",
                        help="Skip prompts whose output file already has spans")
    parser.add_argument("--parallel", type=int, default=1,
                        help="Prompts to process concurrently (default: 1)")
    parser.add_argument("--parallel-dims", action="store_true",
                        help="Also parallelize 8 dimensions within each prompt")
    args = parser.parse_args()

    # Override the Opus/OpenRouter defaults baked into llm_preannotate_v3
    lp.MODEL = GEMINI_MODEL
    lp.MODEL_PRICING[GEMINI_MODEL] = GEMINI_PRICING
    lp.DATA_FILE = DATA_FILE
    lp.OUTPUT_DIR = OUTPUT_DIR
    lp.MAX_TOKENS = GEMINI_MAX_OUTPUT_TOKENS
    # Monkey-patch API functions so all of llm_preannotate_v3's pipeline
    # (extract_dimension_spans, run_batch, …) routes through Google directly.
    lp.call_openrouter = gemini_call
    lp.extract_response = gemini_extract_response

    if not GEMINI_API_KEY and not args.dry_run:
        print("ERROR: GEMINI_API_KEY not set in environment.")
        sys.exit(1)

    indices = find_anthropic_indices()
    print(f"Anthropic prompts to process: {len(indices)}")
    print(f"Indices: {indices}")
    print(f"Model: {lp.MODEL} (direct Google API)")
    print(f"Output dir: {lp.OUTPUT_DIR}")
    print(f"Max output tokens: {lp.MAX_TOKENS}")
    print()

    lp.run_batch(indices,
                 resume=args.resume,
                 dry_run=args.dry_run,
                 parallel=args.parallel,
                 parallel_dims=args.parallel_dims)


if __name__ == "__main__":
    main()
