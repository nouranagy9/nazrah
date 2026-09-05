import os
import tkinter as tk
from collections import namedtuple

# A single selectable cell: id is what on_select/hit_test deal in, icon +
# text are what's drawn. Deliberately not tied to phrases.Phrase — the
# home screen's cells ("turn off light", "needs") aren't phrases at all.
GridItem = namedtuple("GridItem", ["id", "icon", "text"])

# Sized for a patient who may be viewing the screen from a bed at some
# distance, on a full-HD (1920x1080) kiosk display with only a handful of
# large cells — legibility matters far more here than fitting more on
# screen. Bumped up from an initial pass that looked fine on a dev monitor
# but was reported too small once actually seen on the deployed screen.
ICON_FONT_SIZE = 64
TEXT_FONT_SIZE = 40


class GridUI:
    """Tkinter grid of selectable cells with Arabic labels. Call
    `set_active_cell` every frame with the cell id currently being gazed
    at (or None) and a dwell progress in [0, 1] so the cell fills in as
    the user's gaze lingers.

    One window is created up front and reused for the whole session —
    `show()` swaps which cells are displayed (e.g. switching from the home
    screen to the needs grid) without recreating the window or requiring
    a fresh calibration, since calibration only depends on screen
    dimensions, not on what's currently drawn.
    """

    def __init__(self, on_select, items, columns, font_family, font_file=None):
        self.on_select = on_select
        self._font_family = font_family
        # Tk's native font engine on the deployed Pi turned out to only see
        # 28 ancient X-core PostScript fonts — none of them Arabic-capable —
        # regardless of what's installed system-wide (see config.py's
        # GRID_FONT_FAMILY comment). Found on real hardware: icons rendered
        # but every phrase's Arabic text was just blank space. Root cause:
        # the Python 3.11 interpreter this project runs under on the Pi
        # (installed via `uv` specifically to get a working mediapipe —
        # see docs/raspberry_pi_setup.md) bundles its own private Tcl/Tk
        # 9.0 that has no Xft/fontconfig/TrueType support at all, so no
        # font file installed on the system can ever reach it.
        #
        # When font_file points at an actual TrueType font, phrase text is
        # rendered to a bitmap with Pillow (which links its own FreeType +
        # raqm, entirely bypassing Tk's font engine) instead. That bitmap
        # is shown via a plain Label(image=...), which Tk can always
        # display regardless of its own font capabilities. Left None (the
        # default, and what the Windows dev setup uses), cells fall back
        # to normal Tk-drawn text, since Windows already renders Arabic
        # correctly via the OS's own font substitution.
        self._font_file = font_file
        self._pil_font = None  # lazily loaded once, not per cell — see show()
        self._text_photos = {}
        self.root = tk.Tk()
        self.root.title("نظرة — Nazrah")
        self.root.configure(bg="black")
        # Fullscreen so the grid actually spans the whole screen — the
        # calibration in main.py maps gaze to full-screen coordinates
        # (winfo_screenwidth/height), so the grid has to occupy that same
        # coordinate space or hit-testing will never line up. This also
        # doubles as the natural layout for a dedicated kiosk-style device.
        self.root.attributes("-fullscreen", True)
        self.closed = False
        self.root.bind("<Escape>", lambda event: self._on_close())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._cells = {}
        self._active_id = None
        self._calib_window = None
        self._frame = None

        self.show(items, columns)

    def show(self, items, columns):
        """Replaces the currently displayed cells with a new set — how
        screens are switched (see main.py's SCREEN_HOME/SCREEN_NEEDS)."""
        if self._frame is not None:
            self._frame.destroy()

        self._cells = {}
        self._active_id = None
        self._text_photos = {}

        frame = tk.Frame(self.root, bg="black")
        frame.pack(expand=True, fill="both")
        self._frame = frame

        rows = -(-len(items) // columns)  # ceil division
        for col in range(columns):
            frame.columnconfigure(col, weight=1)
        for row in range(rows):
            frame.rowconfigure(row, weight=1)

        for index, item in enumerate(items):
            row, col = divmod(index, columns)
            cell = tk.Frame(frame, bg="#1e1e1e", relief="ridge", borderwidth=2)
            cell.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

            icon_label = tk.Label(
                cell,
                text=item.icon,
                font=(self._font_family, ICON_FONT_SIZE),
                bg="#1e1e1e",
                fg="white",
            )
            icon_label.pack(expand=True)

            text_widget = self._make_text_label(cell, item)
            text_widget.pack(expand=True)

            self._cells[item.id] = cell

    def _make_text_label(self, parent, item):
        """Renders a cell's phrase text as a plain Tk label, or — when
        font_file is set — as a bitmap via Pillow (see __init__)."""
        if self._font_file and os.path.isfile(self._font_file):
            from PIL import Image, ImageDraw, ImageFont, ImageTk

            if self._pil_font is None:
                # Loaded once and reused, not once per cell per screen —
                # re-reading/parsing the font file on every single cell
                # measured at ~380ms each on the Pi, adding up to a
                # multi-second freeze on every screen switch.
                self._pil_font = ImageFont.truetype(self._font_file, TEXT_FONT_SIZE)
            font = self._pil_font
            # direction="rtl" hands shaping AND reordering to Pillow's
            # bundled raqm (harfbuzz + fribidi) in one pass. An earlier
            # version of this manually reshaped letterforms with
            # arabic_reshaper and then bidi-reordered with python-bidi —
            # raqm does both itself, and doing both again on top of it
            # reordered an already-correctly-ordered string, which is what
            # made phrase text render backwards on real hardware.
            probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
            x0, y0, x1, y1 = probe.textbbox(
                (0, 0), item.text, font=font, direction="rtl"
            )
            img = Image.new("RGBA", (x1 - x0 + 8, y1 - y0 + 8), (0, 0, 0, 0))
            ImageDraw.Draw(img).text(
                (4 - x0, 4 - y0),
                item.text,
                font=font,
                fill=(255, 255, 255, 255),
                direction="rtl",
            )
            photo = ImageTk.PhotoImage(img)
            self._text_photos[item.id] = photo  # keep alive — Tk drops GC'd images
            return tk.Label(parent, image=photo, bg="#1e1e1e")

        return tk.Label(
            parent,
            text=item.text,
            font=(self._font_family, TEXT_FONT_SIZE),
            bg="#1e1e1e",
            fg="white",
        )

    def _set_cell_bg(self, cell_id, color):
        cell = self._cells[cell_id]
        cell.configure(bg=color)
        for child in cell.winfo_children():
            child.configure(bg=color)

    def set_active_cell(self, cell_id, progress=0.0):
        if cell_id != self._active_id and self._active_id is not None:
            self._set_cell_bg(self._active_id, "#1e1e1e")
        self._active_id = cell_id
        if cell_id is not None:
            self._set_cell_bg(cell_id, self._progress_color(progress))

    @staticmethod
    def _progress_color(progress):
        green = int(30 + progress * 150)
        return f"#1e{green:02x}3c"

    def flash_selection(self, cell_id):
        self._set_cell_bg(cell_id, "#2e7d32")

        def revert():
            try:
                self._set_cell_bg(cell_id, "#1e1e1e")
            except tk.TclError:
                # The cell's widget may have been destroyed by a show()
                # (screen switch) or window close in the 400ms since this
                # was scheduled — nothing to revert in that case.
                pass

        self.root.after(400, revert)

    def update(self):
        if self.closed:
            return
        self.root.update_idletasks()
        self.root.update()

    def _on_close(self):
        self.closed = True
        self.root.destroy()

    def cell_bbox(self, cell_id):
        cell = self._cells[cell_id]
        x = cell.winfo_rootx()
        y = cell.winfo_rooty()
        return x, y, x + cell.winfo_width(), y + cell.winfo_height()

    def hit_test(self, screen_x, screen_y):
        """Returns whichever cell's center is closest to the given screen
        point. Deliberately not exact-bbox containment: the grid has small
        gaps between cells (padding) and, when the item count isn't a
        multiple of `columns`, an incomplete last row — both of which would
        otherwise create dead zones a calibrated point could land in and
        get no match at all. Always resolving to the nearest cell means
        gaze always lands on *something*, which matters more here than
        precise boundaries."""
        best_id = None
        best_dist = None
        for cell_id in self._cells:
            x1, y1, x2, y2 = self.cell_bbox(cell_id)
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            dist = (cx - screen_x) ** 2 + (cy - screen_y) ** 2
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_id = cell_id
        return best_id

    def show_calibration_target(self, screen_x, screen_y):
        """Shows a small red dot at the given absolute screen coordinates —
        the actual thing the user looks at during calibration, instead of
        having to read coordinates off the terminal."""
        if self._calib_window is None:
            self._calib_window = tk.Toplevel(self.root)
            self._calib_window.overrideredirect(True)
            self._calib_window.attributes("-topmost", True)
            canvas = tk.Canvas(
                self._calib_window, width=30, height=30, bg="black", highlightthickness=0
            )
            canvas.pack()
            canvas.create_oval(5, 5, 25, 25, fill="red", outline="white", width=2)
        self._calib_window.geometry(f"30x30+{screen_x - 15}+{screen_y - 15}")
        self._calib_window.update()

    def hide_calibration_target(self):
        if self._calib_window is not None:
            self._calib_window.destroy()
            self._calib_window = None
