# Atomic

Atomic is a Linux terminal productivity timer CLI.

## Installation

```bash
cd /home/runner/work/atomic/atomic
python -m pip install -e .
```

## Commands

```bash
atomic timer
atomic today
atomic progress
atomic progress <subject>
atomic refresh
```

## Timer controls (`atomic timer`)

- `Ctrl+T`: set/change duration in minutes (starts a new session)
- `Ctrl+O`: choose subject (or unassigned)
- `Space`: pause/resume
- `d`: while paused, finish/save current session
- `q`: request exit; unfinished sessions require confirmation and are discarded if confirmed

Session accounting rules:

- Paused time is excluded from productive time.
- Completed productive time is stored as whole minutes using truncation (`floor`).
- Sessions auto-save when countdown reaches zero.
- Sessions can also be saved early with `d` while paused.

## Data storage

Runtime files are created in the project directory:

- `atomic.json`
- `subjects/*.md`

`atomic.json` schema:

```json
{
  "subjects": {
    "Python": {
      "Name": "Python",
      "Time_spent": 90,
      "md_link": "subjects/python.md",
      "done": 50.0
    }
  },
  "logs": {
    "2026-10-24": {
      "Python": 90,
      "null": 30
    }
  }
}
```

Notes:

- Subject field names are exactly: `Name`, `Time_spent`, `md_link`, `done`.
- Minutes are stored as integers.
- Unassigned sessions are logged under the `null` key.
- Same-day repeated sessions aggregate by subject.
- `Time_spent` increases when a subject session is saved.
- JSON writes are atomic (temp file + replace), and malformed/missing JSON falls back safely.

## Markdown subject format and refresh

Put subject markdown files under `subjects/`.

Example (`subjects/sample.md`):

```md
# Sample Subject

- [ ] Define goals
- [x] Start first focused session
- [ ] Review progress weekly
```

`atomic refresh` behavior:

- Scans `subjects/**/*.md`.
- Uses first H1 (`# ...`) as subject name; otherwise filename stem.
- Updates/creates subject entries with `md_link` and `done`.
- Computes `done` as `(completed/total) * 100`, rounded to 2 decimals.
- Zero-task files get `done = 0.0`.
- Removes subjects whose markdown files no longer exist.
- Preserves all historical `logs` even when subjects are removed.
- If two markdown files resolve to the same subject name, the first discovered file (sorted path order) wins and later duplicates are skipped with a message.

## Display behavior

### `atomic progress`

Shows all subjects with name, progress bar, percent, and total time.

### `atomic progress <subject>`

- Case-insensitive subject match.
- Prints progress bar first, then total time.
- Unknown subject returns a non-zero exit code.

### `atomic today`

- Shows today's logged work (`logs[YYYY-MM-DD]`).
- Converts minutes to `h/m` display.
- Displays `null` as `Unassigned`.
- Includes total.
- Prints an empty-state message when no work exists for today.

## Development

Run tests:

```bash
pytest -q
```
