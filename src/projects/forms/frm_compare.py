"""Main frame for ..."""
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import shutil
from functools import partial

from psiutils.constants import PAD, PADB, PADT, WidgetState
from psiutils.utilities import window_resize, geometry
from psiutils.buttons import ButtonFrame, IconButton
from psiutils.widgets import ScrollingCanvas

from projects.compare import compare, Missing
from projects.config import read_config
from projects.project import Project
from projects.env_version import EnvironmentVersion
from projects.text import Text
from projects import logger

txt = Text()
FRAME_TITLE = 'Compare files across directories'


class CompareFrame():
    """Define the Main frame."""
    def __init__(
            self, parent: ttk.Frame,
            project: Project,
            env_version: EnvironmentVersion) -> None:
        self.root = tk.Toplevel(parent.root)
        self.parent = parent
        self.project = project
        self.env_version = env_version
        self.destroy_widgets = []
        self.missing_file_frame = None
        self.mismatch_frame = None

        self.config = read_config()
        (self.missing, self.mismatches) = compare(
            self.project.source_dir, self.env_version.dir)

        self.missing_frame = None
        self.button_frame = None

        # Tk Variables
        self.project_name = tk.StringVar(value=project.name)
        self.env_dir = tk.StringVar(value=env_version.dir_short)
        self.source_dir = tk.StringVar(value=project.source_dir_short)
        self.env_version_version = tk.StringVar(value=env_version.version)
        self.project_version = tk.StringVar(value=project.project_version)
        self.mismatch = tk.StringVar(value='')
        self._show()

        self.compare_project()
        self._populate_mismatches()

    def _show(self):
        self._configure()

        main_frame = self._main_frame(self.root)
        main_frame.grid(row=0, column=0, sticky=tk.NSEW)

        sizegrip = ttk.Sizegrip(self.root)
        sizegrip.grid(sticky=tk.SE)

    def _configure(self) -> None:
        root = self.root
        root.geometry(geometry(self.config, __file__))
        root.transient(self.parent.root)
        root.bind('<Control-x>', self._dismiss)
        root.bind('<Configure>',
                  lambda event, arg=None: window_resize(self, __file__))

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        root.title(f'{FRAME_TITLE}')

    def _main_frame(self, master: ttk.Frame) -> ttk.Frame:
        frame = ttk.Frame(master)
        frame.columnconfigure(0, weight=1)

        row = 0
        project_frame = self._project_frame(frame)
        project_frame.grid(row=row, column=0, sticky=tk.EW, padx=PAD, pady=PAD)

        row += 1
        label = ttk.Label(
            frame, text='Missing files and dirs', style='blue-fg.TLabel')
        label.grid(row=row, column=0, sticky=tk.W, padx=PAD, pady=PADT)
        self.destroy_widgets.append(label)

        row += 1
        self.missing_file_frame = self._missing_frame(frame)
        self.missing_file_frame.grid(
            row=row, column=0, sticky=tk.NW, padx=PAD, pady=PAD)

        row += 1
        label = ttk.Label(frame, text='Mismatches', style='blue-fg.TLabel')
        label.grid(row=row, column=0, sticky=tk.W, padx=PAD, pady=PADT)

        row += 1
        frame.rowconfigure(row, weight=1)
        self.mismatch_frame = ScrollingCanvas(
            frame,
            relief=tk.SUNKEN,
            borderwidth=2,)
        self.mismatch_frame.grid(
            row=row, column=0, sticky=tk.NSEW, padx=PAD, pady=PAD)

        row += 1
        self.button_frame = self._button_frame(frame)
        self.button_frame.grid(
            row=row, column=0, sticky=tk.EW, padx=PAD, pady=PAD)

        return frame

    def _project_frame(self, master: ttk.Frame) -> ttk.Frame:
        frame = ttk.Frame(master)
        frame.columnconfigure(2, weight=1)

        row = 0
        label = ttk.Label(frame, text='Project')
        label.grid(row=row, column=0, sticky=tk.E)

        entry = ttk.Entry(frame, textvariable=self.project_name,
                          state=WidgetState.READONLY)
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD)

        row += 1
        label = ttk.Label(frame, text='Project version')
        label.grid(row=row, column=0, sticky=tk.E)

        entry = ttk.Entry(frame, textvariable=self.project_version,
                          state=WidgetState.READONLY)
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD)

        entry = ttk.Entry(frame, textvariable=self.source_dir,
                          state=WidgetState.READONLY)
        entry.grid(row=row, column=2, sticky=tk.EW, padx=PAD)

        row += 1
        label = ttk.Label(frame, text='Env version')
        label.grid(row=row, column=0, sticky=tk.E)

        entry = ttk.Entry(frame, textvariable=self.env_version_version,
                          state=WidgetState.READONLY)
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD)

        entry = ttk.Entry(
            frame, textvariable=self.env_dir, state=WidgetState.READONLY)
        entry.grid(row=row, column=2, sticky=tk.EW, padx=PAD)

        return frame

    def _button_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ButtonFrame(master, tk.HORIZONTAL)
        frame.buttons = [
            frame.icon_button('diff', self.show_diff, True),
            frame.icon_button('exit', self._dismiss),
        ]
        frame.enable(False)
        return frame

    def compare_project(self) -> None:
        """Destroy and recreate widgets based on comparison."""
        ...

    def _missing_frame(self, master: ttk.Frame) -> ttk.Frame:
        frame = ttk.Frame(master, relief=tk.SUNKEN, borderwidth=2)
        self.destroy_widgets.append(frame)

        if not self.missing:
            return self._no_missing_items_frame(frame)
        return self._missing_items_frame(frame)

    def _no_missing_items_frame(self, frame: tk.Frame) -> tk.Frame:
        row = 0
        label = ttk.Label(frame, text='None')
        label.grid(row=row, column=0)
        self.destroy_widgets.append(label)
        return frame

    def _missing_items_frame(self, frame: tk.Frame) -> tk.Frame:
        row = 0
        label = ttk.Label(frame, text='Env dir')
        label.grid(row=row, column=0, padx=PAD, sticky=tk.W)
        self.destroy_widgets.append(label)

        label = ttk.Label(frame, text='Project dir')
        label.grid(row=row, column=1, sticky=tk.W)
        self.destroy_widgets.append(label)

        for missing_file in self.missing:
            row += 1
            self._missing_files_labels(frame, missing_file, row)
            self._missing_button(frame, missing_file, row)
        return frame

    def _missing_files_labels(
            self, frame: tk.Frame, missing_file: Missing, row: int) -> None:
        missing_col = 0 if missing_file.missing_in_env else 1
        present_col = (missing_col +1) % 2
        label = ttk.Label(frame, text=missing_file.file_name)
        label.grid(row=row, column=missing_col, padx=PAD, sticky=tk.W)
        label = ttk.Label(
            frame, text='missing', style='red-fg.TLabel')
        label.grid(row=row, column=present_col, padx=PAD, sticky=tk.W)

    def _missing_button(
            self, frame: tk.Frame, missing_file: Missing, row: int) -> None:
        button = IconButton(frame, txt.COPY, 'copy_docs')
        button.grid(row=row, column=2, padx=PAD, pady=PADB)
        button.widget.bind(
            '<Button-1>', partial(self._copy_file, missing_file.file_name))

    def _populate_mismatches(self) -> None:
        for row, item in enumerate(sorted(self.mismatches)):
            button = ttk.Radiobutton(
                self.mismatch_frame.content,
                text=item,
                value=item,
                variable=self.mismatch,
                command=self.rb_selected
            )
            button.grid(row=row+2, column=0, sticky=tk.W, padx=PAD)
            self.destroy_widgets.append(button)

        # return frame

    def rb_selected(self, *args) -> None:
        self.button_frame.enable(True)

    def show_diff(self, *args) -> None:
        file = self.mismatch.get()
        paths = [
            str(Path(self.env_version.dir, file)),
            str(Path(self.project.source_dir, file)),
        ]

        self.root.withdraw()
        subprocess.run(['meld', *paths])
        self.root.deiconify()
        if self.env_dir.get() and self.source_dir.get():
            self.compare_project()

    def _copy_file(self, file_name, *args) -> None:
        source = Path(self.env_version.dir, file_name)
        if not self._confirm_copy(source, file_name):
            return

        destination = Path(self.project.source_dir, file_name)

        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
            logger.info(
                'Copy directory',
                source=str(source),
                destination=str(destination))
        else:
            logger.info(
                'Copy file', source=str(source), destination=str(destination))
            shutil.copyfile(source, destination)

        for widget in self.missing_file_frame.winfo_children():
            widget.destroy()
        self.compare_project()

    def _confirm_copy(self, source: Path, file_name: str) -> bool:
        item = 'directory' if source.is_dir() else 'file'
        return messagebox.askokcancel(
            '', f'Copy this {item}? ({file_name})', parent=self.root)


    def _dismiss(self, *args) -> None:
        self.root.destroy()
