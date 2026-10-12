#!/usr/bin/env python3
"""
Interactive helper to rescore Misc spans in merged_all_annotations.json.

Usage:
  python review_tool/rescore_misc.py
  python review_tool/rescore_misc.py --file /path/to/merged_all_annotations.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


DEFAULT_MERGED_FILE = (
    Path(__file__).resolve().parent.parent
    / "annotation_tool_89"
    / "outputs"
    / "final_result"
    / "analysis"
    / "merged_all_annotations.json"
)

VALID_DIMENSIONS = {"D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "Misc"}
VALID_SCORES = {-1, 0, 1}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactively rescore spans currently labeled as Misc."
    )
    parser.add_argument(
        "--file",
        default=str(DEFAULT_MERGED_FILE),
        help="Path to merged_all_annotations.json",
    )
    parser.add_argument(
        "--backup-dir",
        default=None,
        help="Optional directory for backup file (default: same directory as target file).",
    )
    return parser.parse_args()


def _ask_dimension(current: str) -> str:
    while True:
        raw = input(f"  New dimension [{current}] (D1-D8 or Misc): ").strip()
        if not raw:
            return current
        normalized = raw.upper()
        if normalized in VALID_DIMENSIONS:
            return normalized
        print("  Invalid dimension. Please enter D1-D8 or Misc.")


def _ask_score(current: int) -> int:
    while True:
        raw = input(f"  New score [{current}] (-1 / 0 / 1): ").strip()
        if not raw:
            return current
        try:
            score = int(raw)
        except ValueError:
            print("  Invalid score. Please enter -1, 0, or 1.")
            continue
        if score in VALID_SCORES:
            return score
        print("  Invalid score. Please enter -1, 0, or 1.")


def _ask_note(current: str) -> str:
    raw = input("  New note [keep current, '-' to clear]: ").strip()
    if not raw:
        return current
    if raw == "-":
        return ""
    return raw


def _make_backup(target: Path, backup_dir: Path | None) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{target.stem}.backup_{stamp}{target.suffix}"
    out_dir = backup_dir if backup_dir is not None else target.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    backup_path = out_dir / backup_name
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def main() -> None:
    args = parse_args()
    merged_path = Path(args.file).resolve()
    if not merged_path.exists():
        raise FileNotFoundError(f"File not found: {merged_path}")

    data = json.loads(merged_path.read_text(encoding="utf-8"))
    prompts = data.get("prompts", {})

    targets: list[tuple[str, dict]] = []
    for prompt_id, prompt_data in prompts.items():
        for span in prompt_data.get("kept_spans", []):
            if span.get("dimension") == "Misc":
                targets.append((prompt_id, span))

    if not targets:
        print("No Misc spans found. Nothing to update.")
        return

    print(f"Found {len(targets)} Misc spans.\n")
    print("Press Enter to keep current value.\n")

    changed = 0
    for idx, (prompt_id, span) in enumerate(targets, start=1):
        print("=" * 80)
        print(f"[{idx}/{len(targets)}] {prompt_id}")
        print(f"Range: {span.get('start')} - {span.get('end')}")
        print(f"Current dimension: {span.get('dimension')}")
        print(f"Current score: {span.get('score')}")
        print("Text:")
        print(span.get("text", ""))
        print(f"Current note: {span.get('note', '')}")

        new_dimension = _ask_dimension(span.get("dimension", "Misc"))
        new_score = _ask_score(int(span.get("score", 0)))
        new_note = _ask_note(span.get("note", ""))

        if (
            new_dimension != span.get("dimension")
            or new_score != span.get("score")
            or new_note != span.get("note", "")
        ):
            span["dimension"] = new_dimension
            span["score"] = new_score
            span["note"] = new_note
            span["reviewed"] = True
            changed += 1

        print()

    if changed == 0:
        print("No changes made.")
        return

    backup_dir = Path(args.backup_dir).resolve() if args.backup_dir else None
    backup_path = _make_backup(merged_path, backup_dir)
    merged_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("=" * 80)
    print(f"Updated spans: {changed}")
    print(f"Backup created: {backup_path}")
    print(f"Saved file: {merged_path}")


if __name__ == "__main__":
    main()
