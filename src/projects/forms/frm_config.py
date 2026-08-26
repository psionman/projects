"""Tkinter frame for config maintenance."""

import tkinter as tk
from tkinter import filedialog, ttk

from psiutils.buttons import ButtonFrame, IconButton
from psiutils.constants import PAD
from psiutils.utilities import geometry, window_resize

from projects import logger
from projects.config import config
from projects.text import Text

txt = Text()

LF = "\n"


class ConfigFrame:
    """
    Represents a configuration frame for managing and displaying
    configuration settings.

    Args:
        parent: The parent window for the configuration frame.

    Attributes:
        root: The root window of the configuration frame.
        config: The configuration settings.
        parent: The parent window.
        ignore_text: Text field for ignored settings.

    Methods:
        _stringvar(value: str) -> tk.StringVar: Creates a StringVar with a
        given value.
        _show() -> None: Displays the configuration frame.
        _main_frame(master: tk.Frame) -> tk.Frame: Creates the main frame of
        the configuration.
        _button_frame(master: tk.Frame) -> tk.Frame: Creates the button frame
        for the configuration.
        _check_value_changed(*args) -> None: Checks if values have changed.
        _set_data_directory() -> None: Sets the data directory.
        _set_script_directory() -> None: Sets the script directory.
        _save_config() -> None: Saves the configuration changes.
        _config_changes() -> dict: Determines the changes in
        configuration settings.
        _set_config(*args) -> None: Sets the configuration settings.
        _dismiss() -> None: Dismisses the configuration frame.
    """

    def __init__(self, parent: ttk.Frame) -> None:
        self.root = tk.Toplevel(parent.root)
        self.parent = parent
        self.ignore_text = None

        # tk.StringVars
        self.data_directory = tk.StringVar(value=config.data_directory)
        self.script_directory = tk.StringVar(value=config.script_directory)
        self.desktop_directory = tk.StringVar(value=config.desktop_directory)

        # Track changes
        self.data_directory.trace_add("write", self._check_value_changed)
        self.script_directory.trace_add("write", self._check_value_changed)
        self.desktop_directory.trace_add("write", self._check_value_changed)

        self.button_frame = None
        self._show()

    def _stringvar(self, value: str) -> tk.StringVar:
        stringvar = tk.StringVar(value=value)
        stringvar.trace_add("write", self._check_value_changed)
        return stringvar

    def _boolvar(self, value: bool) -> tk.BooleanVar:
        boolvar = tk.BooleanVar(value=value)
        boolvar.trace_add("write", self._check_value_changed)
        return boolvar

    def _show(self) -> None:
        root = self.root
        root.geometry(geometry(config, __file__))
        root.title(txt.CONFIG)

        root.wait_visibility()

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        main_frame = self._main_frame(root)
        main_frame.grid(row=0, column=0, sticky=tk.NSEW, pady=PAD)

        sizegrip = ttk.Sizegrip(root)
        sizegrip.grid(sticky=tk.SE)

        root.update_idletasks()
        root.bind("<Control-x>", self._dismiss)
        root.bind("<Control-s>", self._save_config)
        root.bind(
            "<Configure>",
            lambda event, arg=None: window_resize(root, __file__, config),
        )

    def _main_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ttk.Frame(master)

        frame.columnconfigure(1, weight=1)

        row = 0
        label = ttk.Label(frame, text="Data directory:")
        label.grid(row=row, column=0, sticky=tk.E)

        directory = ttk.Entry(frame, textvariable=self.data_directory)
        directory.grid(
            row=row, column=1, columnspan=1, sticky=tk.EW, padx=PAD, pady=PAD
        )
        select = IconButton(frame, txt.OPEN, "open", self._set_data_directory)
        select.grid(row=row, column=2, sticky=tk.W, padx=PAD)

        row += 1
        label = ttk.Label(frame, text="Script directory:")
        label.grid(row=row, column=0, sticky=tk.E)

        directory = ttk.Entry(frame, textvariable=self.script_directory)
        directory.grid(
            row=row, column=1, columnspan=1, sticky=tk.EW, padx=PAD, pady=PAD
        )
        select = IconButton(
            frame, txt.OPEN, "open", self._set_script_directory
        )
        select.grid(row=row, column=2, sticky=tk.W, padx=PAD, pady=PAD)

        row += 1
        label = ttk.Label(frame, text="Desktop directory:")
        label.grid(row=row, column=0, sticky=tk.E)

        directory = ttk.Entry(frame, textvariable=self.desktop_directory)
        directory.grid(
            row=row, column=1, columnspan=1, sticky=tk.EW, padx=PAD, pady=PAD
        )
        select = IconButton(
            frame, txt.OPEN, "open", self._set_desktop_directory
        )
        select.grid(row=row, column=2, sticky=tk.W, padx=PAD, pady=PAD)

        row += 1
        label = ttk.Label(frame, text="Ignore")
        label.grid(row=row, column=0, sticky=tk.W, padx=PAD, pady=PAD)

        row += 1
        frame.rowconfigure(row, weight=1)
        self.ignore_text = tk.Text(frame)
        self.ignore_text.grid(
            row=row, column=0, columnspan=3, sticky=tk.NSEW, padx=PAD
        )
        self.ignore_text.insert("0.0", "\n".join(config.ignore))
        self.ignore_text.bind("<KeyRelease>", self._check_value_changed)

        row += 1
        self.button_frame = self._button_frame(frame)
        self.button_frame.grid(
            row=row, column=0, columnspan=3, sticky=tk.EW, padx=PAD, pady=PAD
        )
        self.button_frame.disable()
        return frame

    def _button_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ButtonFrame(master, tk.HORIZONTAL)
        frame.buttons = [
            frame.icon_button("save", self._save_config, True),
            frame.icon_button("exit-orange", self._dismiss),
        ]
        frame.grid(row=0, column=0, sticky=tk.EW)
        return frame

    def _check_value_changed(self, *args) -> None:
        enable = bool(self._config_changes())
        self.button_frame.enable(enable)

    def _set_data_directory(self) -> None:
        if directory := filedialog.askdirectory(
            initialdir=self.data_directory.get(),
            parent=self.root,
        ):
            self.data_directory.set(directory)

    def _set_script_directory(self) -> None:
        if directory := filedialog.askdirectory(
            initialdir=self.script_directory.get(),
            parent=self.root,
        ):
            self.script_directory.set(directory)

    def _set_desktop_directory(self) -> None:
        if directory := filedialog.askdirectory(
            initialdir=self.desktop_directory.get(),
            parent=self.root,
        ):
            self.desktop_directory.set(directory)

    def _save_config(self) -> None:
        raw_changes = self._config_changes()
        changes = {
            field: f"(old value={change[0]}, new_value={change[1]})"
            for field, change in raw_changes.items()
        }

        config.update("data_directory", self.data_directory.get())
        config.update("script_directory", self.script_directory.get())
        config.update("desktop_directory", self.desktop_directory.get())
        if "ignore" in raw_changes:
            config.update("ignore", raw_changes["ignore"][1])

        logger.info("Config saved", changes=changes)

        self._dismiss()
        return config.save()

    def _config_changes(self) -> dict:
        stored = config.config
        changes = {
            "data_directory": (
                stored["data_directory"],
                self.data_directory.get(),
            ),
            "script_directory": (
                stored["script_directory"],
                self.script_directory.get(),
            ),
            "desktop_directory": (
                stored["desktop_directory"],
                self.desktop_directory.get(),
            ),
        }

        ignore_text = self.ignore_text.get("0.0", tk.END)
        ignore_text = ignore_text.strip("\n")
        ignore_text = ignore_text.split("\n")
        if stored["ignore"] != ignore_text:
            changes["ignore"] = (stored["ignore"], ignore_text)
        return changes

    def _dismiss(self) -> None:
        self.root.destroy()
