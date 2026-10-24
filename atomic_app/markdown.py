from __future__ import annotations

import re
from pathlib import Path

HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
CHECKBOX_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s+.+$", re.MULTILINE)


def parse_subject_markdown(path: Path) -> tuple[str | None, float, int, int]:
    content = path.read_text(encoding="utf-8")

    heading_match = HEADING_RE.search(content)
    heading = heading_match.group(1).strip() if heading_match else None

    matches = CHECKBOX_RE.findall(content)
    total = len(matches)
    completed = sum(1 for mark in matches if mark.lower() == "x")
    done = round((completed / total) * 100, 2) if total else 0.0

    return heading, done, completed, total
