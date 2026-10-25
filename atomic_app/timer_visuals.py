from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

DIGIT_ART: dict[str, tuple[str, ...]] = {
    "0": ("┏━┓", "┃ ┃", "┗━┛"),
    "1": (" ╻ ", " ┃ ", "╺┻╸"),
    "2": ("┏━┓", " ━┫", "┗━╸"),
    "3": ("┏━┓", " ━┫", "┗━┛"),
    "4": ("╻ ╻", "┗━┫", "  ╹"),
    "5": ("┏━╸", "┗━┓", "┗━┛"),
    "6": ("┏━╸", "┣━┓", "┗━┛"),
    "7": ("┏━┓", "  ┃", "  ╹"),
    "8": ("┏━┓", "┣━┫", "┗━┛"),
    "9": ("┏━┓", "┗━┫", "╺━┛"),
    ":": ("   ", " • ", " • "),
}


def format_countdown(seconds: int) -> str:
    mins, secs = divmod(max(seconds, 0), 60)
    hours, mins = divmod(mins, 60)
    if hours:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def render_ascii_countdown(seconds: int) -> list[str]:
    return render_ascii_text(format_countdown(seconds))


def render_ascii_text(text: str) -> list[str]:
    rows = [""] * 3
    for index, ch in enumerate(text):
        glyph = DIGIT_ART.get(ch, DIGIT_ART["0"])
        for row in range(3):
            rows[row] += glyph[row]
            if index < len(text) - 1:
                rows[row] += " "
    return rows


def clip_text(text: str, x: int, width: int) -> tuple[int, str]:
    if width <= 0 or not text:
        return x, ""
    if x >= width:
        return x, ""
    if x < 0:
        text = text[-x:]
        x = 0
    if x >= width or not text:
        return x, ""
    return x, text[: max(width - x, 0)]


@dataclass
class DrawCell:
    x: int
    y: int
    char: str
    style: str = "normal"


@dataclass(frozen=True)
class Viewport:
    x: int
    y: int
    width: int
    height: int


def split_layout(height: int, width: int, pad_y: int = 1, pad_x: int = 2) -> tuple[Viewport, Viewport]:
    inner_width = max(width - (pad_x * 2), 0)
    inner_height = max(height - (pad_y * 2), 0)
    if inner_width <= 0 or inner_height <= 0:
        empty = Viewport(0, 0, 0, 0)
        return empty, empty

    top_height = max(int(inner_height * 0.65), 3)
    min_bottom = 7
    if inner_height >= min_bottom + 3:
        top_height = min(top_height, inner_height - min_bottom)
    top_height = min(top_height, inner_height)
    bottom_height = max(inner_height - top_height, 0)

    top = Viewport(x=pad_x, y=pad_y, width=inner_width, height=top_height)
    bottom = Viewport(x=pad_x, y=pad_y + top_height, width=inner_width, height=bottom_height)
    return top, bottom


@dataclass
class RainDrop:
    x: int
    y: float
    speed: float
    char: str
    tail: int


@dataclass
class Star:
    x: int
    y: int
    twinkle_phase: float
    twinkle_speed: float


@dataclass
class RainAnimation:
    rng: random.Random = field(default_factory=random.Random)
    drops: list[RainDrop] = field(default_factory=list)
    glyphs: tuple[str, ...] = ("|", "/", "\\", ".", "'", "`")

    def step(self, dt: float, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            self.drops.clear()
            return
        if dt < 0:
            dt = 0
        for drop in self.drops:
            drop.y += drop.speed * dt
        self.drops = [drop for drop in self.drops if drop.y < height + drop.tail]

        target = max(width // 4, 1)
        spawn_attempts = max(1, int(width * max(dt, 0.05) * 0.5))
        for _ in range(spawn_attempts):
            if len(self.drops) >= target:
                break
            if self.rng.random() < 0.5:
                self.drops.append(
                    RainDrop(
                        x=self.rng.randrange(0, width),
                        y=self.rng.uniform(-float(height), 0.0),
                        speed=self.rng.uniform(8.0, 20.0),
                        char=self.rng.choice(self.glyphs),
                        tail=self.rng.randint(2, 6),
                    )
                )

    def cells(self, width: int, height: int) -> list[DrawCell]:
        output: list[DrawCell] = []
        for drop in self.drops:
            y = int(drop.y)
            if 0 <= y < height and 0 <= drop.x < width:
                output.append(DrawCell(drop.x, y, drop.char, "bright"))
            for tail_index in range(1, drop.tail + 1):
                tail_y = y - tail_index
                if 0 <= tail_y < height and 0 <= drop.x < width:
                    output.append(DrawCell(drop.x, tail_y, ".", "dim"))
        return output


@dataclass
class AstroAnimation:
    rng: random.Random = field(default_factory=random.Random)
    stars: list[Star] = field(default_factory=list)
    planet_phase: float = 0.0
    _initialized_for: tuple[int, int] = (0, 0)

    def _ensure_stars(self, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            self.stars.clear()
            self._initialized_for = (width, height)
            return
        if self._initialized_for == (width, height):
            return
        target = max((width * height) // 140, 10)
        self.stars = [
            Star(
                x=self.rng.randrange(0, width),
                y=self.rng.randrange(0, height),
                twinkle_phase=self.rng.uniform(0.0, math.tau),
                twinkle_speed=self.rng.uniform(0.6, 2.2),
            )
            for _ in range(target)
        ]
        self._initialized_for = (width, height)

    def step(self, dt: float, width: int, height: int) -> None:
        self._ensure_stars(width, height)
        if dt < 0:
            dt = 0
        self.planet_phase = (self.planet_phase + dt * 0.35) % math.tau
        for star in self.stars:
            star.twinkle_phase = (star.twinkle_phase + dt * star.twinkle_speed) % math.tau

    def cells(self, width: int, height: int) -> list[DrawCell]:
        output: list[DrawCell] = []
        for star in self.stars:
            intensity = math.sin(star.twinkle_phase)
            char = "*" if intensity > 0.55 else "."
            style = "bright" if intensity > 0.55 else "dim"
            if 0 <= star.x < width and 0 <= star.y < height:
                output.append(DrawCell(star.x, star.y, char, style))

        planet_x = int(width * 0.8 + math.sin(self.planet_phase) * 1.2)
        planet_y = int(height * 0.35 + math.cos(self.planet_phase) * 0.8)
        planet = [
            DrawCell(planet_x, planet_y, "O", "normal"),
            DrawCell(planet_x - 1, planet_y, "(", "dim"),
            DrawCell(planet_x + 1, planet_y, ")", "dim"),
            DrawCell(planet_x - 2, planet_y + 1, "-", "dim"),
            DrawCell(planet_x - 1, planet_y + 1, "=", "dim"),
            DrawCell(planet_x, planet_y + 1, "=", "dim"),
            DrawCell(planet_x + 1, planet_y + 1, "-", "dim"),
        ]
        for cell in planet:
            if 0 <= cell.x < width and 0 <= cell.y < height:
                output.append(cell)
        return output


@dataclass
class BackgroundAnimator:
    rng_seed: int = 0
    mode: str = "off"
    _last_time: float | None = None
    _rain: RainAnimation = field(init=False)
    _astro: AstroAnimation = field(init=False)

    MODES: tuple[str, ...] = ("off", "rain", "astro")

    def __post_init__(self) -> None:
        self._rain = RainAnimation(random.Random(self.rng_seed + 1))
        self._astro = AstroAnimation(random.Random(self.rng_seed + 2))
        if self.mode not in self.MODES:
            self.mode = "off"

    def cycle_mode(self) -> str:
        index = self.MODES.index(self.mode)
        self.mode = self.MODES[(index + 1) % len(self.MODES)]
        return self.mode

    def step(self, now: float, width: int, height: int) -> None:
        dt = 0.0 if self._last_time is None else max(now - self._last_time, 0.0)
        self._last_time = now
        if self.mode == "rain":
            self._rain.step(dt, width, height)
        elif self.mode == "astro":
            self._astro.step(dt, width, height)

    def cells(self, width: int, height: int) -> list[DrawCell]:
        if self.mode == "rain":
            return self._rain.cells(width, height)
        if self.mode == "astro":
            return self._astro.cells(width, height)
        return []
