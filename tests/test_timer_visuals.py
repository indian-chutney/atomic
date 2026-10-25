import random

from atomic_app.timer_visuals import (
    AstroAnimation,
    BackgroundAnimator,
    RainAnimation,
    clip_text,
    format_countdown,
    render_ascii_countdown,
    split_layout,
)


def test_format_countdown_supports_hours() -> None:
    assert format_countdown(59) == "00:59"
    assert format_countdown(3661) == "01:01:01"


def test_render_ascii_countdown_shape() -> None:
    rows = render_ascii_countdown(125)
    assert len(rows) == 3
    assert all(len(row) > 0 for row in rows)
    assert any("┏" in row or "╺" in row for row in rows)


def test_clip_text_handles_negative_x() -> None:
    x, text = clip_text("abcdef", -2, 4)
    assert x == 0
    assert text == "cdef"


def test_background_mode_cycles() -> None:
    animator = BackgroundAnimator(mode="off")
    assert animator.cycle_mode() == "rain"
    assert animator.cycle_mode() == "astro"
    assert animator.cycle_mode() == "off"


def test_rain_animation_produces_in_bounds_cells() -> None:
    rain = RainAnimation(rng=random.Random(7))
    for _ in range(10):
        rain.step(0.3, width=30, height=12)
    cells = rain.cells(width=30, height=12)
    assert cells
    assert all(0 <= cell.x < 30 and 0 <= cell.y < 12 for cell in cells)


def test_astro_animation_has_stars_and_planet() -> None:
    astro = AstroAnimation(rng=random.Random(11))
    astro.step(0.5, width=40, height=16)
    cells = astro.cells(width=40, height=16)
    assert any(cell.char in {"*", "."} for cell in cells)
    assert any(cell.char == "O" for cell in cells)


def test_split_layout_prioritizes_top_with_padding() -> None:
    top, bottom = split_layout(height=30, width=100, pad_y=1, pad_x=2)
    assert top.x == 2
    assert bottom.x == 2
    assert top.y == 1
    assert bottom.y == 1 + top.height
    assert top.width == 96
    assert bottom.width == 96
    assert top.height > bottom.height
