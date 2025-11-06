"""Tkinter frame for config maintenance."""

import tkinter as tk
from tkinter import ttk, filedialog

from psiutils.buttons import ButtonFrame, IconButton
from psiutils.constants import PAD
from psiutils.utilities import window_resize, geometry

from projects import logger
from projects.config import config, read_config
from projects.text import Text

txt = Text()

LF = '\n'

FIELDS = {
    'data_directory': tk.StringVar,
    'script_directory': tk.StringVar,
}


class ConfigFrame():
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
        _show(): Displays the configuration frame.
        _main_frame(master: tk.Frame) -> tk.Frame: Creates the main frame of
        the configuration.
        _button_frame(master: tk.Frame) -> tk.Frame: Creates the button frame
        for the configuration.
        _check_value_changed(*args) -> None: Checks if values have changed.
        _set_data_directory() -> None: Sets the data directory.
        _set_script_directory() -> None: Sets the script directory.
        _save_config(): Saves the configuration changes.
        _config_changes() -> dict: Determines the changes in
        configuration settings.
        _set_config(*args) -> None: Sets the configuration settings.
        _dismiss() -> None: Dismisses the configuration frame.
    """
    def __init__(self, parent):
        # pylint: disable=no-member
        self.root = tk.Toplevel(parent.root)
        self.config = read_config()
        self.parent = parent
        self.ignore_text = None

        for field, f_type in FIELDS.items():
            if f_type is tk.StringVar:
                setattr(self, field, self._stringvar(getattr(config, field)))

        self.button_frame = None
        self._show()

    def _stringvar(self, value: str) -> tk.StringVar:
        stringvar = tk.StringVar(value=value)
        stringvar.trace_add('write', self._check_value_changed)
        return stringvar

    def _show(self):
        root = self.root
        root.geometry(geometry(self.config, __file__))
        root.title(txt.CONFIG)

        root.bind('<Control-x>', self._dismiss)
        root.bind('<Control-s>', self._save_config)
        root.bind('<Configure>',
                  lambda event, arg=None: window_resize(self, __file__))
        root.bind("<FocusIn>", self._set_config)

        root.wait_visibility()

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        main_frame = self._main_frame(root)
        main_frame.grid(row=0, column=0, sticky=tk.NSEW, pady=PAD)

        sizegrip = ttk.Sizegrip(root)
        sizegrip.grid(sticky=tk.SE)

    def _main_frame(self, master: tk.Frame) -> tk.Frame:
        # pylint: disable=no-member
        frame = ttk.Frame(master)

        frame.columnconfigure(1, weight=1)

        row = 0
        label = ttk.Label(frame, text="Data directory:")
        label.grid(row=row, column=0, sticky=tk.E)

        directory = ttk.Entry(frame,
                              textvariable=self.data_directory)
        directory.grid(row=row, column=1, columnspan=1, sticky=tk.EW,
                       padx=PAD, pady=PAD)
        select = IconButton(
            frame, txt.OPEN, 'open', self._set_data_directory)
        select.grid(row=row, column=2, sticky=tk.W, padx=PAD)

        row += 1
        label = ttk.Label(frame, text="Script directory:")
        label.grid(row=row, column=0, sticky=tk.E)

        directory = ttk.Entry(frame,
                              textvariable=self.script_directory)
        directory.grid(row=row, column=1, columnspan=1, sticky=tk.EW,
                       padx=PAD, pady=PAD)
        select = IconButton(frame, txt.OPEN, 'open',
                            self._set_script_directory)
        select.grid(row=row, column=2, sticky=tk.W, padx=PAD, pady=PAD)

        row += 1
        label = ttk.Label(frame, text='Ignore')
        label.grid(row=row, column=0, sticky=tk.W, padx=PAD, pady=PAD)

        row += 1
        frame.rowconfigure(row, weight=1)
        self.ignore_text = tk.Text(frame)
        self.ignore_text.grid(row=row, column=0, columnspan=3,
                              sticky=tk.NSEW, padx=PAD)
        self.ignore_text.insert('0.0', '\n'.join(self.config.ignore))
        self.ignore_text.bind('<KeyRelease>', self._check_value_changed)

        row += 1
        self.button_frame = self._button_frame(frame)
        self.button_frame.grid(row=row, column=0, columnspan=3,
                               sticky=tk.EW, padx=PAD, pady=PAD)
        self.button_frame.disable()
        return frame

    def _button_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ButtonFrame(master, tk.HORIZONTAL)
        frame.buttons = [
            frame.icon_button('save', self._save_config, True),
            frame.icon_button('exit', self._dismiss),
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

    def _save_config(self):
        raw_changes = self._config_changes()
        changes = {field: f'(old value={change[0]}, new_value={change[1]})'
                   for field, change in raw_changes.items()}

        for field in FIELDS:
            self.config.config[field] = getattr(self, field).get()
        if 'ignore' in raw_changes:
            self.config.update('ignore', raw_changes['ignore'][1])

        logger.info("Config saved", changes=changes)

        self._dismiss()
        return self.config.save()

    def _config_changes(self) -> dict:
        stored = self.config.config
        # for field in FIELDS:
        field = 'script_directory'
        print(f'{field} {stored[field]==getattr(self, field).get()} {stored[field]=} {self.script_directory.get()=}')
        changes = {
            field: (stored[field], getattr(self, field).get())
            for field in FIELDS
            if stored[field] != getattr(self, field).get()
        }
        # field = 'script_directory'
        # print(f'{field} {stored[field]=} {getattr(self, field).get()=}')

        ignore_text = self.ignore_text.get('0.0', tk.END)
        ignore_text = ignore_text.strip('\n')
        ignore_text = ignore_text.split('\n')
        if stored['ignore'] != ignore_text:
            changes['ignore'] = (stored['ignore'], ignore_text)
        return changes

    def _set_config(self, *args) -> None:
        self.config = read_config()
        for field in FIELDS:
            getattr(self, field).set(self.config.config[field])

    def _dismiss(self) -> None:
        self.root.destroy()
