#!/usr/bin/env python3
"""
Live Leaderboard
================

A lightweight, very colourful leaderboard for Linux desktops.
Standard library only (tkinter), no third-party packages, nothing read from or
written to disk. Rows slide into their new rank as scores change, every player
gets their own colour, and taking the lead sets off confetti.

Run:  python3 leaderboard.py
"""

import itertools
import random
import tkinter as tk
from tkinter import font as tkfont

APP_NAME = "Live Leaderboard"

# Every player gets one of these, in order.
PALETTE = [
    "#FF4D6D",  # raspberry
    "#FFA51F",  # mango
    "#2ED573",  # lime
    "#4C6FFF",  # blueberry
    "#B44DFF",  # grape
    "#00C2E0",  # lagoon
    "#FF7AC6",  # bubblegum
    "#FFD93D",  # banana
]

THEMES = {
    "candy": {
        "bg": "#FBF3FF", "panel": "#FFFFFF", "fg": "#2A1B45", "muted": "#7C6BA8",
        "field": "#F2EAFF", "row": "#FFFFFF", "tint": 0.86, "ink": 0.30,
    },
    "neon": {
        "bg": "#17122E", "panel": "#241C4C", "fg": "#F3EEFF", "muted": "#A192D8",
        "field": "#2C2258", "row": "#241C4C", "tint": 0.76, "ink": -0.25,
    },
}

SIZE_PRESETS = {
    "Cosy  660 x 480": (660, 480),
    "Standard  860 x 640": (860, 640),
    "Party mode  1200 x 760": (1200, 760),
}

CHEERS = [
    "Boom!", "Nice one!", "Up they go!", "Look at that!", "Big moves!",
    "Chef's kiss.", "Someone's on fire.", "Oh, it's on now.",
]


# --------------------------------------------------------------- tiny helpers

def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def mix(color_a, color_b, amount):
    """Blend color_a toward color_b. amount 0 = a, 1 = b."""
    a, b = hex_to_rgb(color_a), hex_to_rgb(color_b)
    return rgb_to_hex(a[i] + (b[i] - a[i]) * amount for i in range(3))


def shade(color, amount):
    """Positive amount darkens, negative lightens."""
    if amount >= 0:
        return mix(color, "#000000", amount)
    return mix(color, "#FFFFFF", -amount)


def fmt_score(value):
    """Show 12 instead of 12.0, but keep 12.5 intact."""
    return f"{value:g}"


def parse_score(text):
    try:
        return float(str(text).strip().replace(",", "."))
    except (ValueError, AttributeError):
        return None


def round_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# ------------------------------------------------------------------- the app

class LeaderboardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.minsize(520, 400)

        self.rows = {}          # iid -> {"name", "score", "color"}
        self.order = []         # iids, best first
        self.ranks = {}         # iid -> rank number
        self.pos = {}           # iid -> current y on the canvas
        self.pulse = {}         # iid -> 0..1 glow that decays
        self.confetti = []
        self.selected = None
        self.leader = None

        self._ids = itertools.count(1)
        self._colors = itertools.cycle(PALETTE)
        self._editor = None
        self._animating = False
        self._buttons = []
        self._fields = []
        self._chrome = []       # frames that follow the theme background
        self._labels = []       # text that follows the theme foreground

        self.theme_name = "candy"
        self.ui_scale = 1.0
        self.step_var = tk.StringVar(value="1")
        self.status_var = tk.StringVar(value="Nobody on the board yet. Add someone!")

        family = tkfont.nametofont("TkDefaultFont").cget("family")
        self.ui_font = tkfont.Font(family=family, size=10)
        self.btn_font = tkfont.Font(family=family, size=10, weight="bold")
        self.name_font = tkfont.Font(family=family, size=14, weight="bold")
        self.score_font = tkfont.Font(family=family, size=18, weight="bold")
        self.badge_font = tkfont.Font(family=family, size=13, weight="bold")
        self.title_font = tkfont.Font(family=family, size=22, weight="bold")
        self.empty_font = tkfont.Font(family=family, size=13)

        self._build_menu()
        self._build_layout()
        self.apply_theme()
        self.geometry("860x640")
        self.after(60, self.refresh)
        self.name_entry.focus_set()

    # ---------------------------------------------------------------- chrome

    def _build_menu(self):
        menubar = tk.Menu(self)

        board = tk.Menu(menubar, tearoff=0)
        board.add_command(label="New player", accelerator="Ctrl+N",
                          command=lambda: self.name_entry.focus_set())
        board.add_command(label="Remove selected", accelerator="Del",
                          command=self.remove_selected)
        board.add_separator()
        board.add_command(label="Reset all scores to 0", command=self.reset_scores)
        board.add_command(label="Clear the board", command=self.clear_board)
        board.add_separator()
        board.add_command(label="Quit", accelerator="Ctrl+Q", command=self.destroy)
        menubar.add_cascade(label="Board", menu=board)

        display = tk.Menu(menubar, tearoff=0)
        for label, (w, h) in SIZE_PRESETS.items():
            display.add_command(label=label,
                                command=lambda w=w, h=h: self.set_window_size(w, h))
        display.add_command(label="Custom size...", command=self.open_size_dialog)
        display.add_separator()
        display.add_command(label="Bigger", accelerator="Ctrl++",
                            command=lambda: self.bump_scale(0.1))
        display.add_command(label="Smaller", accelerator="Ctrl+-",
                            command=lambda: self.bump_scale(-0.1))
        display.add_command(label="Reset size", accelerator="Ctrl+0",
                            command=lambda: self.set_scale(1.0))
        display.add_separator()
        self.neon_var = tk.BooleanVar(value=False)
        display.add_checkbutton(label="Neon colours", variable=self.neon_var,
                                command=self.toggle_theme)
        self.full_var = tk.BooleanVar(value=False)
        display.add_checkbutton(label="Fullscreen", accelerator="F11",
                                variable=self.full_var, command=self.apply_fullscreen)
        menubar.add_cascade(label="Display", menu=display)

        fun = tk.Menu(menubar, tearoff=0)
        fun.add_command(label="Throw confetti", accelerator="Ctrl+Space",
                        command=lambda: self.throw_confetti(90))
        fun.add_command(label="Shuffle everyone's colour", command=self.reshuffle_colors)
        menubar.add_cascade(label="Fun", menu=fun)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Keyboard shortcuts", command=self.show_help)
        menubar.add_cascade(label="Help", menu=helpmenu)
        self.config(menu=menubar)

        self.bind("<Control-n>", lambda e: self.name_entry.focus_set())
        self.bind("<Control-q>", lambda e: self.destroy())
        self.bind("<Control-space>", lambda e: self.throw_confetti(90))
        self.bind("<Control-plus>", lambda e: self.bump_scale(0.1))
        self.bind("<Control-equal>", lambda e: self.bump_scale(0.1))
        self.bind("<Control-minus>", lambda e: self.bump_scale(-0.1))
        self.bind("<Control-0>", lambda e: self.set_scale(1.0))
        self.bind("<F11>", lambda e: (self.full_var.set(not self.full_var.get()),
                                      self.apply_fullscreen()))
        self.bind("<Escape>", self._on_escape)

    def _button(self, parent, text, color, command, width=None):
        btn = tk.Button(parent, text=text, command=command, font=self.btn_font,
                        bg=color, fg="#FFFFFF", activebackground=shade(color, 0.18),
                        activeforeground="#FFFFFF", relief="flat", bd=0,
                        highlightthickness=0, padx=14, pady=6, cursor="hand2")
        if width:
            btn.configure(width=width, padx=0)
        self._buttons.append(btn)
        return btn

    def _build_layout(self):
        root = tk.Frame(self)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)
        self._chrome.append(root)

        # Header: one colour per letter --------------------------------------
        header = tk.Frame(root)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        self._chrome.append(header)

        letters = tk.Frame(header)
        letters.pack(side="left")
        self._chrome.append(letters)
        self.title_letters = []
        for i, char in enumerate("LEADERBOARD"):
            lab = tk.Label(letters, text=char, font=self.title_font,
                           fg=PALETTE[i % len(PALETTE)])
            lab.pack(side="left")
            self.title_letters.append(lab)

        self.leader_label = tk.Label(header, text="", font=self.btn_font, anchor="e")
        self.leader_label.pack(side="right")

        # Controls ------------------------------------------------------------
        controls = tk.Frame(root)
        controls.grid(row=1, column=0, sticky="ew", padx=16, pady=(6, 10))
        self._chrome.append(controls)

        line1 = tk.Frame(controls)
        line1.pack(fill="x")
        self._chrome.append(line1)
        self._labels.append(self._plain(line1, "Name"))
        self.name_entry = self._entry(line1, 20)
        self.name_entry.pack(side="left", padx=(6, 14))
        self._labels.append(self._plain(line1, "Score"))
        self.score_entry = self._entry(line1, 7)
        self.score_entry.pack(side="left", padx=(6, 14))
        self._button(line1, "Add or update", PALETTE[3],
                     self.add_or_update).pack(side="left")

        line2 = tk.Frame(controls)
        line2.pack(fill="x", pady=(10, 0))
        self._chrome.append(line2)
        self._labels.append(self._plain(line2, "Nudge the selected player by"))
        self.step_box = tk.Spinbox(line2, from_=1, to=1000, width=4, justify="center",
                                   textvariable=self.step_var, font=self.ui_font,
                                   relief="flat", bd=0, highlightthickness=0,
                                   buttondownrelief="flat", buttonuprelief="flat")
        self.step_box.pack(side="left", padx=8)
        self._fields.append(self.step_box)
        self._button(line2, "\u2212", PALETTE[0], lambda: self.adjust(-1),
                     width=3).pack(side="left", padx=(0, 4))
        self._button(line2, "+", PALETTE[2], lambda: self.adjust(1),
                     width=3).pack(side="left", padx=(0, 16))
        self._button(line2, "Remove", PALETTE[4],
                     self.remove_selected).pack(side="left")
        self._button(line2, "Reset scores", PALETTE[5],
                     self.reset_scores).pack(side="left", padx=6)
        self._button(line2, "Clear board", PALETTE[1],
                     self.clear_board).pack(side="left")

        self.name_entry.bind("<Return>", lambda e: self.add_or_update())
        self.score_entry.bind("<Return>", lambda e: self.add_or_update())

        # The board -----------------------------------------------------------
        self.canvas = tk.Canvas(root, highlightthickness=0, bd=0, takefocus=1)
        self.canvas.grid(row=2, column=0, sticky="nsew", padx=16)
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Double-1>", self.on_double_click)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", lambda e: self._scroll(-1))
        self.canvas.bind("<Button-5>", lambda e: self._scroll(1))

        self.canvas.bind("<Delete>", lambda e: self.remove_selected())
        self.canvas.bind("<Up>", lambda e: self.move_selection(-1))
        self.canvas.bind("<Down>", lambda e: self.move_selection(1))
        self.canvas.bind("<plus>", lambda e: self.adjust(1))
        self.canvas.bind("<KP_Add>", lambda e: self.adjust(1))
        self.canvas.bind("<minus>", lambda e: self.adjust(-1))
        self.canvas.bind("<KP_Subtract>", lambda e: self.adjust(-1))

        # Status --------------------------------------------------------------
        self.status = tk.Label(root, textvariable=self.status_var, anchor="w",
                               font=self.ui_font)
        self.status.grid(row=3, column=0, sticky="ew", padx=16, pady=(10, 12))

    def _plain(self, parent, text):
        lab = tk.Label(parent, text=text, font=self.ui_font)
        lab.pack(side="left")
        return lab

    def _entry(self, parent, width):
        entry = tk.Entry(parent, width=width, font=self.ui_font, relief="flat",
                         bd=0, highlightthickness=2)
        self._fields.append(entry)
        return entry

    # ------------------------------------------------------- theme and sizing

    def apply_theme(self):
        c = THEMES[self.theme_name]
        self.configure(bg=c["bg"])
        for frame in self._chrome:
            frame.configure(bg=c["bg"])
        for lab in self.title_letters:
            lab.configure(bg=c["bg"])
        for lab in self._labels:
            lab.configure(bg=c["bg"], fg=c["muted"])
        self.leader_label.configure(bg=c["bg"], fg=c["muted"])
        self.status.configure(bg=c["bg"], fg=c["muted"])
        self.canvas.configure(bg=c["bg"])
        for field in self._fields:
            field.configure(bg=c["field"], fg=c["fg"], insertbackground=c["fg"],
                            highlightbackground=c["field"],
                            highlightcolor=PALETTE[3])
        self.step_box.configure(buttonbackground=c["field"])
        self.redraw()

    def toggle_theme(self):
        self.theme_name = "neon" if self.neon_var.get() else "candy"
        self.apply_theme()

    def apply_scale(self):
        s = self.ui_scale
        self.ui_font.configure(size=max(7, round(10 * s)))
        self.btn_font.configure(size=max(7, round(10 * s)))
        self.name_font.configure(size=max(9, round(14 * s)))
        self.score_font.configure(size=max(11, round(18 * s)))
        self.badge_font.configure(size=max(8, round(13 * s)))
        self.title_font.configure(size=max(13, round(22 * s)))
        self.empty_font.configure(size=max(9, round(13 * s)))
        self.layout_rows(animate=False)
        self.redraw()

    def set_scale(self, value):
        self.ui_scale = round(min(2.4, max(0.7, value)), 2)
        self.apply_scale()
        self.status_var.set(f"Size set to {int(self.ui_scale * 100)}%")

    def bump_scale(self, delta):
        self.set_scale(self.ui_scale + delta)

    def set_window_size(self, width, height):
        if self.full_var.get():
            self.full_var.set(False)
            self.apply_fullscreen()
        self.geometry(f"{int(width)}x{int(height)}")
        self.status_var.set(f"Window set to {int(width)} x {int(height)}")

    def apply_fullscreen(self):
        self.attributes("-fullscreen", self.full_var.get())

    def open_size_dialog(self):
        c = THEMES[self.theme_name]
        win = tk.Toplevel(self, bg=c["bg"])
        win.title("Window size")
        win.transient(self)
        win.resizable(False, False)

        body = tk.Frame(win, bg=c["bg"])
        body.pack(padx=18, pady=16)
        w_var = tk.StringVar(value=str(self.winfo_width()))
        h_var = tk.StringVar(value=str(self.winfo_height()))
        for i, (label, var) in enumerate((("Width", w_var), ("Height", h_var))):
            tk.Label(body, text=label, font=self.ui_font, bg=c["bg"],
                     fg=c["fg"]).grid(row=i, column=0, sticky="w", pady=5)
            tk.Spinbox(body, from_=520, to=4000, increment=20, width=8,
                       textvariable=var, font=self.ui_font, relief="flat", bd=0,
                       bg=c["field"], fg=c["fg"], buttonbackground=c["field"],
                       highlightthickness=0).grid(row=i, column=1, padx=(12, 0), pady=5)

        def apply_and_close():
            try:
                self.set_window_size(int(float(w_var.get())), int(float(h_var.get())))
            except ValueError:
                self.status_var.set("Width and height need to be numbers.")
            win.destroy()

        bar = tk.Frame(win, bg=c["bg"])
        bar.pack(padx=18, pady=(0, 16), fill="x")
        self._button(bar, "Apply", PALETTE[3], apply_and_close).pack(side="right")
        self._button(bar, "Cancel", PALETTE[4], win.destroy).pack(side="right", padx=8)
        win.bind("<Return>", lambda e: apply_and_close())
        win.bind("<Escape>", lambda e: win.destroy())

    def show_help(self):
        c = THEMES[self.theme_name]
        win = tk.Toplevel(self, bg=c["bg"])
        win.title("Keyboard shortcuts")
        win.transient(self)
        win.resizable(False, False)
        text = (
            "Enter\t\tAdd the typed player, or update their score\n"
            "Double click\tEdit a score right on the board\n"
            "Up / Down\tMove the selection\n"
            "Delete\t\tRemove the selected player\n"
            "Ctrl Space\tConfetti, for no reason at all\n"
            "Ctrl + / Ctrl -\tBigger or smaller\n"
            "Ctrl 0\t\tReset the size\n"
            "F11\t\tFullscreen on or off\n"
            "Ctrl Q\t\tQuit"
        )
        tk.Label(win, text=text, justify="left", font=self.ui_font, bg=c["bg"],
                 fg=c["fg"]).pack(padx=20, pady=18)
        self._button(win, "Got it", PALETTE[2], win.destroy).pack(pady=(0, 16))
        win.bind("<Escape>", lambda e: win.destroy())

    # ------------------------------------------------------------- board data

    def add_or_update(self):
        name = self.name_entry.get().strip()
        raw = self.score_entry.get().strip() or "0"
        score = parse_score(raw)
        if not name:
            self.status_var.set("Type a name first.")
            self.name_entry.focus_set()
            return
        if score is None:
            self.status_var.set(f"'{raw}' is not a number. Try 10 or 10.5.")
            self.score_entry.focus_set()
            return

        iid = self.find_by_name(name)
        if iid:
            self.rows[iid]["score"] = score
            note = f"{name} is on {fmt_score(score)}"
        else:
            iid = f"p{next(self._ids)}"
            self.rows[iid] = {"name": name, "score": score,
                              "color": next(self._colors)}
            note = f"{name} joins the board"
        self.selected = iid
        self.pulse[iid] = 1.0
        self.name_entry.delete(0, "end")
        self.score_entry.delete(0, "end")
        self.name_entry.focus_set()
        self.refresh(note=note)

    def find_by_name(self, name):
        lowered = name.lower()
        for iid, row in self.rows.items():
            if row["name"].lower() == lowered:
                return iid
        return None

    def adjust(self, direction):
        if not self.selected:
            self.status_var.set("Click a player on the board first.")
            return
        step = parse_score(self.step_var.get()) or 1
        row = self.rows[self.selected]
        row["score"] += direction * step
        self.pulse[self.selected] = 1.0
        cheer = random.choice(CHEERS) if direction > 0 else "Ouch."
        self.refresh(note=f"{row['name']} \u2192 {fmt_score(row['score'])}. {cheer}")

    def remove_selected(self):
        if not self.selected:
            self.status_var.set("Click a player to remove.")
            return
        name = self.rows.pop(self.selected)["name"]
        self.pos.pop(self.selected, None)
        self.selected = None
        self.refresh(note=f"{name} has left the board")

    def reset_scores(self):
        if not self.rows:
            return
        for iid, row in self.rows.items():
            row["score"] = 0.0
            self.pulse[iid] = 1.0
        self.refresh(note="Everyone back to zero. Fresh start!")

    def clear_board(self):
        self.rows.clear()
        self.pos.clear()
        self.pulse.clear()
        self.selected = None
        self.leader = None
        self.refresh(note="Board wiped clean")

    def reshuffle_colors(self):
        colors = PALETTE[:]
        random.shuffle(colors)
        for i, iid in enumerate(self.rows):
            self.rows[iid]["color"] = colors[i % len(colors)]
        self.refresh(note="New colours all round")

    def move_selection(self, delta):
        if not self.order:
            return
        if self.selected in self.order:
            index = (self.order.index(self.selected) + delta) % len(self.order)
        else:
            index = 0
        self.selected = self.order[index]
        self.load_selection()
        self.redraw()

    def load_selection(self):
        if self.selected not in self.rows:
            return
        row = self.rows[self.selected]
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, row["name"])
        self.score_entry.delete(0, "end")
        self.score_entry.insert(0, fmt_score(row["score"]))

    # ------------------------------------------------------------- geometry

    def metrics(self):
        s = self.ui_scale
        return {
            "s": s,
            "pad": 20 * s,
            "row_h": 62 * s,
            "gap": 8 * s,
            "radius": 16 * s,
            "badge_r": 20 * s,
            "left": 20 * s,
        }

    def layout_rows(self, animate=True):
        m = self.metrics()
        self.order = sorted(self.rows,
                            key=lambda i: (-self.rows[i]["score"],
                                           self.rows[i]["name"].lower()))
        self.ranks, rank, previous = {}, 0, None
        for index, iid in enumerate(self.order):
            score = self.rows[iid]["score"]
            if score != previous:
                rank, previous = index + 1, score
            self.ranks[iid] = rank
            target = m["pad"] + index * (m["row_h"] + m["gap"])
            if not animate:
                self.pos[iid] = target
            elif iid not in self.pos:
                self.pos[iid] = target + 46 * m["s"]
        for iid in list(self.pos):
            if iid not in self.rows:
                del self.pos[iid]

    def targets(self):
        m = self.metrics()
        return {iid: m["pad"] + i * (m["row_h"] + m["gap"])
                for i, iid in enumerate(self.order)}

    def row_at(self, y):
        m = self.metrics()
        for iid, top in self.pos.items():
            if top <= y <= top + m["row_h"]:
                return iid
        return None

    def _scroll(self, direction):
        self.canvas.yview_scroll(direction, "units")
        self.cancel_edit()

    def _on_wheel(self, event):
        self._scroll(-1 if event.delta > 0 else 1)

    # -------------------------------------------------------------- clicking

    def on_click(self, event):
        self.cancel_edit()
        self.canvas.focus_set()
        iid = self.row_at(self.canvas.canvasy(event.y))
        self.selected = iid
        if iid:
            self.load_selection()
        self.redraw()

    def on_double_click(self, event):
        y = self.canvas.canvasy(event.y)
        iid = self.row_at(y)
        if not iid:
            return
        self.selected = iid
        m = self.metrics()
        width = max(self.canvas.winfo_width(), 400)
        top = self.pos[iid]
        x1, x2 = width - 150 * m["s"], width - 16 * m["s"]
        y1, y2 = top + 12 * m["s"], top + m["row_h"] - 12 * m["s"]

        editor = tk.Entry(self.canvas, font=self.score_font, justify="right",
                          relief="flat", bd=0, highlightthickness=2,
                          bg=THEMES[self.theme_name]["field"],
                          fg=THEMES[self.theme_name]["fg"],
                          insertbackground=THEMES[self.theme_name]["fg"],
                          highlightcolor=self.rows[iid]["color"],
                          highlightbackground=self.rows[iid]["color"])
        editor.insert(0, fmt_score(self.rows[iid]["score"]))
        editor.select_range(0, "end")
        editor.place(x=x1, y=y1 - self.canvas.canvasy(0),
                     width=x2 - x1, height=y2 - y1)
        editor.focus_set()
        editor.bind("<Return>", lambda e: self.commit_from_editor(iid))
        editor.bind("<Escape>", lambda e: self.cancel_edit())
        editor.bind("<FocusOut>", lambda e: self.commit_from_editor(iid))
        self._editor = editor

    def commit_from_editor(self, iid):
        if self._editor is None or not self._editor.winfo_exists():
            return
        text = self._editor.get()
        self.cancel_edit()
        if iid not in self.rows:
            return
        score = parse_score(text)
        if score is None:
            self.status_var.set(f"'{text.strip()}' is not a number.")
            self.redraw()
            return
        self.rows[iid]["score"] = score
        self.pulse[iid] = 1.0
        self.refresh(note=f"{self.rows[iid]['name']} set to {fmt_score(score)}")

    def cancel_edit(self):
        editor, self._editor = self._editor, None
        if editor is not None and editor.winfo_exists():
            editor.destroy()

    def _on_escape(self, _event=None):
        if self._editor is not None:
            self.cancel_edit()
        elif self.full_var.get():
            self.full_var.set(False)
            self.apply_fullscreen()

    # ------------------------------------------------------------- confetti

    def throw_confetti(self, count=70):
        width = max(self.canvas.winfo_width(), 400)
        for _ in range(count):
            self.confetti.append({
                "x": random.uniform(0, width),
                "y": random.uniform(-160, -10),
                "vx": random.uniform(-1.6, 1.6),
                "vy": random.uniform(1.5, 5.0),
                "size": random.uniform(4, 9) * self.ui_scale,
                "color": random.choice(PALETTE),
                "round": random.random() < 0.4,
            })
        self.start_animation()

    # ------------------------------------------------------------- animation

    def start_animation(self):
        if not self._animating:
            self._animating = True
            self.after(16, self._tick)

    def _tick(self):
        busy = False
        height = max(self.canvas.winfo_height(), 200)

        for iid, target in self.targets().items():
            current = self.pos.get(iid, target)
            if abs(current - target) > 0.6:
                self.pos[iid] = current + (target - current) * 0.22
                busy = True
            else:
                self.pos[iid] = target

        for iid in list(self.pulse):
            self.pulse[iid] *= 0.90
            if self.pulse[iid] < 0.03:
                del self.pulse[iid]
            else:
                busy = True

        for flake in self.confetti:
            flake["vy"] += 0.14
            flake["x"] += flake["vx"]
            flake["y"] += flake["vy"]
        self.confetti = [f for f in self.confetti if f["y"] < height + 40]
        if self.confetti:
            busy = True

        self.redraw()
        if busy:
            self.after(16, self._tick)
        else:
            self._animating = False

    # ------------------------------------------------------------- rendering

    def refresh(self, note=None):
        previous_leader = self.leader
        self.layout_rows()
        self.leader = self.order[0] if self.order else None

        clear_lead = (len(self.order) > 1
                      and self.rows[self.order[0]]["score"]
                      > self.rows[self.order[1]]["score"])
        if self.leader and self.leader != previous_leader and clear_lead:
            self.throw_confetti(80)
            name = self.rows[self.leader]["name"]
            note = f"{name} takes the lead!"

        if self.leader:
            row = self.rows[self.leader]
            self.leader_label.configure(
                text=f"Leading: {row['name']} \u00b7 {fmt_score(row['score'])}",
                fg=shade(row["color"], THEMES[self.theme_name]["ink"]))
        else:
            self.leader_label.configure(text="",
                                        fg=THEMES[self.theme_name]["muted"])

        count = len(self.rows)
        label = "player" if count == 1 else "players"
        self.status_var.set(f"{note} \u00b7 {count} {label}" if note
                            else f"{count} {label} on the board")
        self.start_animation()
        self.redraw()

    def redraw(self):
        c = self.canvas
        c.delete("all")
        theme = THEMES[self.theme_name]
        m = self.metrics()
        width = max(c.winfo_width(), 400)
        height = max(c.winfo_height(), 200)

        if not self.rows:
            c.create_text(width / 2, height / 2 - 14 * m["s"],
                          text="The board is empty",
                          font=self.name_font, fill=theme["muted"])
            c.create_text(width / 2, height / 2 + 16 * m["s"],
                          text="Type a name and a score up top, then hit Enter.",
                          font=self.empty_font, fill=theme["muted"])
            self._draw_confetti()
            c.configure(scrollregion=(0, 0, width, height))
            return

        top_score = max((r["score"] for r in self.rows.values()), default=0)
        for iid in self.order:
            self._draw_row(iid, width, m, theme, top_score)

        self._draw_confetti()
        total = m["pad"] * 2 + len(self.order) * (m["row_h"] + m["gap"])
        c.configure(scrollregion=(0, 0, width, max(total, height)))

    def _draw_row(self, iid, width, m, theme, top_score):
        c = self.canvas
        row = self.rows[iid]
        color = row["color"]
        rank = self.ranks[iid]
        y = self.pos.get(iid, 0)
        glow = self.pulse.get(iid, 0.0)
        s = m["s"]

        fill = mix(color, theme["row"], theme["tint"] - 0.22 * glow)
        x1, x2 = 2, width - 4
        outline = color if (iid == self.selected or glow > 0.05) else fill
        round_rect(c, x1, y, x2, y + m["row_h"], m["radius"],
                   fill=fill, outline=outline, width=max(2, 2.5 * s))

        # Rank badge, with a crown for whoever is on top.
        cx = x1 + m["left"] + m["badge_r"]
        cy = y + m["row_h"] / 2
        r = m["badge_r"]
        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")
        c.create_text(cx, cy + 1, text=str(rank), font=self.badge_font,
                      fill="#FFFFFF")
        if rank == 1:
            cw, ch = r * 0.95, r * 0.75
            base = cy - r - 3 * s
            c.create_polygon(
                cx - cw, base,
                cx - cw, base - ch * 0.85,
                cx - cw * 0.45, base - ch * 0.35,
                cx, base - ch * 1.15,
                cx + cw * 0.45, base - ch * 0.35,
                cx + cw, base - ch * 0.85,
                cx + cw, base,
                fill="#FFC93D", outline=shade("#FFC93D", 0.18), width=max(1, s))

        # Name and the score bar.
        text_x = cx + r + 18 * s
        ink = shade(color, theme["ink"])
        room = max(40, width - 170 * s - text_x)
        c.create_text(text_x, cy - 11 * s, text=self._fit(row["name"], room),
                      anchor="w", font=self.name_font, fill=theme["fg"])

        bar_x2 = width - 160 * s
        bar_y = cy + 13 * s
        bar_h = 9 * s
        if bar_x2 > text_x + 30 * s:
            round_rect(c, text_x, bar_y, bar_x2, bar_y + bar_h, bar_h / 2,
                       fill=mix(fill, theme["fg"], 0.10), outline="")
            share = row["score"] / top_score if top_score > 0 else 0
            share = max(0.0, min(1.0, share))
            filled = text_x + (bar_x2 - text_x) * share
            if filled > text_x + bar_h:
                round_rect(c, text_x, bar_y, filled, bar_y + bar_h, bar_h / 2,
                           fill=color, outline="")

        c.create_text(width - 20 * s, cy, text=fmt_score(row["score"]), anchor="e",
                      font=self.score_font, fill=ink)

    def _fit(self, text, room):
        """Shorten a name with an ellipsis so it never collides with the score."""
        if self.name_font.measure(text) <= room:
            return text
        cut = text
        while cut and self.name_font.measure(cut + "\u2026") > room:
            cut = cut[:-1]
        return (cut + "\u2026") if cut else ""

    def _draw_confetti(self):
        c = self.canvas
        for flake in self.confetti:
            x, y, size = flake["x"], flake["y"], flake["size"]
            if flake["round"]:
                c.create_oval(x, y, x + size, y + size,
                              fill=flake["color"], outline="")
            else:
                c.create_rectangle(x, y, x + size * 1.6, y + size * 0.8,
                                   fill=flake["color"], outline="")


if __name__ == "__main__":
    LeaderboardApp().mainloop()
