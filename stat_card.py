"""
OSRS skills tab PNG renderer (headless library).

Draws level text with the bundled RuneScape chat font onto Card.png.
Positions calibrated against the blank_stats template and reference output.
"""

from __future__ import annotations

import os
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSET_DIR = Path(__file__).resolve().parent

CARD_W, CARD_H = 204, 275

# Level text anchors (measured from reference render on 204×275 blank).
DIGIT_X = (45, 106, 166)
ROW_Y = (26, 56, 86, 116, 146, 176, 206, 236)
TOTAL_Y = 255
TOTAL_CENTER_X = 102

SKILL_FONT_SIZE = 12
TOTAL_FONT_SIZE = 11
FONT_FILE = "RuneScape-Chat-Bold-07.ttf"
TEXT_COLOR = (255, 255, 0)

# Column-major order matching icons on Card.png (classic tab + Sailing bottom-right).
# Note: differs from the post-Sailing Jagex hiscores API order — levels are keyed by
# skill id so each stat still lands on the correct icon.
SKILL_COLUMNS: list[list[str]] = [
    ["attack", "strength", "defence", "ranged", "prayer", "magic", "runecrafting", "construction"],
    ["hitpoints", "agility", "herblore", "thieving", "crafting", "fletching", "slayer", "hunter"],
    ["mining", "smithing", "fishing", "cooking", "firemaking", "woodcutting", "farming", "sailing"],
]

SKILL_LIST: list[str] = [skill for column in SKILL_COLUMNS for skill in column]

SKILL_LABELS: dict[str, str] = {
    "hitpoints": "Hitpoints",
    "runecrafting": "Runecrafting",
    **{s: s.capitalize() for s in SKILL_LIST if s not in ("hitpoints", "runecrafting")},
}

_FONTS: dict[int, ImageFont.FreeTypeFont] = {}


def _build_skill_positions() -> dict[str, tuple[int, int]]:
    positions: dict[str, tuple[int, int]] = {}
    for col_idx, column in enumerate(SKILL_COLUMNS):
        for row_idx, skill in enumerate(column):
            positions[skill] = (DIGIT_X[col_idx], ROW_Y[row_idx])
    return positions


SKILL_POSITIONS = _build_skill_positions()


def resource_path(relative_path: str | os.PathLike[str]) -> str:
    """Absolute path to a bundled asset (dev or PyInstaller)."""
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        base_path = str(ASSET_DIR)
    return os.path.join(base_path, os.fspath(relative_path))


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    if size in _FONTS:
        return _FONTS[size]
    path = resource_path(FONT_FILE)
    try:
        font = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.BASIC)
    except (TypeError, AttributeError):
        font = ImageFont.truetype(path, size)
    _FONTS[size] = font
    return font


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    font_size: int,
    center_x: int | None = None,
) -> None:
    font = _load_font(font_size)
    x, y = xy
    if center_x is not None:
        bbox = draw.textbbox((0, 0), text, font=font)
        x = center_x - (bbox[2] - bbox[0]) // 2
    draw.text((x, y), text, TEXT_COLOR, font=font)


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
    draw = ImageDraw.Draw(card)

    if total is None:
        total = sum(levels.get(skill, 1) for skill in SKILL_LIST)

    for skill in SKILL_LIST:
        level = max(1, min(99, int(levels.get(skill, 1))))
        x, y = SKILL_POSITIONS[skill]
        _draw_text(draw, (x, y), str(level), font_size=SKILL_FONT_SIZE)

    _draw_text(
        draw,
        (TOTAL_CENTER_X, TOTAL_Y),
        str(total),
        font_size=TOTAL_FONT_SIZE,
        center_x=TOTAL_CENTER_X,
    )
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
