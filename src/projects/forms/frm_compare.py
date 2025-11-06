"""Main frame for ..."""
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import shutil

from psiutils.constants import PAD, PADB
from psiutils.utilities import window_resize, geometry, notify
from psiutils.buttons import ButtonFrame, IconButton

from projects.compare import compare
from projects.config import read_config
from projects.project import Project
from projects.env_version import EnvironmentVersion
from projects.text import Text

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

        self.config = read_config()

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

        self.destroy_widgets = []
        self.compare_project()

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

    def _main_frame(self, container: ttk.Frame) -> ttk.Frame:
        frame = ttk.Frame(container)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        project_frame = self._project_frame(frame)
        project_frame.grid(row=0, column=0, sticky=tk.EW, padx=PAD, pady=PAD)

        self.missing_frame = ttk.Frame(frame)
        self.missing_frame.grid(row=1, column=0, sticky=tk.NW, pady=PAD)

        self.button_frame = self._button_frame(frame)
        self.button_frame.grid(
            row=2, column=0, sticky=tk.EW, padx=PAD, pady=PAD)

        return frame

    def _project_frame(self, container: ttk.Frame) -> ttk.Frame:
        frame = ttk.Frame(container)
        frame.columnconfigure(2, weight=1)

        row = 0
        label = ttk.Label(frame, text='Project')
        label.grid(row=row, column=0, sticky=tk.E)

        entry = ttk.Entry(frame, textvariable=self.project_name,
                          state='readonly')
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD)

        row += 1
        label = ttk.Label(frame, text='Project version')
        label.grid(row=row, column=0, sticky=tk.E)

        entry = ttk.Entry(frame, textvariable=self.project_version,
                          state='readonly')
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD)

        entry = ttk.Entry(frame, textvariable=self.source_dir,
                          state='readonly')
        entry.grid(row=row, column=2, sticky=tk.EW, padx=PAD)

        row += 1
        label = ttk.Label(frame, text='Env version')
        label.grid(row=row, column=0, sticky=tk.E)

        entry = ttk.Entry(frame, textvariable=self.env_version_version,
                          state='readonly')
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD)

        entry = ttk.Entry(frame, textvariable=self.env_dir, state='readonly')
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
        (missing, mismatches) = compare(
            self.project.source_dir, self.env_version.dir)

        for item in self.destroy_widgets:
            item.destroy()

        frame = ttk.Frame(self.missing_frame)
        frame.grid(row=0, column=0, padx=PAD)
        self.destroy_widgets.append(frame)

        self.missing_file_frame = self._missing_frame(frame, missing)
        self.missing_file_frame.grid(row=0, column=0)
        self.destroy_widgets.append(self.missing_file_frame)

        mismatch_frame = self._mismatch_frame(frame, mismatches)
        mismatch_frame.grid(row=1, column=0, sticky=tk.W)
        self.destroy_widgets.append(mismatch_frame)

    def _missing_frame(self, container: ttk.Frame,
                       missing: list[tuple]) -> ttk.Frame:
        # pylint: disable=no-member)
        frame = ttk.Frame(container)
        frame.grid(row=9, column=0, padx=PAD)
        self.destroy_widgets.append(frame)

        row = 0
        label = ttk.Label(
            frame, text=' Missing files and dirs', style='blue-fg.TLabel')
        label.grid(row=row, column=0, sticky=tk.W)
        self.destroy_widgets.append(label)

        row += 1
        if not missing:
            label = ttk.Label(frame, text='None')
            label.grid(row=row, column=0)
            self.destroy_widgets.append(label)
            return frame

        label = ttk.Label(frame, text='Env dir')
        label.grid(row=row, column=0, sticky=tk.W)
        self.destroy_widgets.append(label)

        label = ttk.Label(frame, text='Project dir')
        label.grid(row=row, column=1, sticky=tk.W)
        self.destroy_widgets.append(label)

        missing_files = None
        for row, missing_files in enumerate(missing):
            label = self._missing_file_label(frame, missing_files[0])
            label.grid(row=row+2, column=0, padx=PAD, sticky=tk.W)

            label = self._missing_file_label(frame, missing_files[1])
            label.grid(row=row, column=1, sticky=tk.W)

            if missing_files[0]:
                button = IconButton(frame, txt.COPY, 'copy_docs')
                button.grid(row=row+2, column=2, padx=PAD, pady=PADB)
                button.widget.bind(
                    '<Button-1>', lambda event, arg=None:
                    self._copy_file(missing_files[0]))

            row += 1
        return frame

    def _missing_file_label(self, frame: ttk.Frame,
                            file_name: str) -> ttk.Label:
        style = ''
        if not file_name:
            file_name = '-- missing --'
            style = 'red-fg.TLabel'
        label = ttk.Label(frame, text=file_name, style=style)
        self.destroy_widgets.append(label)
        return label

    def _mismatch_frame(self, container: ttk.Frame,
                        mismatches: list[str]) -> ttk.Frame:
        frame = ttk.Frame(container)
        self.destroy_widgets.append(frame)

        label = ttk.Label(frame, text=' Mismatches', style='blue-fg.TLabel')
        label.grid(row=0, column=0, sticky=tk.W)
        self.destroy_widgets.append(label)

        if not mismatches:
            label = ttk.Label(frame, text='None')
            label.grid(row=1, column=0)
            self.destroy_widgets.append(label)
            return frame

        for row, item in enumerate(sorted(mismatches)):
            button = ttk.Radiobutton(
                frame,
                text=item,
                value=item,
                variable=self.mismatch,
                command=self.rb_selected
            )
            button.grid(row=row+2, column=0, sticky=tk.W)
            self.destroy_widgets.append(button)

        return frame

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

    def _copy_file(self, file_name: str) -> None:
        source = Path(self.env_version.dir, file_name)
        item = 'file'
        if source.is_dir():
            item = 'directory'
        dlg = messagebox.askokcancel(
            '', f'Copy this {item}? ({file_name})', parent=self.root)
        if not dlg:
            return

        destination = Path(self.project.source_dir, file_name)

        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            print(f'{source=}')
            print(f'{destination=}')
            shutil.copyfile(source, destination)
        notify(FRAME_TITLE, f'Item {file_name} copied')

        for widget in self.missing_file_frame.winfo_children():
            widget.destroy()
        self.compare_project()

    def _dismiss(self, *args) -> None:
        self.root.destroy()
