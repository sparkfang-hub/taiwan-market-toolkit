"""Fail when repository Markdown references missing local documentation files.

The checker intentionally ignores external URLs and in-page anchors. It validates
normal Markdown links plus backticked ``*.md`` path references outside fenced code
blocks, which catches documentation-path drift such as case-only renames on the
Linux CI filesystem.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
BACKTICK_MARKDOWN_PATH = re.compile(r"`([^`\n]*\.md(?:#[^`\s]+)?)`")
FENCE = re.compile(r"^\s*(```|~~~)")
EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel"}


def _text_outside_fences(text: str) -> str:
    kept: list[str] = []
    fence_marker: str | None = None
    for line in text.splitlines():
        match = FENCE.match(line)
        if match:
            marker = match.group(1)
            if fence_marker is None:
                fence_marker = marker
            elif marker == fence_marker:
                fence_marker = None
            continue
        if fence_marker is None:
            kept.append(line)
    return "\n".join(kept)


def _strip_markdown_title(target: str) -> str:
    target = target.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    if " " in target:
        return target.split(None, 1)[0]
    return target


def _candidate_paths(source: Path, raw_target: str) -> list[Path]:
    target = _strip_markdown_title(raw_target)
    if not target or target.startswith("#"):
        return []

    parsed = urlsplit(target)
    if parsed.scheme.lower() in EXTERNAL_SCHEMES or parsed.netloc:
        return []

    path_text = unquote(parsed.path)
    if not path_text:
        return []

    candidate = Path(path_text)
    if candidate.is_absolute():
        return [ROOT / str(candidate).lstrip("/\\")]

    candidates = [source.parent / candidate]
    root_candidate = ROOT / candidate
    if root_candidate not in candidates:
        candidates.append(root_candidate)
    return candidates


def _display(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def main() -> int:
    failures: list[str] = []
    markdown_files = sorted(
        path for path in ROOT.rglob("*.md") if ".git" not in path.parts
    )

    for source in markdown_files:
        text = _text_outside_fences(source.read_text(encoding="utf-8"))
        targets: list[tuple[str, str]] = []
        targets.extend(("link", match.group(1)) for match in MARKDOWN_LINK.finditer(text))
        targets.extend(
            ("path reference", match.group(1))
            for match in BACKTICK_MARKDOWN_PATH.finditer(text)
        )

        seen: set[tuple[str, str]] = set()
        for kind, raw_target in targets:
            key = (kind, raw_target)
            if key in seen:
                continue
            seen.add(key)
            candidates = _candidate_paths(source, raw_target)
            if not candidates:
                continue
            if any(candidate.exists() for candidate in candidates):
                continue
            checked = ", ".join(_display(candidate) for candidate in candidates)
            failures.append(
                f"{_display(source)}: missing local {kind} {raw_target!r} "
                f"(checked: {checked})"
            )

    if failures:
        print("Broken local Markdown references found:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"Checked {len(markdown_files)} Markdown files; local references are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
