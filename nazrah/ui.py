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

        self._cells = {}
        self._active_id = None

        frame = tk.Frame(self.root, bg="black")
        frame.pack(expand=True, fill="both")

        for index, phrase in enumerate(phrase_data.PHRASES):
            row, col = divmod(index, columns)
            cell = tk.Label(
                frame,
                text=f"{phrase.icon}\n{phrase.text_ar}",
                font=("Segoe UI", 20),
                bg="#1e1e1e",
                fg="white",
                width=8,
                height=4,
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
        self.root.update_idletasks()
        self.root.update()

    def cell_bbox(self, phrase_id):
        cell = self._cells[phrase_id]
        x = cell.winfo_rootx()
        y = cell.winfo_rooty()
        return x, y, x + cell.winfo_width(), y + cell.winfo_height()

    def hit_test(self, screen_x, screen_y):
        for phrase_id in self._cells:
            x1, y1, x2, y2 = self.cell_bbox(phrase_id)
            if x1 <= screen_x <= x2 and y1 <= screen_y <= y2:
                return phrase_id
        return None
