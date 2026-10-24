from atomic_app.formatting import format_minutes, render_progress_subject, render_today


def test_format_minutes() -> None:
    assert format_minutes(0) == "0m"
    assert format_minutes(60) == "1h"
    assert format_minutes(125) == "2h 5m"


def test_render_today_uses_unassigned_and_total() -> None:
    output = render_today({"Python": 90, "null": 30})
    assert "Unassigned" in output
    assert "Total" in output
    assert "2h" in output


def test_subject_progress_layout() -> None:
    output = render_progress_subject({"Name": "Python", "done": 50.0, "Time_spent": 90})
    lines = output.splitlines()
    assert lines[0] == "Python"
    assert "50.00%" in lines[1]
    assert lines[2].startswith("Total time:")
