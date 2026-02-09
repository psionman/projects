
import tkinter as tk
from tkinter import ttk


class ScrollingCanvdddas(tk.Frame):
    def __init__(
            self,
            master,
            *,
            relief,
            borderwidth,
            background="#ccc"):
        super().__init__(master, relief=relief, borderwidth=borderwidth)

        self.grid_propagate(False)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self,
            borderwidth=0,
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.content = tk.Frame(self.canvas, background=background)

        self.window_id = self.canvas.create_window(
            (0, 0),
            window=self.content,
            anchor="nw",
        )

        # Geometry management
        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_content_configure(self, event=None):
        # Let Tk finish geometry before computing bbox
        self.after_idle(
            lambda: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

    def _on_canvas_configure(self, event):
        # Width sync ONLY (never height!)
        self.canvas.itemconfigure(self.window_id, width=event.width)
