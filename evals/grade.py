#!/usr/bin/env python3
"""
Code-based grader for slide-pdf Unit Evals (UE-1 through UE-7).
Runs deterministic checks against generate.py pure functions.

Usage: python evals/grade.py
"""

import json
import sys
from pathlib import Path

# Allow importing generate.py from project root
sys.path.insert(0, str(Path(__file__).parent.parent))
from generate import count_slides, has_style_block, inject_style


def run_evals() -> list[dict]:
    results = []

    def record(eval_id: str, name: str, passed: bool, detail: str = "") -> None:
        status = "PASS" if passed else "FAIL"
        results.append({"id": eval_id, "name": name, "status": status, "detail": detail})
        indicator = "+" if passed else "-"
        print(f"  [{indicator}] {eval_id} {name}: {status}" + (f" -- {detail}" if detail else ""))

    print("=== slide-pdf Unit Evals ===\n")

    # UE-1: count_slides — basic
    content = "---\nmarp: true\n---\n# Slide 1\n---\n# Slide 2\n---\n# Slide 3\n"
    result = count_slides(content)
    record("UE-1", "count_slides-basic", result == 3, f"got {result}, expected 3")

    # UE-2: count_slides — frontmatter only (single slide)
    content = "---\nmarp: true\n---\n# Single Slide\n"
    result = count_slides(content)
    record("UE-2", "count_slides-frontmatter-only", result == 1, f"got {result}, expected 1")

    # UE-3: has_style_block — True
    content = "---\nmarp: true\nstyle: |\n  section { color: red; }\n---\n# Slide\n"
    result = has_style_block(content)
    record("UE-3", "has_style_block-true", result is True, f"got {result}, expected True")

    # UE-4: has_style_block — False
    content = "---\nmarp: true\nsize: 16:9\n---\n# Slide\n"
    result = has_style_block(content)
    record("UE-4", "has_style_block-false", result is False, f"got {result}, expected False")

    # UE-5: inject_style — contains font and style block
    content = "---\nmarp: true\nsize: 16:9\n---\n# Slide\n"
    result = inject_style(content)
    contains_style = "style:" in result
    contains_font = "Noto Sans CJK JP" in result
    passed = contains_style and contains_font
    record("UE-5", "inject_style-contains-font", passed,
           f"style:{contains_style} font:{contains_font}")

    # UE-6: inject_style — no frontmatter
    content = "# Just a heading\n\nSome content\n"
    result = inject_style(content)
    contains_marp = "marp: true" in result
    contains_style = "style:" in result
    contains_font = "Noto Sans CJK JP" in result
    passed = contains_marp and contains_style and contains_font
    record("UE-6", "inject_style-no-frontmatter", passed,
           f"marp:{contains_marp} style:{contains_style} font:{contains_font}")

    # UE-7: inject_style — does NOT overwrite existing style
    content = "---\nmarp: true\nstyle: |\n  section { color: red; }\n---\n# Slide\n"
    result = inject_style(content)
    record("UE-7", "inject_style-no-overwrite", result == content,
           "content unchanged" if result == content else "content was modified")

    return results


def print_summary(results: list[dict]) -> int:
    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    failed = [r for r in results if r["status"] == "FAIL"]

    print(f"\n{'='*30}")
    print(f"Result: {passed}/{total} passed")

    if failed:
        print("\nFailed evals:")
        for r in failed:
            print(f"  [-] {r['id']} {r['name']}: {r['detail']}")
        return 1

    print("All unit evals passed.")
    return 0


def main() -> None:
    results = run_evals()
    exit_code = print_summary(results)

    # Write JSON report
    report_path = Path(__file__).parent / "grade_report.json"
    report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReport written to {report_path}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
