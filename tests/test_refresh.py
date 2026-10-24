import json
from pathlib import Path

from atomic_app.refresh import refresh_subjects
from atomic_app.storage import save_data


def test_refresh_creates_updates_and_removes_subjects_preserving_logs(tmp_path: Path) -> None:
    subjects_dir = tmp_path / "subjects"
    subjects_dir.mkdir()

    python_md = subjects_dir / "python.md"
    python_md.write_text("# Python\n- [x] Basics\n- [ ] OOP\n", encoding="utf-8")

    save_data(
        tmp_path,
        {
            "subjects": {
                "Old": {"Name": "Old", "Time_spent": 120, "md_link": "subjects/old.md", "done": 100.0},
                "Python": {"Name": "Python", "Time_spent": 60, "md_link": "subjects/python.md", "done": 0.0},
            },
            "logs": {"2026-10-24": {"Old": 120}},
        },
    )

    result = refresh_subjects(tmp_path)

    data = json.loads((tmp_path / "atomic.json").read_text(encoding="utf-8"))
    assert "Old" in result.removed
    assert data["logs"]["2026-10-24"]["Old"] == 120
    assert data["subjects"]["Python"]["Time_spent"] == 60
    assert data["subjects"]["Python"]["md_link"] == "subjects/python.md"
    assert data["subjects"]["Python"]["done"] == 50.0
