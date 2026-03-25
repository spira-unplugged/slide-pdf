#!/usr/bin/env python3
"""
Marp CLI PDF generator for slide-pdf skill.
Usage: python generate.py --input <slide.md> [--output <slides.pdf>]
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Allow env-var override: CHROMIUM_PATH=/path/to/chrome python generate.py ...
CHROMIUM_PATH = os.environ.get(
    "CHROMIUM_PATH",
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
)
DEFAULT_OUTPUT = "/mnt/user-data/outputs/slides.pdf"
ALLOWED_INPUT_BASE = Path("/mnt/user-data").resolve()
ALLOWED_OUTPUT_BASE = Path("/mnt/user-data/outputs").resolve()
SLIDES_PER_TIMEOUT_THRESHOLD = 20
TIMEOUT_SHORT = 60
TIMEOUT_LONG = 120

DEFAULT_STYLE = """\
  section {
    position: relative;
    overflow: hidden;
    font-family: "Noto Sans CJK JP", "Noto Sans JP", "Meiryo", sans-serif;
    color: #10324a;
    background: #ffffff;
    padding: calc(54px + 28px) 72px calc(54px + 46px) 72px;
  }
  section h1, section h2, section h3 { color: #0f3652; margin: 0 0 0.35em; }
  section h1 { font-size: 2em; }
  section h2 { font-size: 1.34em; border-left: 8px solid #0aa7ad; padding-left: 0.4em; }
  section p, section li { font-size: 0.94em; line-height: 1.42; }
  section ul, section ol { padding-left: 1.05em; margin: 0.25em 0 0.45em; }
  section li + li { margin-top: 0.18em; }
  section p { margin: 0.2em 0 0.45em; }
  section strong { color: #007e92; }
  section code { background: rgba(13,141,216,0.08); border-radius: 6px; padding: 0.12em 0.35em; }
  section blockquote { margin: 1em 0; padding: 0.5em 0.9em; border-left: 6px solid #0aa7ad; background: rgba(8,180,160,0.08); }
  section table { width: 100%; border-collapse: collapse; background: white; }
  section th, section td { padding: 0.5em 0.7em; border: 1px solid #d8e8ef; }
  section th { background: #eaf8fb; }
  section header, section footer { position: absolute; left: 72px; right: 72px; font-size: 0.58em; }
  section header { top: 18px; }
  section footer { bottom: 18px; }
  section.lead, section.cover {
    color: #ffffff;
    background: linear-gradient(90deg, #0d8dd8 0%, #08b4a0 100%);
  }
  section.lead h1, section.cover h1,
  section.lead h2, section.cover h2,
  section.lead h3, section.cover h3,
  section.lead p, section.cover p,
  section.lead li, section.cover li,
  section.lead strong, section.cover strong,
  section.lead header, section.cover header,
  section.lead footer, section.cover footer { color: #ffffff; }
  section.lead h1, section.cover h1 { margin-top: 0.8em; font-size: 1.9em; line-height: 1.25; max-width: 90%; }
  section.lead p, section.cover p { max-width: 90%; }
  section.lead footer, section.cover footer { position: absolute; left: 72px; right: 72px; bottom: 22px; font-size: 0.52em; color: rgba(255,255,255,0.78); }
  section.lead strong, section.cover strong, section.chapter strong { color: #c8fff1; }
  section.lead code, section.cover code, section.chapter code { color: #ffffff; background: rgba(255,255,255,0.14); }
  section.lead header, section.cover header { position: absolute; top: 42px; left: 72px; display: inline-block; padding: 0.22em 0.6em; color: #0d6078; background: white; border-radius: 4px; font-size: 0.66em; font-weight: 700; letter-spacing: 0.04em; }
  section.lead h1::after, section.cover h1::after { content: ""; display: block; width: 45%; height: 2px; margin-top: 0.45em; background: rgba(255,255,255,0.75); }
  section.chapter {
    color: #ffffff;
    background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0)),
                linear-gradient(90deg, #0f7fca 0%, #0fbea6 100%);
    padding-top: calc(54px + 8px);
    padding-bottom: calc(54px + 28px);
  }
  section.chapter h1, section.chapter h2, section.chapter h3,
  section.chapter p, section.chapter li,
  section.chapter header, section.chapter footer { color: #ffffff; }
  section.chapter h2 { border-left-color: rgba(255,255,255,0.55); }
  section.chapter header, section.chapter footer { color: rgba(255,255,255,0.9); }
  section.chapter h1 { max-width: 90%; }
  section.artifacts-with-image p,
  section.artifacts-with-image ul,
  section.artifacts-with-image ol { max-width: 58%; }
  section.artifacts-with-image .artifacts-shot {
    position: absolute; top: 108px; right: 56px; width: 34%;
    border-radius: 18px; border: 1px solid rgba(16,50,74,0.12);
    box-shadow: 0 14px 30px rgba(16,50,74,0.16);
  }"""


def safe_path(raw: str, allowed_base: Path) -> Path:
    """Resolve path and assert it is within the allowed base directory."""
    resolved = Path(raw).resolve()
    if not str(resolved).startswith(str(allowed_base)):
        print(
            f"[slide-pdf] ERROR: Path outside allowed directory: {resolved}",
            file=sys.stderr,
        )
        sys.exit(1)
    return resolved


def count_slides(content: str) -> int:
    """Count the number of slides by counting body-level --- separators.

    Marp files have the structure:
        --- (frontmatter open)
        ...frontmatter...
        --- (frontmatter close / first separator)
        # Slide 1
        --- (slide break)
        # Slide 2

    We split on frontmatter boundaries first, then count slide breaks in the body.
    """
    # Normalise line endings before parsing
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # Strip frontmatter: everything between the first pair of ---
    body = re.sub(r"^---\n.*?\n---\n?", "", content, count=1, flags=re.DOTALL)

    # Each remaining standalone --- is a slide separator
    separators = re.findall(r"^---\s*$", body, re.MULTILINE)
    # slides = separators + 1, minimum 1
    return max(1, len(separators) + 1)


def has_style_block(content: str) -> bool:
    """Check if frontmatter already contains a style: block."""
    # Normalise line endings
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    # Cap search to first 64 KB to avoid ReDoS on adversarial input
    frontmatter_match = re.match(r"^---\n(.*?)\n---", content[:65536], re.DOTALL)
    if not frontmatter_match:
        return False
    return "style:" in frontmatter_match.group(1)


def inject_style(content: str) -> str:
    """Inject default style into frontmatter if not present. Idempotent."""
    # Normalise line endings
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    if has_style_block(content):
        return content

    # Cap search to first 64 KB to avoid ReDoS
    match = re.match(r"^(---\n.*?\n)(---)", content[:65536], re.DOTALL)
    if not match:
        # No frontmatter — prepend minimal Marp frontmatter with style
        header = f"---\nmarp: true\nsize: 16:9\nstyle: |\n{DEFAULT_STYLE}\n---\n\n"
        return header + content

    frontmatter_body = match.group(1)
    style_block = f"style: |\n{DEFAULT_STYLE}\n"
    new_frontmatter = frontmatter_body + style_block + "---"
    return new_frontmatter + content[match.end():]


def find_chromium() -> str | None:
    """Find Chromium binary, falling back to system chrome."""
    candidates = [
        CHROMIUM_PATH,
        "/opt/pw-browsers/chromium-1161/chrome-linux/chrome",
        shutil.which("chromium-browser"),
        shutil.which("chromium"),
        shutil.which("google-chrome"),
    ]
    for path in candidates:
        if path and Path(path).exists():
            return path
    return None


def generate_pdf(input_path: Path, output_path: Path) -> int:
    """Run Marp CLI to generate PDF. Returns exit code."""
    content = input_path.read_text(encoding="utf-8")

    # Inject style if missing — write to a temp file, never modify the source
    needs_injection = not has_style_block(content)
    if needs_injection:
        print("[slide-pdf] style: block not found — injecting default style", file=sys.stderr)
        content = inject_style(content)

    # Count slides to pick timeout
    slide_count = count_slides(content)
    timeout = TIMEOUT_LONG if slide_count > SLIDES_PER_TIMEOUT_THRESHOLD else TIMEOUT_SHORT
    print(f"[slide-pdf] {slide_count} slides detected — timeout: {timeout}s", file=sys.stderr)

    # Find Chromium
    chromium = find_chromium()
    if not chromium:
        print(
            "[slide-pdf] ERROR: Chromium not found. "
            "Install Playwright or set CHROMIUM_PATH environment variable.",
            file=sys.stderr,
        )
        return 1

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file (avoids in-place mutation of the source file)
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".md")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content)

        cmd = [
            "timeout", str(timeout),
            "npx", "@marp-team/marp-cli",
            "--",                    # end-of-options: prevents path being parsed as a flag
            tmp_path,
            "--no-stdin", "--pdf",
            "--browser", "chrome",
            "--browser-path", chromium,
            "-o", str(output_path),
        ]

        print(f"[slide-pdf] Running marp-cli (input: {input_path}, output: {output_path})", file=sys.stderr)
        result = subprocess.run(cmd)

    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if result.returncode == 124:
        print(
            f"[slide-pdf] ERROR: Timed out after {timeout}s. "
            f"Slide count: {slide_count}. Try reducing slide count or splitting into parts.",
            file=sys.stderr,
        )
    elif result.returncode != 0:
        print(f"[slide-pdf] ERROR: marp-cli exited with code {result.returncode}", file=sys.stderr)
    else:
        print(f"[slide-pdf] PDF generated: {output_path}", file=sys.stderr)

    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PDF slides from Marp Markdown")
    parser.add_argument("--input", "-i", required=True, help="Input Markdown file path")
    parser.add_argument(
        "--output", "-o", default=DEFAULT_OUTPUT, help=f"Output PDF path (default: {DEFAULT_OUTPUT})"
    )
    args = parser.parse_args()

    input_path = safe_path(args.input, ALLOWED_INPUT_BASE)
    output_path = safe_path(args.output, ALLOWED_OUTPUT_BASE)

    if not input_path.exists():
        print(f"[slide-pdf] ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if input_path.suffix.lower() not in {".md", ".markdown"}:
        print(f"[slide-pdf] ERROR: Input must be a Markdown file (.md or .markdown): {input_path}", file=sys.stderr)
        sys.exit(1)

    exit_code = generate_pdf(input_path, output_path)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
