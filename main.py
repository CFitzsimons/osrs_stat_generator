"""OSRS Stat Generator — Tkinter UI for stat_card.render_stat_card."""

from __future__ import annotations

import glob
import os
import tkinter as tk
from tkinter import Canvas, Entry, Label, Button

from PIL import Image, ImageTk

from stat_card import SKILL_COLUMNS, SKILL_LABELS, SKILL_LIST, render_stat_card, resource_path

Font_tuple = ("Unispace", 15)
entries: list[Entry] = []


def _build_ui(root: tk.Tk) -> None:
    root.title("OSRS Stat Generator")
    root.geometry("670x620")
    root.configure(background="#40362C")

    title_img = Image.open(resource_path("osrs_title_2.png")).convert("RGBA")
    title_img.thumbnail((500, 500), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(title_img)
    label = tk.Label(image=photo, background="#40362C", anchor="center")
    label.image = photo
    label.grid(column=0, columnspan=6, sticky="e")

    for col_idx, column in enumerate(SKILL_COLUMNS):
        label_col = col_idx * 2
        entry_col = col_idx * 2 + 1
        for row_idx, skill in enumerate(column):
            grid_row = row_idx + 1
            lbl = Label(
                root,
                text=SKILL_LABELS[skill],
                background="#40362C",
                fg="yellow",
                padx=20 if col_idx == 0 else 0,
            )
            lbl.configure(font=Font_tuple)
            lbl.grid(column=label_col, row=grid_row)

            txt = Entry(root, width=5, background="#40362C", fg="yellow")
            txt.insert(0, "1")
            txt.configure(font=Font_tuple)
            txt.grid(column=entry_col, row=grid_row)
            entries.append(txt)

    total_lbl = Label(root, text="Total Level: 24", background="#40362C", fg="yellow")
    total_lbl.configure(font=Font_tuple)
    total_lbl.grid(column=4, row=9, columnspan=2)

    def on_generate() -> None:
        levels = {skill: int(entries[i].get()) for i, skill in enumerate(SKILL_LIST)}
        total = sum(levels.values())

        total_lbl.configure(text=f"Total Level: {total}")

        result_img = render_stat_card(levels, total)
        out_path = os.path.join(os.path.abspath("."), "Result.png")
        result_img.save(out_path, format="PNG")

        # Clean temp digit images
        for path in glob.glob(os.path.join(resource_path("images"), "*")):
            os.remove(path)

        window = tk.Toplevel()
        window.title("OSRS Stat Result")
        window.configure(background="#40362C")
        canvas = Canvas(window, width=300, height=300)
        canvas.pack()
        preview = ImageTk.PhotoImage(result_img)
        canvas.create_image(20, 20, anchor="nw", image=preview)
        canvas.image = preview

    btn = Button(
        root,
        text="Generate Stats",
        fg="yellow",
        command=on_generate,
        background="#40362C",
        pady=0,
    )
    btn.configure(font=Font_tuple)
    btn.grid(column=2, row=11, columnspan=2, pady=20)


def main() -> None:
    root = tk.Tk()
    _build_ui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
