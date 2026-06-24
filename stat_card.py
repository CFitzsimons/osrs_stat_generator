"""
OSRS skills tab PNG renderer (headless library).

Composites digit sprites onto Card.png at fixed grid positions for the
post-Sailing 24-skill layout (3 columns × 8 rows).
"""

from __future__ import annotations

import os
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image

ASSET_DIR = Path(__file__).resolve().parent

# Source template geometry (blank_stats at 759×1024) → scaled to CARD size.
_BLANK_W, _BLANK_H = 759, 1024
CARD_W, CARD_H = 204, 275
_SCALE_X = CARD_W / _BLANK_W
_SCALE_Y = CARD_H / _BLANK_H
_GRID_LEFT, _GRID_RIGHT, _GRID_TOP, _GRID_BOTTOM = 42, 717, 38, 932
_COL_W = (_GRID_RIGHT - _GRID_LEFT) / 3
_ROW_H = (_GRID_BOTTOM - _GRID_TOP) / 8
# Anchor within each cell (right of icon, vertically centred on level text).
_CELL_X_FRAC = 0.62
_CELL_Y_FRAC = 0.55

# Column-major skill order matching the live OSRS Skills tab.
SKILL_COLUMNS: list[list[str]] = [
    ["attack", "strength", "defence", "ranged", "prayer", "magic", "cooking", "woodcutting"],
    ["hitpoints", "agility", "herblore", "thieving", "crafting", "fletching", "firemaking", "fishing"],
    ["mining", "smithing", "farming", "runecrafting", "slayer", "hunter", "construction", "sailing"],
]

SKILL_LIST: list[str] = [skill for column in SKILL_COLUMNS for skill in column]

# Render tuning — adjust when iterating on Card.png alignment.
SKILL_LEVEL_HEIGHT = 11
TOTAL_LEVEL_HEIGHT = 13
TWO_DIGIT_X_NUDGE = 3


def _cell_digit_pos(col: int, row: int) -> tuple[int, int]:
    x = int((_GRID_LEFT + col * _COL_W + _COL_W * _CELL_X_FRAC) * _SCALE_X)
    y = int((_GRID_TOP + row * _ROW_H + _ROW_H * _CELL_Y_FRAC) * _SCALE_Y)
    return x, y


def _build_skill_positions() -> dict[str, tuple[int, int]]:
    positions: dict[str, tuple[int, int]] = {}
    for col_idx, column in enumerate(SKILL_COLUMNS):
        for row_idx, skill in enumerate(column):
            positions[skill] = _cell_digit_pos(col_idx, row_idx)
    return positions


SKILL_POSITIONS = _build_skill_positions()

# Centre of the total-level bar at the bottom of the tab.
TOTAL_LEVEL_POSITION = (
    int((_GRID_LEFT + _GRID_RIGHT) / 2 * _SCALE_X),
    int((_GRID_BOTTOM + (_BLANK_H - _GRID_BOTTOM) * 0.45) * _SCALE_Y),
)

# Display names for the Tkinter UI.
SKILL_LABELS: dict[str, str] = {
    "hitpoints": "Hitpoints",
    "runecrafting": "Runecrafting",
    **{s: s.capitalize() for s in SKILL_LIST if s not in ("hitpoints", "runecrafting")},
}


def resource_path(relative_path: str | os.PathLike[str]) -> str:
    """Absolute path to a bundled asset (dev or PyInstaller)."""
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        base_path = str(ASSET_DIR)
    return os.path.join(base_path, os.fspath(relative_path))


def _digit_image_path(digit: str) -> str:
    """Resolve digit sprite (repo ships both .png and .PNG)."""
    for name in (f"{digit}.png", f"{digit}.PNG"):
        path = resource_path(name)
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(f"Digit sprite not found for {digit!r}")


def _render_digit_image(num: int) -> Image.Image:
    """Composite level digits into a single RGBA image."""
    num_str = str(num)
    if len(num_str) > 1:
        canvas = Image.new("RGBA", (50, 60), (0, 0, 0, 0))
        for i, ch in enumerate(num_str):
            digit = Image.open(_digit_image_path(ch))
            canvas.paste(digit, (i * 24, 0), digit.convert("RGBA"))
        return canvas
    return Image.open(_digit_image_path(num_str)).copy()


def _scale_to_height(img: Image.Image, height: int) -> Image.Image:
    w, h = img.size
    if h <= 0:
        return img
    width = max(1, round(w * height / h))
    return img.resize((width, height), Image.Resampling.NEAREST)


def _paste_level(background: Image.Image, level: int, skill: str) -> None:
    pos = SKILL_POSITIONS[skill]
    front = _scale_to_height(_render_digit_image(level), SKILL_LEVEL_HEIGHT)
    front = front.convert("RGBA")
    x, y = pos
    if level >= 10:
        x -= TWO_DIGIT_X_NUDGE
    background.paste(front, (x, y), front)


def _paste_total(background: Image.Image, total: int) -> None:
    num_str = str(total)
    width = 25 * len(num_str)
    canvas = Image.new("RGBA", (width, 60), (0, 0, 0, 0))
    for i, ch in enumerate(num_str):
        digit = Image.open(_digit_image_path(ch))
        canvas.paste(digit, (i * 25, 0), digit.convert("RGBA"))

    front = _scale_to_height(canvas, TOTAL_LEVEL_HEIGHT)
    front = front.convert("RGBA")
    x = TOTAL_LEVEL_POSITION[0] - front.width // 2
    y = TOTAL_LEVEL_POSITION[1] - front.height // 2
    background.paste(front, (x, y), front)


def render_stat_card(levels: dict[str, int], total: int | None = None) -> Image.Image:
    """
    Render a skills tab PNG.

    Args:
        levels: Skill id → level (e.g. {"attack": 99, "sailing": 75}).
        total: Total level; computed from levels if omitted.

    Returns:
        RGBA PIL Image (204×275).
    """
    card = Image.open(resource_path("Card.png")).convert("RGBA")

    if total is None:
        total = sum(levels.get(skill, 1) for skill in SKILL_LIST)

    for skill in SKILL_LIST:
        level = max(1, min(99, int(levels.get(skill, 1))))
        _paste_level(card, level, skill)

    _paste_total(card, total)
    return card


def render_stat_card_bytes(levels: dict[str, int], total: int | None = None) -> bytes:
    """Render skills tab PNG and return raw bytes."""
    buf = BytesIO()
    render_stat_card(levels, total).save(buf, format="PNG")
    return buf.getvalue()


def levels_from_names(name_levels: dict[str, int]) -> dict[str, int]:
    """Map display names (Attack, Hitpoints, …) to internal skill ids."""
    name_to_id = {label: sid for sid, label in SKILL_LABELS.items()}
    name_to_id.update({
        "Attack": "attack",
        "Strength": "strength",
        "Defence": "defence",
        "Ranged": "ranged",
        "Prayer": "prayer",
        "Magic": "magic",
        "Cooking": "cooking",
        "Woodcutting": "woodcutting",
        "Hitpoints": "hitpoints",
        "Agility": "agility",
        "Herblore": "herblore",
        "Thieving": "thieving",
        "Crafting": "crafting",
        "Fletching": "fletching",
        "Firemaking": "firemaking",
        "Fishing": "fishing",
        "Mining": "mining",
        "Smithing": "smithing",
        "Farming": "farming",
        "Runecraft": "runecrafting",
        "Runecrafting": "runecrafting",
        "Slayer": "slayer",
        "Hunter": "hunter",
        "Construction": "construction",
        "Sailing": "sailing",
    })
    result: dict[str, int] = {}
    for name, level in name_levels.items():
        skill_id = name_to_id.get(name)
        if skill_id:
            result[skill_id] = level
    return result
