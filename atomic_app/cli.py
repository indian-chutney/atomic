from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from atomic_app.formatting import render_progress_all, render_progress_subject, render_today
from atomic_app.refresh import refresh_subjects
from atomic_app.storage import load_data
from atomic_app.timer_ui import run_timer


def _find_subject(subjects: dict[str, dict[str, object]], name: str) -> dict[str, object] | None:
    lowered = name.lower()
    for key, payload in subjects.items():
        if key.lower() == lowered:
            return payload
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="atomic", description="Atomic productivity timer CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("timer", help="Open the interactive timer")
    sub.add_parser("today", help="Show today's logged work")

    progress = sub.add_parser("progress", help="Show subject progress")
    progress.add_argument("subject", nargs="?", help="Subject name")

    sub.add_parser("refresh", help="Refresh subjects from markdown files")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    base_path = Path.cwd()

    if args.command == "timer":
        return run_timer(base_path)

    if args.command == "refresh":
        result = refresh_subjects(base_path)
        print(f"Added: {len(result.added)}, Updated: {len(result.updated)}, Removed: {len(result.removed)}")
        for name, path in result.collisions:
            print(f"Skipped duplicate subject name '{name}' from {path} (first discovered file wins).")
        return 0

    data = load_data(base_path)

    if args.command == "today":
        today = dt.date.today().isoformat()
        day_logs = data["logs"].get(today, {})
        print(render_today(day_logs))
        return 0

    if args.command == "progress":
        subjects = data["subjects"]
        if not args.subject:
            print(render_progress_all(subjects))
            return 0

        match = _find_subject(subjects, args.subject)
        if not match:
            print(f"Unknown subject: {args.subject}")
            return 1

        print(render_progress_subject(match))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
