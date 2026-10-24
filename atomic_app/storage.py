from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_DATA: dict[str, dict[str, Any]] = {"subjects": {}, "logs": {}}


def _default_data() -> dict[str, dict[str, Any]]:
    return {"subjects": {}, "logs": {}}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return default


def _safe_done(value: Any) -> float:
    try:
        done = float(value)
    except (TypeError, ValueError):
        done = 0.0
    return round(max(0.0, min(done, 100.0)), 2)


def _slugify(name: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "subject"


def ensure_environment(base_path: Path) -> None:
    subjects_dir = base_path / "subjects"
    subjects_dir.mkdir(parents=True, exist_ok=True)
    data_file = base_path / "atomic.json"
    if not data_file.exists():
        data_file.write_text(json.dumps(_default_data(), indent=2, sort_keys=True), encoding="utf-8")


def load_data(base_path: Path) -> dict[str, dict[str, Any]]:
    ensure_environment(base_path)
    data_file = base_path / "atomic.json"

    try:
        raw = json.loads(data_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _default_data()

    if not isinstance(raw, dict):
        return _default_data()

    normalized = _default_data()

    subjects = raw.get("subjects", {})
    if isinstance(subjects, dict):
        for subject_key, payload in subjects.items():
            if not isinstance(subject_key, str) or not isinstance(payload, dict):
                continue
            name = str(payload.get("Name", subject_key))
            normalized["subjects"][subject_key] = {
                "Name": name,
                "Time_spent": _safe_int(payload.get("Time_spent", 0)),
                "md_link": str(payload.get("md_link", f"subjects/{_slugify(name)}.md")),
                "done": _safe_done(payload.get("done", 0.0)),
            }

    logs = raw.get("logs", {})
    if isinstance(logs, dict):
        for date_key, day_payload in logs.items():
            if not isinstance(date_key, str) or not isinstance(day_payload, dict):
                continue
            day: dict[str, int] = {}
            for subject_key, minutes in day_payload.items():
                if not isinstance(subject_key, str):
                    continue
                day[subject_key] = _safe_int(minutes)
            normalized["logs"][date_key] = day

    return normalized


def save_data(base_path: Path, data: dict[str, dict[str, Any]]) -> None:
    ensure_environment(base_path)
    target = base_path / "atomic.json"
    payload = json.dumps(data, indent=2, sort_keys=True)

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=base_path, prefix=".atomic_tmp_", delete=False
    ) as handle:
        handle.write(payload)
        handle.flush()
        temp_name = handle.name

    Path(temp_name).replace(target)


def add_session(base_path: Path, date_key: str, subject: str | None, minutes: int) -> dict[str, dict[str, Any]]:
    data = load_data(base_path)
    safe_minutes = max(math.floor(minutes), 0)

    day_logs = data["logs"].setdefault(date_key, {})
    log_key = subject if subject else "null"
    day_logs[log_key] = _safe_int(day_logs.get(log_key, 0)) + safe_minutes

    if subject:
        entry = data["subjects"].get(subject)
        if not entry:
            entry = {
                "Name": subject,
                "Time_spent": 0,
                "md_link": f"subjects/{_slugify(subject)}.md",
                "done": 0.0,
            }
            data["subjects"][subject] = entry
        entry["Time_spent"] = _safe_int(entry.get("Time_spent", 0)) + safe_minutes

    save_data(base_path, data)
    return data
