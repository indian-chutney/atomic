from pathlib import Path

from atomic_app.markdown import parse_subject_markdown


def test_parse_markdown_heading_and_tasks(tmp_path: Path) -> None:
    md = tmp_path / "python.md"
    md.write_text("# Python\n\n- [ ] Variables\n- [x] Functions\n- [X] Classes\n", encoding="utf-8")

    heading, done, completed, total = parse_subject_markdown(md)

    assert heading == "Python"
    assert completed == 2
    assert total == 3
    assert done == 66.67


def test_parse_markdown_without_tasks(tmp_path: Path) -> None:
    md = tmp_path / "notes.md"
    md.write_text("# Notes\nNo checkboxes here", encoding="utf-8")

    heading, done, completed, total = parse_subject_markdown(md)
    assert heading == "Notes"
    assert completed == 0
    assert total == 0
    assert done == 0.0
