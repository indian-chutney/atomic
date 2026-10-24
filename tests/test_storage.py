import json
from pathlib import Path

from atomic_app.storage import add_session, load_data, save_data


def test_load_data_handles_malformed_json(tmp_path: Path) -> None:
    (tmp_path / "subjects").mkdir()
    (tmp_path / "atomic.json").write_text("{bad json", encoding="utf-8")

    data = load_data(tmp_path)
    assert data == {"subjects": {}, "logs": {}}


def test_add_session_aggregates_and_uses_null_key(tmp_path: Path) -> None:
    save_data(tmp_path, {"subjects": {"Python": {"Name": "Python", "Time_spent": 0, "md_link": "subjects/python.md", "done": 0.0}}, "logs": {}})

    add_session(tmp_path, "2026-10-24", "Python", 30)
    add_session(tmp_path, "2026-10-24", "Python", 45)
    add_session(tmp_path, "2026-10-24", None, 15)

    data = json.loads((tmp_path / "atomic.json").read_text(encoding="utf-8"))
    assert data["logs"]["2026-10-24"]["Python"] == 75
    assert data["logs"]["2026-10-24"]["null"] == 15
    assert data["subjects"]["Python"]["Time_spent"] == 75
