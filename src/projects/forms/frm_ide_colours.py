# forms/frm_ide_colours.py

"""IdeColoursFrame for projects."""

import re
import tkinter as tk
from tkinter import colorchooser, ttk

from psiutils.buttons import IconButton
from psiutils.constants import PAD
from psiutils.utilities import geometry, window_resize

from projects.buttons import ButtonFrame
from projects.config import config
from projects.constants import APP_TITLE, ICON_DIR
from projects.project import Project
from projects.text import Text

txt = Text()

FRAME_TITLE = APP_TITLE


class ColourLabel(ttk.Label):
    def __init__(self, *args, **kwargs):
        self.colour = ""
        if "colour" in kwargs:
            self.colour = kwargs["colour"]
            kwargs.pop("colour")
        super().__init__(*args, **kwargs)


class IdeColoursFrame:
    def __init__(self, root: tk.Tk, project: Project) -> None:
        self.root = tk.Toplevel(root)
        self.project = project
        self.style = ttk.Style()
        self.colours_changed = False

        # tk variables
        self.project_name = tk.StringVar(value=project.name)
        # Colour items
        for key, item in project.workbench_colours.items():
            setattr(self, key, tk.StringVar(value=item))
            setattr(self, f"{key}_original", item)

        self.show()
        self._populate_colour_frame()

    def show(self):
        root = self.root
        root.geometry(geometry(config, __file__))
        root.title(f"{FRAME_TITLE} - IDE Colours")

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        main_frame = self._main_frame(root)
        main_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=PAD, pady=PAD)
        self.button_frame = self._button_frame(root)
        self.button_frame.grid(
            row=8, column=0, columnspan=9, sticky=tk.EW, padx=PAD, pady=PAD
        )
        sizegrip = ttk.Sizegrip(root)
        sizegrip.grid(sticky=tk.SE)

        root.bind("<Control-x>", self._dismiss)
        root.bind("<Control-o>", self._process)
        root.bind(
            "<Configure>",
            lambda event, arg=None: window_resize(root, __file__, config),
        )

    def _main_frame(self, master: tk.Frame) -> ttk.Frame:
        frame = ttk.Frame(master)

        self.colour_frame = tk.Frame(frame)
        self.colour_frame.grid(row=0, column=0, columnspan=4, sticky=tk.EW)
        return frame

    def _button_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ButtonFrame(master, tk.HORIZONTAL)
        frame.buttons = [
            frame.icon_button("accept", self._process, True),
            frame.icon_button("exit", self._dismiss),
        ]
        frame.enable(False)
        return frame

    def _populate_colour_frame(self) -> None:
        for child in self.colour_frame.winfo_children():
            child.destroy()

        row = 0
        label = ttk.Label(self.colour_frame, text="Project name")
        label.grid(row=row, column=0, sticky=tk.E, padx=PAD, pady=PAD)

        entry = ttk.Entry(
            self.colour_frame, textvariable=self.project_name, state="readonly"
        )
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD, pady=PAD)

        for index, key in enumerate(self.project.workbench_colours.keys()):
            row = index + 1
            self._add_colour_widgets(row, key)
        self._check_value_changed()

    def _add_colour_widgets(self, row: int, key: str) -> None:
        frame = self.colour_frame
        label = ttk.Label(frame, text=key)
        label.grid(row=row, column=0, sticky=tk.E, padx=PAD, pady=PAD)
        entry = ttk.Entry(frame, textvariable=getattr(self, key))
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD, pady=PAD)
        entry.bind(
            "<FocusOut>", lambda e, k=key: self._validate_colour_change(k)
        )

        colour = getattr(self, key).get()
        self.style.configure(f"{colour}.TLabel", background=colour)

        label = ColourLabel(
            frame,
            width=10,
            style=f"{colour}.TLabel",
            colour=colour,
            relief=tk.SOLID,
            borderwidth=1,
        )
        label.grid(row=row, column=2, sticky=tk.W, padx=PAD)
        button = IconButton(
            frame,
            txt.SELECT,
            "palette",
            lambda k=key: self._get_color(k),
            icon_path=ICON_DIR,
        )
        button.grid(row=row, column=3, padx=PAD, pady=(0, 5))

    def _validate_colour_change(self, key: str) -> None:
        colour = getattr(self, key).get()
        pattern = r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$"
        if not re.match(pattern, colour):
            # Invalid colour, reset to original
            getattr(self, key).set(getattr(self, f"{key}_original"))
        self._populate_colour_frame()

    def _get_color(self, key: str) -> None:
        colour = getattr(self, key).get()
        result = colorchooser.askcolor(colour, parent=self.root)
        getattr(self, key).set(result[1])
        self._populate_colour_frame()

    def _check_value_changed(self, *args) -> None:
        enable = self._record_changes()
        self.colours_changed = enable
        self.button_frame.enable(enable)

    def _record_changes(self) -> bool:
        for key in self.project.workbench_colours.keys():
            if getattr(self, key).get() != getattr(self, f"{key}_original"):
                return True
        return False

    def _process(self, *args) -> None:
        pass

    def _dismiss(self, *args) -> None:
        self.root.destroy()
