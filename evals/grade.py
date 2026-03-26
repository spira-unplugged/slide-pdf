#!/usr/bin/env python3
"""
Code-based grader for slide-pdf Unit Evals (UE-1 through UE-23).
Runs deterministic checks against generate.py pure functions.

Usage: python evals/grade.py
"""

import json
import sys
from pathlib import Path

# Allow importing generate.py from project root
sys.path.insert(0, str(Path(__file__).parent.parent))
from generate import (
    ALLOWED_INPUT_BASE,
    PathSecurityError,
    count_slides,
    default_output_path,
    format_to_marp_flag,
    has_math_block,
    has_size_block,
    has_style_block,
    inject_math,
    inject_size,
    inject_style,
    lint_slides,
    safe_path,
    should_auto_outlines,
    should_inject_style,
)


def run_evals() -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    def record(eval_id: str, name: str, passed: bool, detail: str = "") -> None:
        status = "PASS" if passed else "FAIL"
        results.append({"id": eval_id, "name": name, "status": status, "detail": detail})
        indicator = "+" if passed else "-"
        print(f"  [{indicator}] {eval_id} {name}: {status}" + (f" -- {detail}" if detail else ""))

    print("=== slide-pdf Unit Evals ===\n")

    # UE-1: count_slides — basic
    c1 = "---\nmarp: true\n---\n# Slide 1\n---\n# Slide 2\n---\n# Slide 3\n"
    n1 = count_slides(c1)
    record("UE-1", "count_slides-basic", n1 == 3, f"got {n1}, expected 3")

    # UE-2: count_slides — frontmatter only (single slide)
    c2 = "---\nmarp: true\n---\n# Single Slide\n"
    n2 = count_slides(c2)
    record("UE-2", "count_slides-frontmatter-only", n2 == 1, f"got {n2}, expected 1")

    # UE-3: has_style_block — True
    c3 = "---\nmarp: true\nstyle: |\n  section { color: red; }\n---\n# Slide\n"
    has3 = has_style_block(c3)
    record("UE-3", "has_style_block-true", has3 is True, f"got {has3}, expected True")

    # UE-4: has_style_block — False
    c4 = "---\nmarp: true\nsize: 16:9\n---\n# Slide\n"
    has4 = has_style_block(c4)
    record("UE-4", "has_style_block-false", has4 is False, f"got {has4}, expected False")

    # UE-5: inject_style — contains font and style block
    c5 = "---\nmarp: true\nsize: 16:9\n---\n# Slide\n"
    injected5 = inject_style(c5)
    has_style5 = "style:" in injected5
    has_font5 = "Noto Sans CJK JP" in injected5
    record("UE-5", "inject_style-contains-font", has_style5 and has_font5,
           f"style:{has_style5} font:{has_font5}")

    # UE-6: inject_style — no frontmatter
    c6 = "# Just a heading\n\nSome content\n"
    injected6 = inject_style(c6)
    has_marp6 = "marp: true" in injected6
    has_style6 = "style:" in injected6
    has_font6 = "Noto Sans CJK JP" in injected6
    record("UE-6", "inject_style-no-frontmatter", has_marp6 and has_style6 and has_font6,
           f"marp:{has_marp6} style:{has_style6} font:{has_font6}")

    # UE-7: inject_style — does NOT overwrite existing style
    c7 = "---\nmarp: true\nstyle: |\n  section { color: red; }\n---\n# Slide\n"
    injected7 = inject_style(c7)
    unchanged7 = injected7 == c7
    record("UE-7", "inject_style-no-overwrite", unchanged7,
           "content unchanged" if unchanged7 else "content was modified")

    # UE-8: format_to_marp_flag — pdf maps to --pdf
    flag8 = format_to_marp_flag("pdf")
    record("UE-8", "format_to_marp_flag-pdf", flag8 == "--pdf", f"got {flag8!r}, expected '--pdf'")

    # UE-9: default_output_path — pptx path contains .pptx
    path9 = default_output_path("pptx")
    has_ext9 = ".pptx" in path9
    record("UE-9", "default_output_path-pptx", has_ext9, f"got {path9!r}")

    # UE-10: should_inject_style — True for default theme
    inject10 = should_inject_style("default")
    record("UE-10", "should_inject_style-default", inject10 is True, f"got {inject10}, expected True")

    # UE-11: should_inject_style — False for gaia theme
    inject11 = should_inject_style("gaia")
    record("UE-11", "should_inject_style-gaia", inject11 is False, f"got {inject11}, expected False")

    # UE-12: should_auto_outlines — True above threshold (6 > 5)
    above12 = should_auto_outlines(6)
    below12 = should_auto_outlines(3)
    record("UE-12", "should_auto_outlines", above12 is True and below12 is False,
           f"count=6:{above12} count=3:{below12}")

    # UE-13: inject_math — adds math: mathjax when absent
    c13 = "---\nmarp: true\nsize: 16:9\n---\n# Slide\n"
    injected13 = inject_math(c13)
    has_math13 = "math: mathjax" in injected13
    record("UE-13", "inject_math-adds-mathjax", has_math13, f"math:mathjax present:{has_math13}")

    # UE-14: inject_math — does NOT overwrite existing math key
    c14 = "---\nmarp: true\nmath: katex\n---\n# Slide\n"
    injected14 = inject_math(c14)
    unchanged14 = injected14 == c14
    record("UE-14", "inject_math-no-overwrite", unchanged14,
           "content unchanged" if unchanged14 else "content was modified")

    # UE-15: safe_path — path traversal raises PathSecurityError
    # Note: os.path.realpath normalises ".." without following symlinks when the path
    # does not exist, so this covers the path-normalisation case. Symlink traversal
    # requires an on-disk integration test (not performed here).
    traversal_blocked = False
    try:
        safe_path("/mnt/user-data/../etc/passwd", ALLOWED_INPUT_BASE)
    except PathSecurityError:
        traversal_blocked = True
    # Any other exception (AttributeError, TypeError, etc.) propagates and fails the suite
    record("UE-15", "safe_path-traversal-blocked", traversal_blocked,
           "PathSecurityError raised" if traversal_blocked else "traversal was NOT blocked")

    # UE-16: count_slides — --- inside fenced code block does NOT count as separator
    c16 = (
        "---\nmarp: true\n---\n"
        "# Slide 1\n\n"
        "```yaml\n---\nkey: value\n---\n```\n\n"
        "---\n"
        "# Slide 2\n"
    )
    n16 = count_slides(c16)
    record("UE-16", "count_slides-skip-fenced-code", n16 == 2,
           f"got {n16}, expected 2 (--- in code block should not count)")

    # UE-17: should_auto_outlines — boundary: exactly at threshold (5) returns False
    at17 = should_auto_outlines(5)
    record("UE-17", "should_auto_outlines-boundary", at17 is False,
           f"count=5 (exactly at threshold): got {at17}, expected False")

    # UE-18: inject_math — katex engine
    c18 = "---\nmarp: true\nsize: 16:9\n---\n# Slide\n"
    injected18 = inject_math(c18, engine="katex")
    has_katex18 = "math: katex" in injected18
    record("UE-18", "inject_math-katex", has_katex18,
           f"math:katex present:{has_katex18}")

    # UE-19: format_to_marp_flag — invalid format raises ValueError
    invalid_fmt_raises = False
    try:
        format_to_marp_flag("docx")
    except ValueError:
        invalid_fmt_raises = True
    record("UE-19", "format_to_marp_flag-invalid-raises", invalid_fmt_raises,
           "ValueError raised" if invalid_fmt_raises else "no exception raised")

    # UE-20: inject_size — adds size: 4:3 when absent
    c20 = "---\nmarp: true\n---\n# Slide\n"
    injected20 = inject_size(c20, size="4:3")
    has_size20 = "size: 4:3" in injected20
    record("UE-20", "inject_size-adds-4x3", has_size20,
           f"size:4:3 present:{has_size20}")

    # UE-21: inject_size — does NOT overwrite existing size key
    c21 = "---\nmarp: true\nsize: 16:9\n---\n# Slide\n"
    injected21 = inject_size(c21, size="4:3")
    unchanged21 = injected21 == c21
    record("UE-21", "inject_size-no-overwrite", unchanged21,
           "content unchanged" if unchanged21 else "content was modified")

    # UE-22: has_size_block — True when present
    c22 = "---\nmarp: true\nsize: 16:9\n---\n# Slide\n"
    has22 = has_size_block(c22)
    record("UE-22", "has_size_block-true", has22 is True, f"got {has22}, expected True")

    # UE-23: lint_slides — valid slide passes
    c23_valid = (
        "---\nmarp: true\nsize: 16:9\n---\n"
        "<!-- _class: cover -->\n# Title\n"
        "---\n# Slide 2\n- Content\n"
    )
    valid23, issues23 = lint_slides(c23_valid)
    record("UE-23", "lint_slides-valid", valid23,
           f"issues: {issues23}" if not valid23 else "no issues")

    # UE-24: lint_slides — missing marp: true reported
    c24 = "---\nsize: 16:9\n---\n<!-- _class: cover -->\n# Title\n"
    valid24, issues24 = lint_slides(c24)
    has_marp_issue = any("marp" in i for i in issues24)
    record("UE-24", "lint_slides-missing-marp", not valid24 and has_marp_issue,
           f"valid:{valid24} issues:{issues24}")

    # UE-25: lint_slides — missing cover slide reported
    c25 = "---\nmarp: true\nsize: 16:9\n---\n# Slide 1\n---\n# Slide 2\n"
    valid25, issues25 = lint_slides(c25)
    has_cover_issue = any("cover" in i.lower() for i in issues25)
    record("UE-25", "lint_slides-missing-cover", not valid25 and has_cover_issue,
           f"valid:{valid25} issues:{issues25}")

    # UE-26: has_size_block — False when key is absent
    c26 = "---\nmarp: true\n---\n# Slide\n"
    has26 = has_size_block(c26)
    record("UE-26", "has_size_block-false", has26 is False, f"got {has26}, expected False")

    # UE-27: inject_size — no frontmatter path creates minimal header with size
    c27 = "# Just a heading\n\nSome content\n"
    injected27 = inject_size(c27, size="4:3")
    has_marp27 = "marp: true" in injected27
    has_size27 = "size: 4:3" in injected27
    record("UE-27", "inject_size-no-frontmatter", has_marp27 and has_size27,
           f"marp:{has_marp27} size:{has_size27}")

    # UE-28: lint_slides — size: missing produces [WARNING] advisory (non-blocking)
    c28 = "---\nmarp: true\n---\n<!-- _class: cover -->\n# Title\n"
    valid28, issues28 = lint_slides(c28)
    has_size_warn28 = any("[WARNING]" in i and "size" in i for i in issues28)
    record("UE-28", "lint_slides-size-advisory", valid28 and has_size_warn28,
           f"valid:{valid28} issues:{issues28}")

    # UE-29: lint_slides — cover directive inside code block does NOT satisfy cover check
    c29 = (
        "---\nmarp: true\nsize: 16:9\n---\n"
        "# Intro\n\n"
        "```markdown\n<!-- _class: cover -->\n# Example\n```\n"
        "---\n# Slide 2\n"
    )
    valid29, issues29 = lint_slides(c29)
    has_cover_issue29 = any("cover" in i.lower() for i in issues29)
    record("UE-29", "lint_slides-cover-in-code-block", not valid29 and has_cover_issue29,
           f"valid:{valid29} issues:{issues29}")

    # UE-30: has_style_block — no false positive from YAML value containing 'style:'
    c30 = "---\nmarp: true\ndescription: sets font-style: italic\n---\n# Slide\n"
    has30 = has_style_block(c30)
    record("UE-30", "has_style_block-no-false-positive", has30 is False,
           f"got {has30}, expected False (substring in value should not match)")

    # UE-31: has_math_block — no false positive from YAML value containing 'math:'
    c31 = "---\nmarp: true\ntitle: learn math: basics\n---\n# Slide\n"
    has31 = has_math_block(c31)
    record("UE-31", "has_math_block-no-false-positive", has31 is False,
           f"got {has31}, expected False")

    return results


def print_summary(results: list[dict[str, str]]) -> int:
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
