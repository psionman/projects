
"""ProjectEditFrame  for <application>."""
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path

from psiutils.constants import PAD, Status, Mode
from psiutils.buttons import ButtonFrame, IconButton
from psiutils.utilities import window_resize, geometry

from projects.project import Project
from projects.constants import APP_TITLE
from projects.config import read_config
from projects.text import Text
from projects import logger

txt = Text()
FRAME_TITLE = f'{APP_TITLE} - edit'

DEFAULT_DEV_DIR = str(Path(Path.home(), '.pyenv', 'versions'))
DEFAULT_PROJECT_DIR = str(Path(Path.home(), 'projects'))
DEFAULT_VERSION_TEXT = '0.0.0'


class ProjectEditFrame():
    def __init__(self, parent, mode: int, project: Project = None) -> None:
        self.root = tk.Toplevel(parent.root)
        self.parent = parent
        self.config = read_config()
        self.mode = mode
        self.project = project
        self.projects = parent.projects
        if project:
            project.env_versions: list = project.get_versions()

        self.status = Status.NULL

        if not project:
            project = Project()
            project.source_dir = DEFAULT_PROJECT_DIR
            project.version_text = DEFAULT_VERSION_TEXT
            project.pypi = False
        self.project = project

        self.button_frame = None

        # tk variables
        self.project_name = tk.StringVar(value=project.name)
        self.source_dir = tk.StringVar(value=project.source_dir)
        self.project_version = tk.StringVar(value=project.version_text)
        self.version = tk.StringVar(value=project.version_text)
        self.pypi = tk.BooleanVar(value=project.pypi)
        self.build_for_windows = tk.BooleanVar(value=project.build_for_windows)
        self.script = tk.StringVar(value=project.script)
        self.repository_name = tk.StringVar(value=project.repository_name)

        # Trace
        self.project_name.trace_add('write', self._check_value_changed)
        self.source_dir.trace_add('write', self._check_value_changed)
        self.version.trace_add('write', self._check_value_changed)
        self.pypi.trace_add('write', self._check_value_changed)
        self.build_for_windows.trace_add('write', self._check_value_changed)
        self.script.trace_add('write', self._check_value_changed)
        self.repository_name.trace_add('write', self._check_value_changed)

        self._show()

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

        sizegrip = ttk.Sizegrip(root)
        sizegrip.grid(sticky=tk.SE)

    def _main_frame(self, master: tk.Frame) -> ttk.Frame:
        # pylint: disable=no-member)
        frame = ttk.Frame(master)
        frame.columnconfigure(2, weight=1)

        row = 0
        label = ttk.Label(frame, text='Project name')
        label.grid(row=row, column=0, sticky=tk.E, pady=PAD)

        state = 'readonly' if self.mode == Mode.EDIT else 'normal'
        entry = ttk.Entry(frame, textvariable=self.project_name, state=state)
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD)
        entry.focus_set()

        row += 1
        label = ttk.Label(frame, text='(Used to find dirs in virtual envs)')
        label.grid(row=row, column=1, sticky=tk.W, pady=0)

        row += 1
        label = ttk.Label(frame, text='Current_version')
        label.grid(row=row, column=0, sticky=tk.E, pady=PAD)

        entry = ttk.Entry(
            frame, textvariable=self.project_version, state='readonly')
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD)

        row += 1
        label = ttk.Label(frame, text='Source dir')
        label.grid(row=row, column=0, sticky=tk.E, pady=PAD)

        entry = ttk.Entry(frame, textvariable=self.source_dir)
        entry.grid(row=row, column=1, columnspan=2, padx=PAD, sticky=tk.EW)

        button = IconButton(
            frame, txt.OPEN, 'open', self._get_source_dir)
        button.grid(row=row, column=3)

        row += 1
        label = ttk.Label(frame, text='script')
        label.grid(row=row, column=0, sticky=tk.E, pady=PAD)

        entry = ttk.Entry(frame, textvariable=self.script)
        entry.grid(row=row, column=1, columnspan=2, padx=PAD, sticky=tk.EW)

        button = IconButton(
            frame, txt.OPEN, 'open', self._get_script)
        button.grid(row=row, column=3, pady=PAD)

        row += 1
        check_button = ttk.Checkbutton(
            frame, text='PyPi project', variable=self.pypi)
        check_button.grid(row=row, column=1, sticky=tk.W)

        row += 1
        check_button = ttk.Checkbutton(
            frame, text='Build for windows', variable=self.build_for_windows)
        check_button.grid(row=row, column=1, sticky=tk.W)

        # row += 1
        # label = ttk.Label(frame, text='Repository name')
        # label.grid(row=row, column=0, sticky=tk.E, padx=PAD, pady=PAD)

        # entry = ttk.Entry(frame, textvariable=self.repository_name)
        # entry.grid(row=row, column=1, sticky=tk.EW)

        row += 1
        frame.rowconfigure(row, weight=1)

        row += 1
        self.button_frame = self._button_frame(frame)
        self.button_frame.grid(row=row, column=0, columnspan=4,
                               sticky=tk.EW, padx=PAD, pady=PAD)
        return frame

    def _button_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ButtonFrame(master, tk.HORIZONTAL)
        frame.buttons = [
            frame.icon_button('save', self._save, True),
            frame.icon_button('exit', self._dismiss),
        ]
        frame.enable(False)
        return frame

    def _get_source_dir(self, *args) -> None:
        if directory := filedialog.askdirectory(
                initialdir=self.source_dir.get(),
                parent=self.root,):
            self.source_dir.set(directory)

    def _get_script(self, *args) -> None:
        # pylint: disable=no-member)
        initialdir = self.config.script_directory
        if self.script.get():
            initialdir = Path(self.script.get()).parent

        if directory := filedialog.askopenfilename(
                initialdir=initialdir,
                initialfile=self.script.get(),
                parent=self.root,):
            self.script.set(directory)

    def _check_value_changed(self, *args) -> None:
        enable = self._record_changes()
        self.button_frame.enable(enable)

    def _save(self, *args) -> None:
        changes = self._record_changes()
        ic(changes)
        if self.mode == Mode.NEW:
            self.project = Project()
            self.project.name = self.project_name.get()
            self.projects[self.project.name] = self.project

            logger.info(
                "New project",
                name=self.project.name
            )

        self.project.source_dir = self.source_dir.get()
        self.project.pypi = self.pypi.get()
        self.project.build_for_windows = self.build_for_windows.get()
        self.project.script = self.script.get()
        self.project.repository_name = self.repository_name.get()

        logger.info(
            "Project changed",
            changes=changes
        )

        self.parent.project_server.save_projects(self.projects)
        self.project_version.set(self.project.version_text)
        self.status = Status.UPDATED
        self._dismiss()

    def _record_changes(self) -> dict:
        changes = {}
        if self.project.name != self.project_name.get():
            changes['project_name'] = (
                self.project.name, self.project_name.get())
        if self.project.source_dir != self.source_dir.get():
            changes['source_dir'] = (
                 self.project.source_dir, self.source_dir.get())
        if self.project.pypi != self.pypi.get():
            changes['pypi'] = (self.project.pypi, self.pypi.get())
        if self.project.build_for_windows != self.build_for_windows.get():
            changes['build_for_windows'] = (
                self.project.build_for_windows, self.build_for_windows.get())
        if self.project.script != self.script.get():
            changes['script'] = (self.project.script, self.script.get())
        if self.project.repository_name != self.repository_name.get():
            changes['repository'] = (
                self.project.repository_name, self.repository_name.get()
                )

        return changes

    def _dismiss(self, *args) -> None:
        self.root.destroy()
