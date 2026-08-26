import tkinter as tk
from collections import namedtuple

# A single selectable cell: id is what on_select/hit_test deal in, icon +
# text are what's drawn. Deliberately not tied to phrases.Phrase — the
# home screen's cells ("turn off light", "needs") aren't phrases at all.
GridItem = namedtuple("GridItem", ["id", "icon", "text"])


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

    def __init__(self, on_select, items, columns):
        self.on_select = on_select
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
            cell = tk.Label(
                frame,
                text=f"{item.icon}\n{item.text}",
                font=("Segoe UI", 20),
                bg="#1e1e1e",
                fg="white",
                relief="ridge",
                borderwidth=2,
            )
            cell.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            self._cells[item.id] = cell

    def set_active_cell(self, cell_id, progress=0.0):
        if cell_id != self._active_id and self._active_id is not None:
            self._cells[self._active_id].configure(bg="#1e1e1e")
        self._active_id = cell_id
        if cell_id is not None:
            self._cells[cell_id].configure(bg=self._progress_color(progress))

    @staticmethod
    def _progress_color(progress):
        green = int(30 + progress * 150)
        return f"#1e{green:02x}3c"

    def flash_selection(self, cell_id):
        cell = self._cells[cell_id]
        cell.configure(bg="#2e7d32")

        def revert():
            try:
                cell.configure(bg="#1e1e1e")
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
