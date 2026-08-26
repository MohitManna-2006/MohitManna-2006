#!/usr/bin/env python3
"""
Render the animated terminal hero used by the profile README.

Outputs (relative to the repository root):
    assets/terminal.gif         the animated hero
    assets/terminal-static.png  the final frame, used as a reduced-motion fallback

Everything worth editing lives in the CONFIGURATION block and in build_script()
near the top of this file. The renderer below is deliberately small: it draws a
window, a buffer of coloured text spans, and a block cursor.
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

WIDTH, HEIGHT = 940, 450     # final image size in pixels
MARGIN = 14                  # gap between image edge and the window
TITLEBAR_H = 40
PAD_X, PAD_TOP = 28, 16      # padding inside the window body
FONT_SIZE = 19
LINE_H = 27
CORNER = 10

TYPE_MS = 62                 # base delay between typed characters
TYPE_JITTER = 14             # +/- variation, seeded so runs are reproducible
BLINK_MS = 560               # cursor half-period while idle
PALETTE_COLORS = 64          # GIF palette size
LEADER_COL = 46              # column where "[ok]" markers line up

COLORS = {
    "canvas":   (1, 4, 9),        # outside the window
    "body":     (13, 17, 23),     # #0d1117
    "titlebar": (22, 27, 34),     # #161b22
    "border":   (48, 54, 61),     # #30363d
    "primary":  (201, 209, 217),  # #c9d1d9
    "bright":   (230, 237, 243),
    "muted":    (139, 148, 158),  # #8b949e
    "green":    (63, 185, 80),    # #3fb950
    "blue":     (88, 166, 255),   # #58a6ff
    "dim":      (72, 79, 88),     # dot leaders and separators
}

TITLE_LEFT = "mohit://dev"
TITLE_RIGHT = "connected"

# Searched in order. Override with PROFILE_TERMINAL_FONT=/path/to/font.ttf
FONT_CANDIDATES = [
    ("/System/Library/Fonts/Menlo.ttc", 0),
    ("/System/Library/Fonts/SFNSMono.ttf", 0),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 0),
    ("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", 0),
    ("/usr/share/fonts/TTF/DejaVuSansMono.ttf", 0),
    ("/usr/share/fonts/dejavu/DejaVuSansMono.ttf", 0),
    ("/usr/local/share/fonts/DejaVuSansMono.ttf", 0),
    ("/System/Library/Fonts/Supplemental/Courier New.ttf", 0),
    ("C:/Windows/Fonts/consola.ttf", 0),
]

ROOT = Path(__file__).resolve().parent.parent
GIF_PATH = ROOT / "assets" / "terminal.gif"
PNG_PATH = ROOT / "assets" / "terminal-static.png"

# The shell prompt, as coloured spans.
PROMPT = [
    ("visitor", "green"), ("@", "dim"), ("profile", "green"),
    (":", "dim"), ("~", "blue"), ("$ ", "muted"),
]


# ---------------------------------------------------------------------------
# SCRIPT  --  the animation content, in order
# ---------------------------------------------------------------------------

def build_script(t: "Terminal") -> None:
    """Drive the terminal. Every call here appends frames to the timeline."""
    t.hold(0.6)

    t.type_command("connect mohit")
    t.hold(0.30)
    t.status("establishing session")
    t.hold(0.42)
    t.status("handshake complete")
    t.blank()
    t.hold(0.55)

    t.type_command("whoami")
    t.hold(0.22)
    t.line([("Mohit Manna", "bright")])
    t.hold(0.20)
    t.line([("Computer Engineering @ Purdue", "primary")])
    t.hold(0.20)
    t.line([("Software \u00b7 Systems \u00b7 AI \u00b7 Infrastructure", "muted")])
    t.blank()
    t.hold(0.60)

    t.type_command("ls projects --featured")
    t.hold(0.26)
    t.line([
        ("pulsekv/", "blue"), ("   ", "dim"),
        ("tessera/", "blue"), ("   ", "dim"),
        ("fintrak/", "blue"), ("   ", "dim"),
        ("personal-portfolio/", "blue"),
    ])
    t.blank()
    t.hold(0.45)

    t.prompt_only()
    t.hold(3.4)          # rest here so the loop does not feel like a restart


# ---------------------------------------------------------------------------
# RENDERING
# ---------------------------------------------------------------------------

Span = tuple[str, str]


def load_font() -> tuple[ImageFont.FreeTypeFont, str]:
    override = os.environ.get("PROFILE_TERMINAL_FONT")
    candidates = ([(override, 0)] if override else []) + FONT_CANDIDATES
    for path, index in candidates:
        if path and Path(path).is_file():
            try:
                return ImageFont.truetype(path, FONT_SIZE, index=index), path
            except OSError:
                continue
    raise SystemExit(
        "No monospace font found. Install DejaVu Sans Mono or Liberation Mono, "
        "or set PROFILE_TERMINAL_FONT to a .ttf/.ttc path."
    )


@dataclass
class Renderer:
    font: ImageFont.FreeTypeFont

    def __post_init__(self) -> None:
        self.char_w = self.font.getlength("M")
        self.ascent, _ = self.font.getmetrics()
        self.body_top = MARGIN + TITLEBAR_H
        self.text_x = MARGIN + PAD_X
        self.text_y = self.body_top + PAD_TOP
        self.base = self._draw_window()

    def _draw_window(self) -> Image.Image:
        """The static chrome: canvas, window body, title bar, border."""
        img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["canvas"])
        d = ImageDraw.Draw(img)
        box = (MARGIN, MARGIN, WIDTH - MARGIN - 1, HEIGHT - MARGIN - 1)

        d.rounded_rectangle(box, radius=CORNER, fill=COLORS["body"])
        # Title bar: a rounded top capped with a square bottom edge.
        d.rounded_rectangle(
            (box[0], box[1], box[2], box[1] + TITLEBAR_H),
            radius=CORNER, fill=COLORS["titlebar"],
        )
        d.rectangle(
            (box[0], box[1] + TITLEBAR_H - CORNER, box[2], box[1] + TITLEBAR_H),
            fill=COLORS["titlebar"],
        )
        d.line(
            (box[0], box[1] + TITLEBAR_H, box[2], box[1] + TITLEBAR_H),
            fill=COLORS["border"], width=1,
        )
        d.rounded_rectangle(box, radius=CORNER, outline=COLORS["border"], width=1)

        # Title bar contents.
        bar_mid = box[1] + TITLEBAR_H // 2
        d.text((self.text_x, bar_mid), TITLE_LEFT,
               font=self.font, fill=COLORS["muted"], anchor="lm")

        right = box[2] - PAD_X
        d.text((right, bar_mid), TITLE_RIGHT,
               font=self.font, fill=COLORS["muted"], anchor="rm")
        dot_x = right - self.font.getlength(TITLE_RIGHT) - 14
        d.ellipse((dot_x - 4, bar_mid - 4, dot_x + 4, bar_mid + 4),
                  fill=COLORS["green"])
        return img

    def frame(self, lines: list[list[Span]], cursor: bool) -> Image.Image:
        img = self.base.copy()
        d = ImageDraw.Draw(img)
        y = self.text_y
        for row, spans in enumerate(lines):
            x = self.text_x
            for text, color in spans:
                d.text((x, y), text, font=self.font, fill=COLORS[color])
                x += self.font.getlength(text)
            if cursor and row == len(lines) - 1:
                d.rectangle(
                    (x, y + 3, x + self.char_w - 1, y + self.ascent),
                    fill=COLORS["primary"],
                )
            y += LINE_H
        return img


# ---------------------------------------------------------------------------
# TIMELINE
# ---------------------------------------------------------------------------

class Terminal:
    """Holds the visible buffer and records (image, duration_ms) frames."""

    def __init__(self, renderer: Renderer) -> None:
        self.r = renderer
        self.lines: list[list[Span]] = [list(PROMPT)]
        self.frames: list[tuple[Image.Image, int]] = []
        self.rng = random.Random(7)

    # -- frame emission ----------------------------------------------------
    def _emit(self, duration_ms: int, cursor: bool = True) -> None:
        self.frames.append((self.r.frame(self.lines, cursor), duration_ms))

    def hold(self, seconds: float) -> None:
        """Pause. Long pauses blink the cursor instead of freezing it."""
        ms = int(seconds * 1000)
        if ms <= BLINK_MS:
            self._emit(ms)
            return
        on = True
        while ms > 0:
            step = min(BLINK_MS, ms)
            # Absorb a short remainder rather than emitting a sliver frame.
            if 0 < ms - step < 120:
                step = ms
            self._emit(step, cursor=on)
            on = not on
            ms -= step

    # -- content -----------------------------------------------------------
    def type_command(self, command: str) -> None:
        """Type into the current prompt line, one character per frame."""
        typed = ""
        for ch in command:
            typed += ch
            self.lines[-1] = list(PROMPT) + [(typed, "primary")]
            self._emit(TYPE_MS + self.rng.randint(-TYPE_JITTER, TYPE_JITTER))
        self.hold(0.18)              # beat before "enter"
        self.lines.append([])

    def line(self, spans: list[Span]) -> None:
        self.lines[-1] = spans
        self.lines.append([])
        self._emit(60)

    def status(self, label: str) -> None:
        """An output line with dot leaders and a right-aligned [ok] marker."""
        dots = max(1, LEADER_COL - len(label) - 6)
        self.line([
            (label + " ", "muted"),
            ("\u00b7" * dots + " ", "dim"),
            ("[", "dim"), ("ok", "green"), ("]", "dim"),
        ])

    def blank(self) -> None:
        self.lines[-1] = []
        self.lines.append([])

    def prompt_only(self) -> None:
        self.lines[-1] = list(PROMPT)
        self._emit(60)


# ---------------------------------------------------------------------------
# EXPORT
# ---------------------------------------------------------------------------

def export(terminal: "Terminal") -> None:
    """Quantise every frame against one shared palette, then write the GIF."""
    GIF_PATH.parent.mkdir(parents=True, exist_ok=True)
    frames = terminal.frames

    # The completed screen with a visible cursor: the reduced-motion fallback,
    # and the reference for the shared palette.
    final = terminal.r.frame(terminal.lines, cursor=True)

    # One shared palette across every frame avoids inter-frame flicker.
    master = final.quantize(colors=PALETTE_COLORS, method=Image.Quantize.MEDIANCUT)
    paletted = [
        img.quantize(palette=master, dither=Image.Dither.NONE)
        for img, _ in frames
    ]
    durations = [ms for _, ms in frames]

    paletted[0].save(
        GIF_PATH,
        save_all=True,
        append_images=paletted[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=1,
    )
    final.save(PNG_PATH, optimize=True)


def main() -> None:
    font, font_path = load_font()
    renderer = Renderer(font)
    terminal = Terminal(renderer)
    build_script(terminal)
    export(terminal)

    total_ms = sum(ms for _, ms in terminal.frames)
    print(f"font        {font_path}")
    print(f"frames      {len(terminal.frames)}")
    print(f"duration    {total_ms / 1000:.2f}s")
    print(f"gif         {GIF_PATH.relative_to(ROOT)}  "
          f"{WIDTH}x{HEIGHT}  {GIF_PATH.stat().st_size / 1024:.0f} KB")
    print(f"png         {PNG_PATH.relative_to(ROOT)}  "
          f"{WIDTH}x{HEIGHT}  {PNG_PATH.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
