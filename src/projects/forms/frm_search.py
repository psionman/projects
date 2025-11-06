"""SearchFrame for <application>."""
import os
import re
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from clipboard import copy

from psiutils.constants import PAD
from psiutils.buttons import ButtonFrame, IconButton
from psiutils.utilities import window_resize, geometry

from projects.constants import APP_TITLE
from projects.config import read_config

FRAME_TITLE = f'{APP_TITLE} - Search for content'


class SearchFrame():
    """
    Initialize a Search form.

    Args:
        parent: The parent window.

    Returns:
        None
    """
    def __init__(self, parent: tk.Frame, search_term: str = '') -> None:
        self.root = tk.Toplevel()
        self.parent = parent
        self.config = read_config()
        self.projects = parent.projects
        self.files = []

        self.search_button = None
        self.copy_button = None
        self.found_list = None
        self.found = []

        # tk variables
        self.search_text = tk.StringVar()
        self.file_type = tk.StringVar(value='py')
        self.match_case = tk.BooleanVar()
        self.match_whole_word = tk.BooleanVar()

        self.search_text.trace_add('write', self._check_value_changed)

        self._show()

        self.search_text.set(search_term)

    def _show(self) -> None:
        root = self.root
        root.geometry(geometry(self.config, __file__))
        root.title(FRAME_TITLE)
        root.transient(self.parent.root)
        root.bind('<Control-x>', self._dismiss)
        root.bind('<Configure>',
                  lambda event, arg=None: window_resize(self, __file__))

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        main_frame = self._main_frame(root)
        main_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=PAD, pady=PAD)
        self.button_frame = self._button_frame(root)
        self.button_frame.grid(row=8, column=0, columnspan=9,
                               sticky=tk.EW, padx=PAD, pady=PAD)

        sizegrip = ttk.Sizegrip(root)
        sizegrip.grid(sticky=tk.SE)

    def _main_frame(self, master: tk.Frame) -> ttk.Frame:
        frame = ttk.Frame(master)
        frame.columnconfigure(1, weight=1)

        row = 0
        label = ttk.Label(frame, text='Search for')
        label.grid(row=row, column=0, sticky=tk.E, padx=PAD, pady=PAD)

        entry = ttk.Entry(frame, textvariable=self.search_text)
        entry.grid(row=row, column=1, sticky=tk.EW)
        entry.focus_set()

        row += 1
        options = self._options_frame(frame)
        options.grid(row=row, column=1, sticky=tk.W)

        row += 1
        frame.rowconfigure(row, weight=1)
        self.found_list = tk.Text(frame, height=20)
        self.found_list.grid(row=row, column=0, columnspan=2, sticky=tk.NSEW)
        self.found_list.insert('0.0', '')

        return frame

    def _options_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ButtonFrame(master, tk.HORIZONTAL)

        # Match options
        row = 0
        check_button = ttk.Checkbutton(
            frame, text='Match case', variable=self.match_case)
        check_button.grid(row=row, column=0, sticky=tk.W)

        row += 1
        check_button = ttk.Checkbutton(
            frame, text='Match whole word', variable=self.match_whole_word)
        check_button.grid(row=row, column=0, sticky=tk.W)

        # File options
        row = 0
        button = ttk.Radiobutton(
            frame,
            text='.py files',
            variable=self.file_type,
            value='py',
        )
        button.grid(row=row, column=1, sticky=tk.W)

        row += 1
        button = ttk.Radiobutton(
            frame,
            text='all files',
            variable=self.file_type,
            value='all',
        )
        button.grid(row=row, column=1, sticky=tk.W)

        return frame

    def _button_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ButtonFrame(master, tk.HORIZONTAL)
        self.search_button = IconButton(
            frame, 'Search', 'search', self._start_process, True)
        self.copy_button = IconButton(
            frame, 'Copy', 'copy_clipboard', self._copy, True)
        frame.buttons = [
            self.search_button,
            self.copy_button,
            frame.icon_button('exit', self._dismiss),
        ]
        frame.enable(False)
        return frame

    def _check_value_changed(self, *args) -> None:
        enable = (self.search_text != '')
        self.search_button.enable(enable)

    def _start_process(self, *args) -> None:
        self.copy_button.disable()
        self.found_list.delete('0.0', tk.END)
        self.found = [
            project.name
            for project in self.projects.values()
            if self._parse_project(project.base_dir)
        ]
        self.found_list.insert('0.0', '\n'.join(sorted(self.found)))
        print(f'{self.found=}')
        if self.found:
            self.copy_button.enable()
        else:
            self.found_list.insert('0.0', 'No items found')

    def _parse_project(self, search_dir: str) -> bool:
        found = False
        for directory_name, subdir_list, file_list in os.walk(search_dir):
            del subdir_list
            if not self._ignore_path(directory_name):
                for file_name in file_list:
                    path = Path(directory_name, file_name)
                    if self.file_type.get() == 'py':
                        if file_name.endswith('.py'):
                            found = self._contains_search_text(path)
                    else:
                        found = self._contains_search_text(path)
                    if found:
                        return True
        return False

    def _contains_search_text(self, path: str) -> bool:
        with open(path, 'r', encoding='utf-8') as f_test:
            file_text = f_test.read()

        search = self.search_text.get()
        if not self.match_case.get():
            search = search.lower()
        search_re = rf'\b{re.escape(search)}\b'

        if not self.match_case.get() and not self.match_whole_word.get():
            return search in file_text.lower()

        if self.match_case.get() and not self.match_whole_word.get():
            return search in file_text

        if not self.match_case.get() and self.match_whole_word.get():
            return re.findall(search_re, file_text.lower())

        if self.match_case.get() and self.match_whole_word.get():
            return re.findall(search_re, file_text)

        return False

    def _ignore_path(self, path: str) -> bool:
        ignore = [
            '.venv',
            '.git',
            '__pycache__',
        ]
        return any(item in path for item in ignore)

    def _copy(self, *args) -> None:
        copy('\n'.join(sorted(self.found)))

    def _dismiss(self, *args) -> None:
        self.root.destroy()
