from __future__ import annotations

import curses
import datetime as dt
from pathlib import Path

from atomic_app.session import TimerSession
from atomic_app.storage import add_session, load_data

CTRL_T = 20
CTRL_O = 15


def _draw_box(stdscr: curses.window, title: str, lines: list[str]) -> None:
    h, w = stdscr.getmaxyx()
    box_h = min(max(len(lines) + 4, 7), h - 2)
    box_w = min(max(max((len(line) for line in lines), default=20) + 4, len(title) + 4), w - 2)
    y = (h - box_h) // 2
    x = (w - box_w) // 2

    win = curses.newwin(box_h, box_w, y, x)
    win.box()
    win.addstr(0, 2, f" {title} "[: box_w - 4])
    for idx, line in enumerate(lines[: box_h - 4]):
        win.addstr(2 + idx, 2, line[: box_w - 4])
    win.refresh()


def _prompt_minutes(stdscr: curses.window) -> int | None:
    curses.echo()
    curses.curs_set(1)
    h, w = stdscr.getmaxyx()
    prompt = "Duration in minutes: "
    win_w = min(max(len(prompt) + 12, 30), w - 2)
    win = curses.newwin(5, win_w, max((h - 5) // 2, 0), max((w - win_w) // 2, 0))
    win.box()
    win.addstr(1, 2, prompt)
    win.refresh()

    try:
        value = win.getstr(1, len(prompt) + 2, 8).decode("utf-8").strip()
        if not value:
            return None
        minutes = int(value)
        return minutes if minutes > 0 else None
    except (ValueError, curses.error):
        return None
    finally:
        curses.noecho()
        curses.curs_set(0)


def _select_subject(stdscr: curses.window, subjects: list[str], selected: str | None) -> str | None:
    options = ["<Unassigned>", *subjects]
    index = 0
    if selected and selected in subjects:
        index = subjects.index(selected) + 1

    while True:
        h, w = stdscr.getmaxyx()
        win_h = min(max(len(options) + 4, 8), h - 2)
        win_w = min(max(max(len(item) for item in options) + 6, 30), w - 2)
        y = max((h - win_h) // 2, 0)
        x = max((w - win_w) // 2, 0)
        win = curses.newwin(win_h, win_w, y, x)
        win.keypad(True)
        win.box()
        win.addstr(0, 2, " Select subject ")

        start = max(index - (win_h - 4) + 1, 0)
        visible = options[start : start + (win_h - 4)]

        for row, option in enumerate(visible, start=0):
            option_index = start + row
            marker = "> " if option_index == index else "  "
            attr = curses.A_REVERSE if option_index == index else curses.A_NORMAL
            win.addstr(2 + row, 2, f"{marker}{option}"[: win_w - 4], attr)

        win.refresh()
        key = win.getch()

        if key in (curses.KEY_UP, ord("k")):
            index = (index - 1) % len(options)
        elif key in (curses.KEY_DOWN, ord("j")):
            index = (index + 1) % len(options)
        elif key in (10, 13, curses.KEY_ENTER):
            chosen = options[index]
            return None if chosen == "<Unassigned>" else chosen
        elif key in (27, ord("q")):
            return selected


def _confirm_exit(stdscr: curses.window) -> bool:
    options = ["Yes, exit", "No, continue"]
    index = 1

    while True:
        h, w = stdscr.getmaxyx()
        box_h, box_w = 8, min(52, w - 2)
        y = max((h - box_h) // 2, 0)
        x = max((w - box_w) // 2, 0)
        win = curses.newwin(box_h, box_w, y, x)
        win.keypad(True)
        win.box()
        win.addstr(1, 2, "Exit timer?")
        win.addstr(2, 2, "The current unfinished session will be discarded.")

        for idx, label in enumerate(options):
            attr = curses.A_REVERSE if idx == index else curses.A_NORMAL
            win.addstr(4 + idx, 4, label, attr)

        win.refresh()
        key = win.getch()

        if key in (curses.KEY_UP, curses.KEY_DOWN, 9):
            index = (index + 1) % len(options)
        elif key in (ord("y"), ord("Y")):
            return True
        elif key in (ord("n"), ord("N"), 27):
            return False
        elif key in (10, 13, curses.KEY_ENTER):
            return index == 0


def _format_countdown(seconds: int) -> str:
    mins, secs = divmod(max(seconds, 0), 60)
    hours, mins = divmod(mins, 60)
    if hours:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def _render_main(stdscr: curses.window, session: TimerSession, selected_subject: str | None, status: str) -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    stdscr.addstr(1, 2, "Atomic Timer", curses.A_BOLD)
    stdscr.addstr(3, 2, f"Remaining: {_format_countdown(session.remaining_seconds)}", curses.A_BOLD)
    stdscr.addstr(4, 2, f"Elapsed productive time: {_format_countdown(int(session.elapsed_seconds))}")
    stdscr.addstr(5, 2, f"Subject: {selected_subject or 'Unassigned'}")

    mode = "Running" if session.running else "Paused"
    if session.finished:
        mode = "Completed"
    stdscr.addstr(7, 2, f"Status: {mode}")

    help_lines = [
        "Ctrl+T set duration", "Ctrl+O select subject", "Space pause/resume", "d save paused session", "q quit",
    ]
    stdscr.addstr(9, 2, " | ".join(help_lines)[: w - 4])

    if status:
        stdscr.addstr(11, 2, status[: w - 4])

    stdscr.refresh()


def _run(stdscr: curses.window, base_path: Path) -> int:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    session = TimerSession(total_minutes=0)
    selected_subject: str | None = None
    status = "Press Ctrl+T to set a duration."

    while True:
        session.tick()

        if session.finished and session.started:
            today = dt.date.today().isoformat()
            add_session(base_path, today, session.subject, session.productive_minutes)
            status = f"Saved {session.productive_minutes} minute(s) for {session.subject or 'Unassigned'}."
            session = TimerSession(total_minutes=0, subject=selected_subject)

        _render_main(stdscr, session, selected_subject, status)

        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            return 130

        if key == -1:
            curses.napms(100)
            continue

        if key == CTRL_T:
            minutes = _prompt_minutes(stdscr)
            if minutes is None:
                status = "Duration unchanged. Enter a positive integer minute value."
            else:
                session = TimerSession(total_minutes=minutes, subject=selected_subject)
                session.start()
                status = f"Timer started for {minutes} minute(s)."
        elif key == CTRL_O:
            data = load_data(base_path)
            subjects = sorted(data["subjects"].keys(), key=str.lower)
            selected_subject = _select_subject(stdscr, subjects, selected_subject)
            if session.total_minutes == 0 or not session.started:
                session.subject = selected_subject
            status = f"Subject set to {selected_subject or 'Unassigned'}."
        elif key == ord(" "):
            if session.total_minutes <= 0:
                status = "Set a duration first with Ctrl+T."
            elif session.running:
                session.pause()
                status = "Paused. Press Space to resume or d to save."
            elif not session.finished:
                session.resume()
                status = "Resumed."
        elif key in (ord("d"), ord("D")):
            if session.total_minutes <= 0 or not session.started:
                status = "No active session to save."
            elif session.running:
                status = "Pause the timer before saving with d."
            else:
                today = dt.date.today().isoformat()
                add_session(base_path, today, session.subject, session.productive_minutes)
                status = f"Saved {session.productive_minutes} minute(s) for {session.subject or 'Unassigned'}."
                session = TimerSession(total_minutes=0, subject=selected_subject)
        elif key in (ord("q"), ord("Q")):
            if session.has_unsaved_work:
                if _confirm_exit(stdscr):
                    return 0
                status = "Exit canceled."
            else:
                return 0
        elif key == curses.KEY_RESIZE:
            continue


def run_timer(base_path: Path) -> int:
    load_data(base_path)
    try:
        return curses.wrapper(_run, base_path)
    except KeyboardInterrupt:
        return 130
