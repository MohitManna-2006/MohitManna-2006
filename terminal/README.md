# terminal

Generator for the animated terminal shown at the top of the profile README.

`generate_terminal.py` renders every frame with Pillow and writes both assets
itself — there are no intermediate frame files to manage, and nothing here is
hand-edited after generation.

The terminal keeps a scrollback buffer and renders only the tail that fits on
screen, so output accumulates and older lines scroll off the top the way a real
session behaves. The session is longer than the viewport by design.

## Requirements

- Python 3.9 or newer
- Pillow (see `requirements.txt`)
- A monospace TrueType font

The script searches for a font in this order, taking the first one it finds:
Menlo and SF Mono (macOS), DejaVu Sans Mono and Liberation Mono (Linux),
Courier New, then Consolas (Windows). To force a specific face:

```bash
PROFILE_TERMINAL_FONT=/path/to/font.ttf python terminal/generate_terminal.py
```

If no font is found the script exits with a message rather than falling back to
an unreadable bitmap default.

## Regenerating

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r terminal/requirements.txt
python terminal/generate_terminal.py
```

Output, overwritten in place:

```
assets/terminal.gif         animated hero
assets/terminal-static.png  final frame, reduced-motion fallback
```

The script prints the font it resolved, the frame count, the duration, and the
size of each asset.

## Editing

Two places in `generate_terminal.py` cover almost every change:

- **`CONFIGURATION`** — dimensions, palette, font size, line height, typing
  speed, cursor blink rate, GIF palette size, and the column positions
  (`RIGHT_EDGE`, `COL_ROLE`, `COL_DOMAIN`, `COL_STACK`) that everything aligns
  against.
- **`CONTENT`** — the profile data itself: `BOOT`, `IDENTITY`, `EXPERIENCE`,
  `PROJECTS`, `STACK`. Editing a company, role, date, project, or technology
  means editing a tuple here and nothing else.

`build_session()` sets the order commands run in, and `mark_static()` picks
which screen becomes the fallback PNG. The line builders (`experience_head`,
`project_detail`, ...) turn content tuples into aligned coloured spans; they are
the only place layout maths lives.

Commands animate character by character. Output prints a line at a time, much
faster — that contrast is what makes the session feel real.

Frames are emitted with individual durations rather than at a fixed frame rate,
so a long pause costs one or two frames instead of thirty. Every frame is
quantised against a single shared palette, which is what keeps the GIF small and
free of inter-frame colour flicker.
