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

# Column-major skill order matching the live OSRS Skills tab.
SKILL_COLUMNS: list[list[str]] = [
    ["attack", "strength", "defence", "ranged", "prayer", "magic", "cooking", "woodcutting"],
    ["hitpoints", "agility", "herblore", "thieving", "crafting", "fletching", "firemaking", "fishing"],
    ["mining", "smithing", "farming", "runecrafting", "slayer", "hunter", "construction", "sailing"],
]

SKILL_LIST: list[str] = [skill for column in SKILL_COLUMNS for skill in column]

ICON_X = (42, 105, 168)
DIGIT_X = (59, 122, 185)
ROW_ICON_Y = (13, 45, 77, 109, 141, 173, 205, 237)
ROW_DIGIT_Y = (26, 58, 90, 122, 154, 186, 218, 250)

TOTAL_LEVEL_POSITION = (155, 250)


def _build_skill_positions() -> dict[str, tuple[tuple[int, int], tuple[int, int]]]:
    positions: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {}
    for col_idx, column in enumerate(SKILL_COLUMNS):
        for row_idx, skill in enumerate(column):
            icon_pos = (ICON_X[col_idx], ROW_ICON_Y[row_idx])
            digit_pos = (DIGIT_X[col_idx], ROW_DIGIT_Y[row_idx])
            positions[skill] = (icon_pos, digit_pos)
    return positions


SKILL_POSITIONS = _build_skill_positions()

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


def _images_dir() -> str:
    path = resource_path("images")
    os.makedirs(path, exist_ok=True)
    return path


def _digit_image_path(digit: str) -> str:
    """Resolve digit sprite (repo ships both .png and .PNG)."""
    for name in (f"{digit}.png", f"{digit}.PNG"):
        path = resource_path(name)
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(f"Digit sprite not found for {digit!r}")


def _create_digit_image(num: int, suffix: str) -> str:
    """Render level digits to a temporary PNG; return its path."""
    num_str = str(num)
    out_path = os.path.join(_images_dir(), f"{num_str}{suffix}.png")

    if len(num_str) > 1:
        canvas = Image.new("RGBA", (50, 60), (0, 0, 0, 0))
        for i, ch in enumerate(num_str):
            digit = Image.open(_digit_image_path(ch))
            canvas.paste(digit, (i * 24, 0), digit.convert("RGBA"))
    else:
        digit = Image.open(_digit_image_path(num_str))
        canvas = digit.copy()

    canvas.save(out_path, format="PNG")
    return out_path


def _paste_level(
    background: Image.Image,
    level: int,
    skill: str,
) -> None:
    icon_pos, digit_pos = SKILL_POSITIONS[skill]
    digit_path = _create_digit_image(level, skill)
    front = Image.open(digit_path)
    size = (10, 10) if level < 10 else (15, 15)
    front.thumbnail(size, Image.Resampling.LANCZOS)
    front = front.convert("RGBA")

    background.paste(front, icon_pos, front)
    if level < 10:
        background.paste(front, digit_pos, front)
    else:
        background.paste(front, (digit_pos[0] - 5, digit_pos[1]), front)


def _paste_total(background: Image.Image, total: int) -> None:
    num_str = str(total)
    out_path = os.path.join(_images_dir(), f"{num_str}total.png")

    width = 25 * len(num_str)
    canvas = Image.new("RGBA", (width, 60), (0, 0, 0, 0))
    for i, ch in enumerate(num_str):
        digit = Image.open(_digit_image_path(ch))
        canvas.paste(digit, (i * 25, 0), digit.convert("RGBA"))
    canvas.save(out_path, format="PNG")

    front = Image.open(out_path)
    if total > 999:
        size = (25, 25)
        position = TOTAL_LEVEL_POSITION
    elif total > 99:
        size = (19, 19)
        position = (TOTAL_LEVEL_POSITION[0] + 3, TOTAL_LEVEL_POSITION[1])
    else:
        size = (15, 15)
        position = (TOTAL_LEVEL_POSITION[0] + 5, TOTAL_LEVEL_POSITION[1])

    front.thumbnail(size, Image.Resampling.LANCZOS)
    front = front.convert("RGBA")
    background.paste(front, position, front)


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
