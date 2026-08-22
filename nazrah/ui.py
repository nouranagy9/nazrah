import tkinter as tk

from . import phrases as phrase_data


class PhraseGridUI:
    """Tkinter grid of phrase cells with Arabic labels. Call `set_active_cell`
    every frame with the phrase id currently being gazed at (or None) and a
    dwell progress in [0, 1] so the cell fills in as the user's gaze lingers.
    """

    def __init__(self, on_select, columns=4):
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

        frame = tk.Frame(self.root, bg="black")
        frame.pack(expand=True, fill="both")

        rows = -(-len(phrase_data.PHRASES) // columns)  # ceil division
        for col in range(columns):
            frame.columnconfigure(col, weight=1)
        for row in range(rows):
            frame.rowconfigure(row, weight=1)

        for index, phrase in enumerate(phrase_data.PHRASES):
            row, col = divmod(index, columns)
            cell = tk.Label(
                frame,
                text=f"{phrase.icon}\n{phrase.text_ar}",
                font=("Segoe UI", 20),
                bg="#1e1e1e",
                fg="white",
                relief="ridge",
                borderwidth=2,
            )
            cell.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            self._cells[phrase.id] = cell

    def set_active_cell(self, phrase_id, progress=0.0):
        if phrase_id != self._active_id and self._active_id is not None:
            self._cells[self._active_id].configure(bg="#1e1e1e")
        self._active_id = phrase_id
        if phrase_id is not None:
            self._cells[phrase_id].configure(bg=self._progress_color(progress))

    @staticmethod
    def _progress_color(progress):
        green = int(30 + progress * 150)
        return f"#1e{green:02x}3c"

    def flash_selection(self, phrase_id):
        self._cells[phrase_id].configure(bg="#2e7d32")
        self.root.after(400, lambda: self._cells[phrase_id].configure(bg="#1e1e1e"))

    def update(self):
        if self.closed:
            return
        self.root.update_idletasks()
        self.root.update()

    def _on_close(self):
        self.closed = True
        self.root.destroy()

    def cell_bbox(self, phrase_id):
        cell = self._cells[phrase_id]
        x = cell.winfo_rootx()
        y = cell.winfo_rooty()
        return x, y, x + cell.winfo_width(), y + cell.winfo_height()

    def hit_test(self, screen_x, screen_y):
        """Returns whichever cell's center is closest to the given screen
        point. Deliberately not exact-bbox containment: the grid has small
        gaps between cells (padding) and, when the phrase count isn't a
        multiple of `columns`, an incomplete last row — both of which would
        otherwise create dead zones a calibrated point could land in and
        get no match at all. Always resolving to the nearest cell means
        gaze always lands on *something*, which matters more here than
        precise boundaries."""
        best_id = None
        best_dist = None
        for phrase_id in self._cells:
            x1, y1, x2, y2 = self.cell_bbox(phrase_id)
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            dist = (cx - screen_x) ** 2 + (cy - screen_y) ** 2
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_id = phrase_id
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
