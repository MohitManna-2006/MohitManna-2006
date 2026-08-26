#!/usr/bin/env python3
"""
Render the animated terminal hero used by the profile README.

Outputs (relative to the repository root):
    assets/terminal.gif         the animated session
    assets/terminal-static.png  the richest single screen, used as the
                                reduced-motion fallback

The terminal keeps a scrollback history and renders the tail of it, so output
accumulates and older lines scroll off the top the way a real session behaves.

Two places cover almost every edit:
    CONFIGURATION  geometry, palette, timing
    CONTENT        the profile data itself
    build_session  the order commands run in
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

WIDTH, HEIGHT = 940, 720     # final image size in pixels
MARGIN = 14                  # gap between image edge and the window
TITLEBAR_H = 40
FOOTER_H = 34                # tmux-style status bar
PAD_X, PAD_TOP = 28, 16      # padding inside the window body
PAD_BOTTOM = 10
FONT_SIZE = 19
LINE_H = 28
CORNER = 10

TYPE_MS = 55                 # delay between typed characters
TYPE_JITTER = 12             # +/- variation, seeded so runs are reproducible
BLINK_MS = 560               # cursor half-period while idle
PALETTE_COLORS = 64          # GIF palette size

COLORS = {
    "canvas":   (1, 4, 9),        # outside the window
    "body":     (13, 17, 23),     # #0d1117
    "titlebar": (22, 27, 34),     # #161b22
    "border":   (48, 54, 61),     # #30363d
    "primary":  (201, 209, 217),  # #c9d1d9
    "bright":   (237, 242, 247),
    "muted":    (139, 148, 158),  # #8b949e
    "green":    (63, 185, 80),    # #3fb950
    "blue":     (88, 166, 255),   # #58a6ff
    "dim":      (78, 86, 96),     # tree glyphs, dot leaders, separators
}

TITLE_LEFT = "mohit://dev"
TITLE_RIGHT = "connected"
FOOTER_LEFT = "profile:mohit"
FOOTER_RIGHT = "~/profile"

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

# Character-grid columns. Everything aligns against these.
RIGHT_EDGE = 72              # right-aligned column for dates and metrics
COL_ROLE = 13                # experience: where the role starts
COL_DOMAIN = 20              # projects: where the domain label starts
COL_STACK = 12               # env: where values start
LEADER_EDGE = 56             # boot lines: where "[ok]" lands

PROMPT = [
    ("visitor", "green"), ("@", "dim"), ("profile", "green"),
    (":", "dim"), ("~", "blue"), ("$ ", "muted"),
]

# ---------------------------------------------------------------------------
# CONTENT  --  every profile fact lives here
# ---------------------------------------------------------------------------

BOOT = [
    "establishing session",
    "loading engineering profile",
    "mounting ~/projects",
]

IDENTITY = [
    [("Mohit Manna", "bright")],
    [("Computer Engineering @ Purdue · Dec 2027", "primary")],
    [("minors  ", "muted"), ("Math · Finance", "primary")],
    [("focus   ", "muted"),
     ("distributed systems · LLM infrastructure · performance", "primary")],
]

# company, role, dates, technical signature, one verified metric
EXPERIENCE = [
    ("IBM", "Software Engineer Intern", "May–Aug 2026",
     "FastAPI · Redis · Kubernetes · pgvector", "10K+ analyses"),
    ("Handshake", "AI Engineer", "Jan–Apr 2026",
     "RLHF · code eval · vLLM · AWQ", "+18% pass@1"),
    ("Caterpillar", "Machine Learning Intern", "Aug–Dec 2025",
     "PyTorch · TFT · Optuna · TorchScript", "+12% forecast accuracy"),
    ("Stealth AI", "Software Engineer Intern", "Jun–Aug 2025",
     "React · GraphQL · WebSockets", "500+ concurrent connections"),
]

# name, domain, what it is, technical signature
PROJECTS = [
    ("pulsekv", "distributed systems",
     "sharded KV for LLM inference", "C · epoll · Go · Raft · vLLM"),
    ("tessera", "developer tooling",
     "repos + résumé → deployable portfolio", "Next.js · PDF · export"),
    ("fintrak", "applied ai",
     "finance tracker with an LLM in the loop", "Prisma · Postgres"),
    ("personal-portfolio", "web",
     "portfolio built as a technical artifact", "Next.js · TypeScript"),
]

STACK = [
    ("languages", "Python · TypeScript · C · C++ · Go · Java · SQL"),
    ("systems",   "Linux · epoll · Raft · gRPC · concurrency"),
    ("backend",   "FastAPI · Node.js · Express · PostgreSQL · Redis"),
    ("ai",        "PyTorch · vLLM · RLHF · pgvector"),
    ("infra",     "Docker · Kubernetes · AWS · Azure"),
    ("web",       "React · Next.js · GraphQL · Tailwind"),
    ("tooling",   "Git · GitHub Actions · OpenTelemetry"),
]


# ---------------------------------------------------------------------------
# SESSION  --  the order things happen in
# ---------------------------------------------------------------------------

def build_session(s: "Session") -> None:
    s.hold(0.6)

    s.type_command("connect mohit")
    for label in BOOT:
        s.print(boot_line(label), 260)
    s.blank()
    s.hold(0.5)

    s.type_command("whoami")
    for line in IDENTITY:
        s.print(line, 220)
    s.blank()
    s.hold(0.7)

    s.type_command("experience --timeline")
    for company, role, dates, tech, metric in EXPERIENCE:
        s.print(experience_head(company, role, dates), 190)
        s.print(experience_detail(tech, metric), 190)
    # This screen — connect, whoami, and all four roles — is the fallback PNG.
    # Captured before the blank line so the opening command stays on screen.
    s.mark_static()
    s.blank()
    s.hold(1.5)

    s.type_command("projects --featured")
    for name, domain, what, tech in PROJECTS:
        s.print(project_head(name, domain), 190)
        s.print(project_detail(what, tech), 190)
    s.blank()
    s.hold(1.5)

    s.type_command("env --stack")
    for key, value in STACK:
        s.print(stack_line(key, value), 180)
    s.blank()
    s.hold(1.0)

    s.prompt_only()
    s.hold(2.6)


# ---------------------------------------------------------------------------
# LINE BUILDERS  --  turn content into aligned coloured spans
# ---------------------------------------------------------------------------

Span = tuple[str, str]


def _pad_to(spans: list[Span], column: int) -> list[Span]:
    """Pad with spaces so the next span starts at `column`."""
    used = sum(len(t) for t, _ in spans)
    return spans + [(" " * max(1, column - used), "dim")]


def _right_align(spans: list[Span], text: str, color: str) -> list[Span]:
    """Place `text` so it ends at RIGHT_EDGE."""
    used = sum(len(t) for t, _ in spans)
    gap = max(1, RIGHT_EDGE - len(text) - used)
    return spans + [(" " * gap, "dim"), (text, color)]


def boot_line(label: str) -> list[Span]:
    dots = max(1, LEADER_EDGE - len(label) - 6)
    return [
        (label + " ", "muted"),
        ("·" * dots + " ", "dim"),
        ("[", "dim"), ("ok", "green"), ("]", "dim"),
    ]


def experience_head(company: str, role: str, dates: str) -> list[Span]:
    spans = _pad_to([(company, "bright")], COL_ROLE) + [(role, "primary")]
    return _right_align(spans, dates, "muted")


def experience_detail(tech: str, metric: str) -> list[Span]:
    return _right_align([("└─ ", "dim"), (tech, "muted")], metric, "green")


def project_head(name: str, domain: str) -> list[Span]:
    return _pad_to([(name, "blue")], COL_DOMAIN) + [(domain, "muted")]


def project_detail(what: str, tech: str) -> list[Span]:
    return [("└─ ", "dim"), (what, "primary"), ("  ·  ", "dim"), (tech, "muted")]


def stack_line(key: str, value: str) -> list[Span]:
    return _pad_to([(key, "muted")], COL_STACK) + [(value, "primary")]


# ---------------------------------------------------------------------------
# RENDERING
# ---------------------------------------------------------------------------

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
        self.text_x = MARGIN + PAD_X
        self.text_y = MARGIN + TITLEBAR_H + PAD_TOP
        text_bottom = HEIGHT - MARGIN - FOOTER_H - PAD_BOTTOM
        self.rows = int((text_bottom - self.text_y) // LINE_H)
        self.base = self._draw_window()

    def _draw_window(self) -> Image.Image:
        """Static chrome: canvas, body, title bar, status bar, border."""
        img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["canvas"])
        d = ImageDraw.Draw(img)
        box = (MARGIN, MARGIN, WIDTH - MARGIN - 1, HEIGHT - MARGIN - 1)
        d.rounded_rectangle(box, radius=CORNER, fill=COLORS["body"])

        # Title bar: rounded top, squared-off bottom edge.
        bar_bottom = box[1] + TITLEBAR_H
        d.rounded_rectangle((box[0], box[1], box[2], bar_bottom),
                            radius=CORNER, fill=COLORS["titlebar"])
        d.rectangle((box[0], bar_bottom - CORNER, box[2], bar_bottom),
                    fill=COLORS["titlebar"])
        d.line((box[0], bar_bottom, box[2], bar_bottom),
               fill=COLORS["border"], width=1)

        bar_mid = box[1] + TITLEBAR_H // 2
        d.text((self.text_x, bar_mid), TITLE_LEFT,
               font=self.font, fill=COLORS["muted"], anchor="lm")
        right = box[2] - PAD_X
        d.text((right, bar_mid), TITLE_RIGHT,
               font=self.font, fill=COLORS["muted"], anchor="rm")
        dot_x = right - self.font.getlength(TITLE_RIGHT) - 14
        d.ellipse((dot_x - 4, bar_mid - 4, dot_x + 4, bar_mid + 4),
                  fill=COLORS["green"])

        # Status bar: squared top, rounded bottom.
        foot_top = box[3] - FOOTER_H
        d.rounded_rectangle((box[0], foot_top, box[2], box[3]),
                            radius=CORNER, fill=COLORS["titlebar"])
        d.rectangle((box[0], foot_top, box[2], foot_top + CORNER),
                    fill=COLORS["titlebar"])
        d.line((box[0], foot_top, box[2], foot_top),
               fill=COLORS["border"], width=1)
        foot_mid = foot_top + FOOTER_H // 2
        d.text((self.text_x, foot_mid), FOOTER_LEFT,
               font=self.font, fill=COLORS["dim"], anchor="lm")
        d.text((right, foot_mid), FOOTER_RIGHT,
               font=self.font, fill=COLORS["dim"], anchor="rm")

        d.rounded_rectangle(box, radius=CORNER, outline=COLORS["border"], width=1)
        return img

    def frame(self, lines: list[list[Span]], cursor: bool) -> Image.Image:
        """Draw the visible rows; the cursor sits after the final line."""
        img = self.base.copy()
        d = ImageDraw.Draw(img)
        y = self.text_y
        for row, spans in enumerate(lines):
            x = self.text_x
            for text, color in spans:
                d.text((x, y), text, font=self.font, fill=COLORS[color])
                x += self.font.getlength(text)
            if cursor and row == len(lines) - 1:
                d.rectangle((x, y + 3, x + self.char_w - 1, y + self.ascent),
                            fill=COLORS["primary"])
            y += LINE_H
        return img


# ---------------------------------------------------------------------------
# SESSION DRIVER  --  scrollback, viewport, timeline
# ---------------------------------------------------------------------------

class Session:
    """Holds terminal scrollback and records (image, duration_ms) frames."""

    def __init__(self, renderer: Renderer) -> None:
        self.r = renderer
        self.history: list[list[Span]] = [list(PROMPT)]
        self.frames: list[tuple[Image.Image, int]] = []
        self.static: Image.Image | None = None
        self.rng = random.Random(7)

    def viewport(self) -> list[list[Span]]:
        """The tail of scrollback that fits on screen; older lines scroll off."""
        return self.history[-self.r.rows:]

    # -- frame emission ----------------------------------------------------
    def _emit(self, duration_ms: int, cursor: bool = True) -> None:
        self.frames.append((self.r.frame(self.viewport(), cursor), duration_ms))

    def hold(self, seconds: float) -> None:
        """Pause. Long pauses blink the cursor rather than freezing it."""
        ms = int(seconds * 1000)
        if ms <= BLINK_MS:
            self._emit(ms)
            return
        on = True
        while ms > 0:
            step = min(BLINK_MS, ms)
            if 0 < ms - step < 120:       # absorb a short remainder
                step = ms
            self._emit(step, cursor=on)
            on = not on
            ms -= step

    def mark_static(self) -> None:
        """Capture the current screen as the reduced-motion fallback."""
        self.static = self.r.frame(self.viewport(), cursor=True)

    # -- content -----------------------------------------------------------
    def type_command(self, command: str) -> None:
        """Commands animate character by character; output does not."""
        typed = ""
        for ch in command:
            typed += ch
            self.history[-1] = list(PROMPT) + [(typed, "primary")]
            self._emit(TYPE_MS + self.rng.randint(-TYPE_JITTER, TYPE_JITTER))
        self.hold(0.20)                   # beat before "enter"
        self.history.append([])

    def print(self, spans: list[Span], duration_ms: int = 190) -> None:
        """Print one output line, then park the cursor on the next row."""
        self.history[-1] = spans
        self.history.append([])
        self._emit(duration_ms)

    def blank(self) -> None:
        self.history[-1] = []
        self.history.append([])

    def prompt_only(self) -> None:
        self.history[-1] = list(PROMPT)
        self._emit(80)


# ---------------------------------------------------------------------------
# EXPORT
# ---------------------------------------------------------------------------

def export(session: Session) -> None:
    """Quantise every frame against one shared palette, then write the GIF."""
    GIF_PATH.parent.mkdir(parents=True, exist_ok=True)
    frames = session.frames
    static = session.static or frames[-1][0]

    # One shared palette across all frames avoids inter-frame colour flicker.
    # The palette is built from the densest screen so every colour is present.
    master = static.quantize(colors=PALETTE_COLORS,
                             method=Image.Quantize.MEDIANCUT)
    paletted = [img.quantize(palette=master, dither=Image.Dither.NONE)
                for img, _ in frames]

    paletted[0].save(
        GIF_PATH,
        save_all=True,
        append_images=paletted[1:],
        duration=[ms for _, ms in frames],
        loop=0,
        optimize=True,
        disposal=1,
    )
    static.save(PNG_PATH, optimize=True)


def main() -> None:
    font, font_path = load_font()
    renderer = Renderer(font)
    session = Session(renderer)
    build_session(session)
    export(session)

    total_ms = sum(ms for _, ms in session.frames)
    print(f"font        {font_path}")
    print(f"viewport    {renderer.rows} rows x "
          f"{int((WIDTH - 2 * MARGIN - 2 * PAD_X) / renderer.char_w)} cols")
    print(f"scrollback  {len(session.history)} lines")
    print(f"frames      {len(session.frames)}")
    print(f"duration    {total_ms / 1000:.2f}s "
          f"({len(session.frames) / (total_ms / 1000):.1f} fps avg)")
    print(f"gif         {WIDTH}x{HEIGHT}  {GIF_PATH.stat().st_size / 1024:.0f} KB")
    print(f"png         {WIDTH}x{HEIGHT}  {PNG_PATH.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
