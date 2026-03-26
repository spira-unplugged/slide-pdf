#!/usr/bin/env python3
"""
Marp CLI slide generator for slide-pdf skill.
Usage: python generate.py --input <slide.md> [--output <path>]
                          [--format pdf|pptx|html]
                          [--theme default|gaia|uncover]
                          [--pdf-outlines] [--pdf-notes]
                          [--math mathjax|katex|none]
                          [--size 16:9|4:3|9:16]
                          [--lint]
                          [--json]
"""

import argparse
import dataclasses
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import warnings
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger("slide-pdf")


def _setup_logging() -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("[slide-pdf] %(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Allow env-var override: CHROMIUM_PATH=/path/to/chrome python generate.py ...
CHROMIUM_PATH = os.environ.get(
    "CHROMIUM_PATH",
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
)
# Allow env-var override for deployment in different environments
ALLOWED_INPUT_BASE = Path(
    os.environ.get("ALLOWED_INPUT_BASE", "/mnt/user-data")
).resolve()
ALLOWED_OUTPUT_BASE = Path(
    os.environ.get("ALLOWED_OUTPUT_BASE", "/mnt/user-data/outputs")
).resolve()

SLIDES_PER_TIMEOUT_THRESHOLD = 20
TIMEOUT_SHORT = 60
TIMEOUT_LONG = 120
AUTO_OUTLINES_THRESHOLD = 5

# Cap frontmatter regex scans to prevent ReDoS on adversarial input.
# All helpers that scan frontmatter use this constant — keep them in sync.
MAX_FRONTMATTER_SCAN_BYTES = 65536
MAX_INPUT_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

VALID_FORMATS = {"pdf", "pptx", "html"}
VALID_THEMES = {"default", "gaia", "uncover"}
VALID_MATH_ENGINES = {"mathjax", "katex", "none"}
VALID_SIZES = {"16:9", "4:3", "9:16"}

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


# ---------------------------------------------------------------------------
# Startup validation
# ---------------------------------------------------------------------------

def _assert_allowed_bases() -> None:
    """Verify that the allowed base directories exist at startup.

    Fails fast with a clear error rather than letting path operations produce
    confusing results when the VM directories are not mounted.
    """
    for base in (ALLOWED_INPUT_BASE, ALLOWED_OUTPUT_BASE):
        if not base.exists():
            logger.error("Allowed base directory does not exist: %s", base)
            sys.exit(1)
        if not base.is_dir():
            logger.error("Allowed base path is not a directory: %s", base)
            sys.exit(1)


# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------

class PathSecurityError(ValueError):
    """Raised when a path escapes the allowed base directory."""


def safe_path(raw: str, allowed_base: Path) -> Path:
    """Resolve path and assert it is within the allowed base directory.

    Uses os.path.realpath() to resolve all symlinks before checking containment,
    preventing symlink-based traversal attacks. Raises PathSecurityError instead
    of calling sys.exit() so callers can handle errors gracefully.
    """
    resolved = Path(os.path.realpath(raw))
    real_base = Path(os.path.realpath(allowed_base))
    if not resolved.is_relative_to(real_base):
        raise PathSecurityError(
            f"Path outside allowed directory: {resolved} (allowed: {real_base})"
        )
    return resolved


# ---------------------------------------------------------------------------
# Pure helper functions (all testable without I/O)
# ---------------------------------------------------------------------------

def format_to_marp_flag(fmt: str) -> str:
    """Map format name to the corresponding Marp CLI flag."""
    if fmt not in VALID_FORMATS:
        raise ValueError(f"Unknown format: {fmt!r}. Valid: {', '.join(sorted(VALID_FORMATS))}")
    mapping = {"pdf": "--pdf", "pptx": "--pptx", "html": "--html"}
    return mapping[fmt]


def default_output_path(fmt: str) -> str:
    """Return the default output path for the given format."""
    if fmt not in VALID_FORMATS:
        raise ValueError(f"Unknown format: {fmt!r}. Valid: {', '.join(sorted(VALID_FORMATS))}")
    return f"/mnt/user-data/outputs/slides.{fmt}"


def should_inject_style(theme: str) -> bool:
    """Return True only when using the default theme (custom CSS needed)."""
    return theme == "default"


def should_auto_outlines(slide_count: int, threshold: int = AUTO_OUTLINES_THRESHOLD) -> bool:
    """Return True when slide count exceeds the threshold for auto-enabling PDF outlines."""
    return slide_count > threshold


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
    Fenced code blocks (```...```) are stripped before counting to avoid false
    positives from --- inside code examples.
    """
    # Normalise line endings before parsing
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # Cap body scan to avoid ReDoS on adversarial input
    body_content = content[:MAX_FRONTMATTER_SCAN_BYTES * 4]

    # Strip frontmatter: everything between the first pair of ---
    # Newlines are normalised to \n above — regex assumes \n only
    body = re.sub(r"^---\n.*?\n---\n?", "", body_content, count=1, flags=re.DOTALL)

    # Strip fenced code blocks to avoid counting --- inside code examples
    body = re.sub(r"```.*?```", "", body, flags=re.DOTALL)

    # Each remaining standalone --- is a slide separator
    separators = re.findall(r"^---\s*$", body, re.MULTILINE)
    # slides = separators + 1, minimum 1
    return max(1, len(separators) + 1)


def has_style_block(content: str) -> bool:
    """Check if frontmatter already contains a style: block."""
    # Normalise line endings
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    # Cap search to MAX_FRONTMATTER_SCAN_BYTES to avoid ReDoS on adversarial input
    frontmatter_match = re.match(
        r"^---\n(.*?)\n---", content[:MAX_FRONTMATTER_SCAN_BYTES], re.DOTALL
    )
    if not frontmatter_match:
        return False
    return "style:" in frontmatter_match.group(1)


def inject_style(content: str) -> str:
    """Inject default style into frontmatter if not present. Idempotent."""
    # Normalise line endings
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    if has_style_block(content):
        return content

    # Cap search to MAX_FRONTMATTER_SCAN_BYTES to avoid ReDoS
    match = re.match(r"^(---\n.*?\n)(---)", content[:MAX_FRONTMATTER_SCAN_BYTES], re.DOTALL)
    if not match:
        # No frontmatter — prepend minimal Marp frontmatter with style
        header = f"---\nmarp: true\nsize: 16:9\nstyle: |\n{DEFAULT_STYLE}\n---\n\n"
        return header + content

    frontmatter_body = match.group(1)
    style_block = f"style: |\n{DEFAULT_STYLE}\n"
    new_frontmatter = frontmatter_body + style_block + "---"
    return new_frontmatter + content[match.end():]


def has_math_block(content: str) -> bool:
    """Check if frontmatter already contains a math: key."""
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    frontmatter_match = re.match(
        r"^---\n(.*?)\n---", content[:MAX_FRONTMATTER_SCAN_BYTES], re.DOTALL
    )
    if not frontmatter_match:
        return False
    return "math:" in frontmatter_match.group(1)


def inject_math(content: str, engine: str = "mathjax") -> str:
    """Inject math: engine into frontmatter if not present. Idempotent."""
    _valid_engines = {"mathjax", "katex"}
    if engine not in _valid_engines:
        raise ValueError(f"Unknown math engine: {engine!r}. Valid: {', '.join(sorted(_valid_engines))}")
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    if has_math_block(content):
        return content

    match = re.match(r"^(---\n.*?\n)(---)", content[:MAX_FRONTMATTER_SCAN_BYTES], re.DOTALL)
    if not match:
        # No frontmatter — prepend minimal Marp frontmatter with math
        header = f"---\nmarp: true\nsize: 16:9\nmath: {engine}\n---\n\n"
        return header + content

    frontmatter_body = match.group(1)
    math_block = f"math: {engine}\n"
    new_frontmatter = frontmatter_body + math_block + "---"
    return new_frontmatter + content[match.end():]


def has_size_block(content: str) -> bool:
    """Check if frontmatter already contains a size: key."""
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    frontmatter_match = re.match(
        r"^---\n(.*?)\n---", content[:MAX_FRONTMATTER_SCAN_BYTES], re.DOTALL
    )
    if not frontmatter_match:
        return False
    return "size:" in frontmatter_match.group(1)


def inject_size(content: str, size: str = "16:9") -> str:
    """Inject size: directive into frontmatter if not present. Idempotent."""
    if size not in VALID_SIZES:
        raise ValueError(f"Unknown size: {size!r}. Valid: {', '.join(sorted(VALID_SIZES))}")
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    if has_size_block(content):
        return content

    match = re.match(r"^(---\n.*?\n)(---)", content[:MAX_FRONTMATTER_SCAN_BYTES], re.DOTALL)
    if not match:
        header = f"---\nmarp: true\nsize: {size}\n---\n\n"
        return header + content

    frontmatter_body = match.group(1)
    size_block = f"size: {size}\n"
    new_frontmatter = frontmatter_body + size_block + "---"
    return new_frontmatter + content[match.end():]


# ---------------------------------------------------------------------------
# Lint / validation
# ---------------------------------------------------------------------------

def lint_slides(content: str) -> tuple[bool, list[str]]:
    """Check slide structure without invoking Marp CLI.

    Returns (is_valid, list_of_issues). Issues are human-readable strings.
    An empty issue list means the file passed all checks.
    """
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    issues: list[str] = []

    fm_match = re.match(r"^---\n(.*?)\n---", content[:MAX_FRONTMATTER_SCAN_BYTES], re.DOTALL)
    if not fm_match:
        issues.append("Missing YAML frontmatter (expected --- ... --- block at start of file)")
        return False, issues

    fm = fm_match.group(1)

    if "marp: true" not in fm:
        issues.append("Frontmatter missing 'marp: true'")

    if "size:" not in fm:
        issues.append("Frontmatter missing 'size:' directive (recommended: size: 16:9)")

    has_cover = (
        "<!-- _class: cover -->" in content
        or "<!-- _class: lead -->" in content
    )
    if not has_cover:
        issues.append(
            "No cover slide found. Add <!-- _class: cover --> or <!-- _class: lead --> "
            "to the first slide"
        )

    slide_count = count_slides(content)
    if slide_count > 50:
        issues.append(
            f"High slide count ({slide_count}). Consider splitting into multiple files."
        )

    return len(issues) == 0, issues


# ---------------------------------------------------------------------------
# Chromium discovery
# ---------------------------------------------------------------------------

def _validate_chromium_path(path: str) -> str:
    """Validate that a Chromium path is absolute and resolves to an existing file."""
    resolved = Path(os.path.realpath(path))
    if not resolved.is_absolute():
        raise ValueError(f"CHROMIUM_PATH must be an absolute path: {path!r}")
    if not resolved.exists():
        raise FileNotFoundError(f"CHROMIUM_PATH does not exist: {resolved}")
    return str(resolved)


def find_chromium() -> str | None:
    """Find Chromium binary, falling back to system chrome.

    The primary candidate (CHROMIUM_PATH) is validated as an absolute path before use.
    Returns the resolved path of the first found binary, or None if nothing is found.
    """
    # Validate the env-var / default primary path before trusting it
    try:
        validated = _validate_chromium_path(CHROMIUM_PATH)
        logger.debug("Using Chromium from CHROMIUM_PATH: %s", validated)
        return validated
    except (ValueError, FileNotFoundError):
        pass

    # Fallback candidates: use glob to avoid hardcoding specific build numbers
    import glob
    playwright_candidates = sorted(
        glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"),
        reverse=True,  # prefer highest version number
    )
    system_candidates = [
        shutil.which("chromium-browser"),
        shutil.which("chromium"),
        shutil.which("google-chrome"),
    ]
    for path in playwright_candidates + system_candidates:
        if path and Path(path).exists():
            logger.debug("Using fallback Chromium: %s", path)
            return path
    return None


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class GenerationResult:
    """Structured result from generate_output()."""
    success: bool
    exit_code: int
    output_path: Path | None
    slide_count: int
    fmt: str
    warnings: tuple[str, ...]
    error: str | None
    duration_seconds: float

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "output_path": str(self.output_path) if self.output_path else None,
            "slide_count": self.slide_count,
            "format": self.fmt,
            "warnings": list(self.warnings),
            "error": self.error,
            "duration_seconds": round(self.duration_seconds, 3),
        }


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------

def _prepare_content(
    content: str,
    theme: str,
    math: str,
    size: str = "16:9",
) -> tuple[str, int]:
    """Apply style/math/size injection and return (modified_content, slide_count).

    Pure side-effect-free transformation — does not touch the filesystem.
    """
    if size != "16:9" and not has_size_block(content):
        content = inject_size(content, size)

    if should_inject_style(theme) and not has_style_block(content):
        logger.info("style: block not found — injecting default style")
        content = inject_style(content)

    if math != "none" and not has_math_block(content):
        logger.info("injecting math: %s into frontmatter", math)
        content = inject_math(content, engine=math)

    slide_count = count_slides(content)
    return content, slide_count


def _build_marp_cmd(
    tmp_path: str,
    chromium: str,
    output_path: Path,
    fmt: str,
    theme: str,
    slide_count: int,
    pdf_outlines: bool,
    pdf_notes: bool,
) -> list[str]:
    """Build the Marp CLI subprocess command list. Pure — no I/O.

    The timeout is handled by subprocess.run(timeout=N), not the timeout binary,
    so it is not included here.
    """
    cmd = [
        "npx", "@marp-team/marp-cli",
        "--",                        # end-of-options: prevents path being parsed as a flag
        tmp_path,
        "--no-stdin",
        format_to_marp_flag(fmt),    # --pdf / --pptx / --html
        "--browser", "chrome",
        "--browser-path", chromium,
    ]
    if theme != "default":
        cmd += ["--theme", theme]
    if fmt == "pdf":
        if pdf_outlines or should_auto_outlines(slide_count):
            cmd.append("--pdf-outlines")
        if pdf_notes:
            cmd.append("--pdf-notes")
    cmd += ["-o", str(output_path)]
    return cmd


def generate_output(
    input_path: Path,
    output_path: Path,
    fmt: str = "pdf",
    theme: str = "default",
    pdf_outlines: bool = False,
    pdf_notes: bool = False,
    math: str = "none",
    size: str = "16:9",
) -> GenerationResult:
    """Run Marp CLI to generate the requested output format.

    Always returns a GenerationResult — never raises on expected failure conditions.
    """
    start = time.monotonic()
    run_warnings: list[str] = []

    # --- Input size guard ---
    try:
        file_size = input_path.stat().st_size
    except OSError as exc:
        return GenerationResult(
            success=False, exit_code=1, output_path=None, slide_count=0,
            fmt=fmt, warnings=tuple(run_warnings),
            error=f"Cannot stat input file: {exc}",
            duration_seconds=time.monotonic() - start,
        )
    if file_size > MAX_INPUT_SIZE_BYTES:
        return GenerationResult(
            success=False, exit_code=1, output_path=None, slide_count=0,
            fmt=fmt, warnings=tuple(run_warnings),
            error=f"Input file too large ({file_size} bytes, max {MAX_INPUT_SIZE_BYTES})",
            duration_seconds=time.monotonic() - start,
        )

    content = input_path.read_text(encoding="utf-8")
    content, slide_count = _prepare_content(content, theme, math, size)

    timeout = TIMEOUT_LONG if slide_count > SLIDES_PER_TIMEOUT_THRESHOLD else TIMEOUT_SHORT
    logger.info("%d slides detected — timeout: %ds", slide_count, timeout)

    chromium = find_chromium()
    if not chromium:
        return GenerationResult(
            success=False, exit_code=1, output_path=None, slide_count=slide_count,
            fmt=fmt, warnings=tuple(run_warnings),
            error=(
                "Chromium not found. "
                "Install Playwright or set CHROMIUM_PATH environment variable."
            ),
            duration_seconds=time.monotonic() - start,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write temp file in a controlled subdirectory under ALLOWED_OUTPUT_BASE
    # to prevent TOCTOU races in an attacker-controlled TMPDIR.
    tmp_dir = ALLOWED_OUTPUT_BASE / ".slide-pdf-tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".md", dir=str(tmp_dir))
    try:
        # Two-stage open: handle fdopen failure without double-closing
        try:
            f = os.fdopen(tmp_fd, "w", encoding="utf-8")
        except Exception:
            os.close(tmp_fd)
            raise
        with f:
            f.write(content)

        cmd = _build_marp_cmd(
            tmp_path, chromium, output_path, fmt, theme,
            slide_count, pdf_outlines, pdf_notes,
        )
        logger.info(
            "Running marp-cli (input: %s, output: %s, format: %s)",
            str(input_path).replace("\n", "\\n"),
            str(output_path).replace("\n", "\\n"),
            fmt,
        )

        try:
            proc = subprocess.run(
                cmd,
                shell=False,
                stdin=subprocess.DEVNULL,
                timeout=timeout,
            )
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            logger.error(
                "Timed out after %ds. Slide count: %d. "
                "Try reducing slide count or splitting into parts.",
                timeout, slide_count,
            )
            return GenerationResult(
                success=False, exit_code=124, output_path=None,
                slide_count=slide_count, fmt=fmt, warnings=tuple(run_warnings),
                error=f"Timed out after {timeout}s",
                duration_seconds=time.monotonic() - start,
            )
        except (FileNotFoundError, OSError) as exc:
            logger.error("Failed to launch marp-cli: %s", exc)
            return GenerationResult(
                success=False, exit_code=1, output_path=None,
                slide_count=slide_count, fmt=fmt, warnings=tuple(run_warnings),
                error=f"Failed to launch marp-cli: {exc}",
                duration_seconds=time.monotonic() - start,
            )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if exit_code != 0:
        logger.error("marp-cli exited with code %d", exit_code)
        return GenerationResult(
            success=False, exit_code=exit_code, output_path=None,
            slide_count=slide_count, fmt=fmt, warnings=tuple(run_warnings),
            error=f"marp-cli exited with code {exit_code}",
            duration_seconds=time.monotonic() - start,
        )

    logger.info("%s generated: %s", fmt.upper(), output_path)
    return GenerationResult(
        success=True, exit_code=0, output_path=output_path,
        slide_count=slide_count, fmt=fmt, warnings=tuple(run_warnings),
        error=None,
        duration_seconds=time.monotonic() - start,
    )


def generate_pdf(input_path: Path, output_path: Path) -> int:
    """Backward-compatible wrapper — delegates to generate_output() with PDF defaults."""
    warnings.warn(
        "generate_pdf() is deprecated — use generate_output() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return generate_output(input_path, output_path, fmt="pdf").exit_code


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    _setup_logging()

    parser = argparse.ArgumentParser(description="Generate slides from Marp Markdown")
    parser.add_argument("--input", "-i", required=True, help="Input Markdown file path")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output file path (default: /mnt/user-data/outputs/slides.<format>)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=sorted(VALID_FORMATS),
        default="pdf",
        help="Output format (default: pdf)",
    )
    parser.add_argument(
        "--theme",
        choices=sorted(VALID_THEMES),
        default="default",
        help="Marp theme (default: default). Built-in: default, gaia, uncover",
    )
    parser.add_argument(
        "--pdf-outlines",
        action="store_true",
        help="Add PDF bookmarks/outlines (PDF only; auto-enabled for >5 slides)",
    )
    parser.add_argument(
        "--pdf-notes",
        action="store_true",
        help="Include speaker notes in PDF (PDF only)",
    )
    parser.add_argument(
        "--math",
        choices=sorted(VALID_MATH_ENGINES),
        default="none",
        help="Math rendering engine (default: none)",
    )
    parser.add_argument(
        "--size",
        choices=sorted(VALID_SIZES),
        default="16:9",
        help="Slide aspect ratio (default: 16:9)",
    )
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Validate slide structure without generating output. "
             "Exits 0 if valid, 1 if issues found.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON result to stdout (errors still go to stderr)",
    )
    args = parser.parse_args()

    # Startup: verify allowed base directories exist (skip in lint mode for flexibility)
    if not args.lint:
        _assert_allowed_bases()

    # Resolve and validate input path
    try:
        input_path = safe_path(args.input, ALLOWED_INPUT_BASE)
    except PathSecurityError as exc:
        logger.error("%s", exc)
        sys.exit(1)

    if not input_path.exists():
        logger.error("Input file not found: %s", input_path)
        sys.exit(1)

    if input_path.suffix.lower() not in {".md", ".markdown"}:
        logger.error(
            "Input must be a Markdown file (.md or .markdown): %s", input_path
        )
        sys.exit(1)

    # --- Lint mode ---
    if args.lint:
        content = input_path.read_text(encoding="utf-8")
        is_valid, issues = lint_slides(content)
        if args.json:
            print(json.dumps({"valid": is_valid, "issues": issues}, ensure_ascii=False))
        else:
            if is_valid:
                logger.info("OK — no issues found in %s", input_path)
            else:
                for issue in issues:
                    logger.warning("LINT: %s", issue)
        sys.exit(0 if is_valid else 1)

    # --- Generation mode ---
    try:
        raw_output = args.output if args.output is not None else default_output_path(args.format)
        output_path = safe_path(raw_output, ALLOWED_OUTPUT_BASE)
    except PathSecurityError as exc:
        logger.error("%s", exc)
        sys.exit(1)

    result = generate_output(
        input_path,
        output_path,
        fmt=args.format,
        theme=args.theme,
        pdf_outlines=args.pdf_outlines,
        pdf_notes=args.pdf_notes,
        math=args.math,
        size=args.size,
    )

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False))

    if result.error:
        logger.error("%s", result.error)

    sys.exit(result.exit_code)


if __name__ == "__main__":
    main()
