from __future__ import annotations

from typing import Any


def format_minutes(minutes: int) -> str:
    safe = max(int(minutes), 0)
    hours, mins = divmod(safe, 60)
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"


def progress_bar(percent: float, width: int = 20) -> str:
    clamped = max(0.0, min(float(percent), 100.0))
    filled = int(round((clamped / 100.0) * width))
    return "█" * filled + "░" * (width - filled)


def render_progress_all(subjects: dict[str, dict[str, Any]]) -> str:
    if not subjects:
        return "No subjects found. Add markdown files in subjects/ and run `atomic refresh`."

    lines = []
    for _, entry in sorted(subjects.items(), key=lambda item: item[0].lower()):
        name = entry.get("Name", "Unknown")
        done = float(entry.get("done", 0.0))
        spent = int(entry.get("Time_spent", 0))
        lines.append(f"{name:<18} {progress_bar(done, 24)} {done:6.2f}%  {format_minutes(spent)}")
    return "\n".join(lines)


def render_progress_subject(entry: dict[str, Any]) -> str:
    name = entry.get("Name", "Unknown")
    done = float(entry.get("done", 0.0))
    spent = int(entry.get("Time_spent", 0))
    return f"{name}\n{progress_bar(done, 28)} {done:.2f}%\nTotal time: {format_minutes(spent)}"


def render_today(day_logs: dict[str, int]) -> str:
    if not day_logs:
        return "No work logged for today yet."

    lines = []
    total = 0
    for subject, minutes in sorted(day_logs.items(), key=lambda item: item[0].lower()):
        safe_minutes = max(int(minutes), 0)
        total += safe_minutes
        label = "Unassigned" if subject == "null" else subject
        lines.append(f"{label:<18} {format_minutes(safe_minutes)}")

    lines.append("")
    lines.append(f"{'Total':<18} {format_minutes(total)}")
    return "\n".join(lines)
