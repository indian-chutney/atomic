from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from atomic_app.markdown import parse_subject_markdown
from atomic_app.storage import load_data, save_data


@dataclass
class RefreshResult:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    collisions: list[tuple[str, str]] = field(default_factory=list)


def refresh_subjects(base_path: Path) -> RefreshResult:
    data = load_data(base_path)
    subjects_dir = base_path / "subjects"
    subjects_dir.mkdir(parents=True, exist_ok=True)

    existing = data.get("subjects", {})
    existing_by_link = {
        str(payload.get("md_link")): payload
        for payload in existing.values()
        if isinstance(payload, dict) and isinstance(payload.get("md_link"), str)
    }

    discovered: dict[str, dict[str, object]] = {}
    seen_names: set[str] = set()
    result = RefreshResult()

    for file_path in sorted(subjects_dir.rglob("*.md")):
        heading, done, _, _ = parse_subject_markdown(file_path)
        name = heading or file_path.stem
        rel_link = file_path.relative_to(base_path).as_posix()

        if name in seen_names:
            result.collisions.append((name, rel_link))
            continue

        previous = existing.get(name)
        if not previous:
            previous = existing_by_link.get(rel_link, {})

        time_spent = int(previous.get("Time_spent", 0)) if isinstance(previous, dict) else 0
        discovered[name] = {
            "Name": name,
            "Time_spent": max(time_spent, 0),
            "md_link": rel_link,
            "done": round(done, 2),
        }
        seen_names.add(name)

        if name in existing:
            result.updated.append(name)
        else:
            result.added.append(name)

    old_names = set(existing.keys())
    new_names = set(discovered.keys())
    result.removed = sorted(old_names - new_names)

    data["subjects"] = discovered
    save_data(base_path, data)
    return result
