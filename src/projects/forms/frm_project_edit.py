"""ProjectEditFrame  for projects."""

import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from psiutils.buttons import ButtonFrame, IconButton
from psiutils.constants import PAD, Mode, Status, WidgetState
from psiutils.utilities import geometry, window_resize

from projects import logger
from projects.config import config
from projects.constants import APP_TITLE, ICON_DIR
from projects.data_store import store as data_store
from projects.forms.frm_ide_colours import IdeColoursFrame
from projects.project import Project
from projects.text import Text
from projects.utilities import call_process

txt = Text()
FRAME_TITLE = f"{APP_TITLE} - edit"

DEFAULT_DEV_DIR = str(Path(Path.home(), ".pyenv", "versions"))
DEFAULT_PROJECT_DIR = str(Path(Path.home(), "projects"))


class ColourLabel(ttk.Label):
    def __init__(self, *args, **kwargs):
        self.colour = ""
        if "colour" in kwargs:
            self.colour = kwargs["colour"]
            kwargs.pop("colour")
        super().__init__(*args, **kwargs)


class ProjectEditFrame:
    def __init__(self, parent, mode: int, project: Project = None) -> None:
        self.root = tk.Toplevel(parent.root)
        self.parent = parent
        self.mode = mode
        self.status = Status.NULL
        self.style = ttk.Style()
        self.script_button = None
        self.desktop_button = None

        if not project:
            project = Project()
        self.project = project

        self.button_frame = None

        # tk variables
        self.project_name = tk.StringVar(value=project.name)
        self.base_dir = tk.StringVar(value=project.base_dir)
        self.source_dir = tk.StringVar(value=project.source_dir)
        self.project_version = tk.StringVar(value=project.version_text)
        self.version = tk.StringVar(value=project.version_text)
        self.pypi = tk.BooleanVar(value=project.pypi)
        self.build_for_windows = tk.BooleanVar(value=project.build_for_windows)
        self.desktop_file = tk.StringVar(value=project.desktop_file)
        self.script = tk.StringVar(value=project.script)
        self.repository = tk.StringVar(value=project.repository)

        # Trace
        self.project_name.trace_add("write", self._check_value_changed)
        self.base_dir.trace_add("write", self._check_value_changed)
        self.source_dir.trace_add("write", self._check_value_changed)
        self.version.trace_add("write", self._check_value_changed)
        self.pypi.trace_add("write", self._check_value_changed)
        self.build_for_windows.trace_add("write", self._check_value_changed)
        self.script.trace_add("write", self._check_value_changed)
        self.desktop_file.trace_add("write", self._check_value_changed)
        self.repository.trace_add("write", self._check_value_changed)

        self._show()

        print(f"Script: {self.script.get()}")
        print(f"Script exists: {Path(self.script.get()).exists()}")
        print(f"Desktop file: {self.desktop_file.get()}")
        print(f"Desktop file exists: {Path(self.desktop_file.get()).exists()}")
        if not Path(self.script.get()).is_file():
            self.script_button.enable(False)
        if not Path(self.desktop_file.get()).is_file():
            self.desktop_button.enable(False)

    def _show(self) -> None:
        root = self.root
        root.geometry(geometry(config, __file__))
        root.title(FRAME_TITLE)
        root.transient(self.parent.root)

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        main_frame = self._main_frame(root)
        main_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=PAD, pady=PAD)

        sizegrip = ttk.Sizegrip(root)
        sizegrip.grid(sticky=tk.SE)

        root.update_idletasks()
        root.bind("<Control-x>", self._dismiss)
        root.bind(
            "<Configure>",
            lambda event, arg=None: window_resize(root, __file__, config),
        )

    def _main_frame(self, master: tk.Frame) -> ttk.Frame:
        frame = ttk.Frame(master)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        project_frame = self._project_frame(frame)
        project_frame.grid(row=0, column=0, sticky=tk.NSEW)

        self.button_frame = self._button_frame(frame)
        self.button_frame.grid(
            row=0, column=1, sticky=tk.NS, padx=PAD, pady=PAD
        )
        return frame

    def _project_frame(self, master: tk.Frame) -> ttk.Frame:
        frame = ttk.Frame(master)
        frame.columnconfigure(1, weight=1)

        row = 0
        label = ttk.Label(frame, text="Project name")
        label.grid(row=row, column=0, sticky=tk.E, pady=PAD)

        state = (
            WidgetState.NORMAL
            if self.mode in (Mode.EDIT, Mode.NEW)
            else WidgetState.READONLY
        )
        entry = ttk.Entry(frame, textvariable=self.project_name, state=state)
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD)
        entry.focus_set()

        row += 1
        label = ttk.Label(frame, text="Current_version")
        label.grid(row=row, column=0, sticky=tk.E, pady=PAD)

        entry = ttk.Entry(
            frame,
            textvariable=self.project_version,
            state=WidgetState.READONLY,
        )
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD)

        row += 1
        label = ttk.Label(frame, text="Base dir")
        label.grid(row=row, column=0, sticky=tk.E, pady=PAD)

        entry = ttk.Entry(frame, textvariable=self.base_dir)
        entry.grid(row=row, column=1, columnspan=2, padx=PAD, sticky=tk.EW)

        button = IconButton(frame, txt.OPEN, "open", self._get_base_dir)
        button.grid(row=row, column=3, pady=PAD)

        row += 1
        label = ttk.Label(frame, text="Source dir")
        label.grid(row=row, column=0, sticky=tk.E, pady=PAD)

        entry = ttk.Entry(frame, textvariable=self.source_dir)
        entry.grid(row=row, column=1, columnspan=2, padx=PAD, sticky=tk.EW)

        button = IconButton(frame, txt.OPEN, "open", self._get_source_dir)
        button.grid(row=row, column=3)

        row += 1
        label = ttk.Label(frame, text="Desktop file")
        label.grid(row=row, column=0, sticky=tk.E, pady=PAD)

        entry = ttk.Entry(frame, textvariable=self.desktop_file)
        entry.grid(row=row, column=1, columnspan=2, padx=PAD, sticky=tk.EW)

        button = IconButton(frame, txt.OPEN, "open", self._get_desktop_file)
        button.grid(row=row, column=3, pady=PAD)

        row += 1
        label = ttk.Label(frame, text="script")
        label.grid(row=row, column=0, sticky=tk.E, pady=PAD)

        entry = ttk.Entry(frame, textvariable=self.script)
        entry.grid(row=row, column=1, columnspan=2, padx=PAD, sticky=tk.EW)

        button = IconButton(frame, txt.OPEN, "open", self._get_script)
        button.grid(row=row, column=3, pady=PAD)

        row += 1
        check_button = ttk.Checkbutton(
            frame, text="PyPi project", variable=self.pypi
        )
        check_button.grid(row=row, column=1, sticky=tk.W)

        row += 1
        check_button = ttk.Checkbutton(
            frame, text="Build for windows", variable=self.build_for_windows
        )
        check_button.grid(row=row, column=1, sticky=tk.W)
        return frame

    def _button_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ButtonFrame(master, tk.VERTICAL)

        self.desktop_button = IconButton(
            frame, "Edit Desktop", "script", self._edit_desktop
        )
        frame.buttons = [
            IconButton(
                frame,
                txt.IDE_COLOURS,
                "palette",
                self._project_colours,
                icon_path=ICON_DIR,
            ),
            IconButton(
                frame,
                "Edit Desktop",
                "script",
                self._edit_desktop,
                tag="desktop",
            ),
            IconButton(
                frame,
                txt.EDIT_SCRIPT,
                "script",
                self._edit_script,
                tag="script",
            ),
            frame.icon_button("save", self._save, True),
            frame.icon_button("exit-orange", self._dismiss),
        ]
        self.script_button = frame.tagged_buttons["script"]
        self.desktop_button = frame.tagged_buttons["desktop"]
        frame.enable(False)
        return frame

    def _get_base_dir(self, *args) -> None:
        if self.base_dir.get():
            init_dir = self.base_dir.get()
        else:
            init_dir = DEFAULT_PROJECT_DIR
        if directory := filedialog.askdirectory(
            initialdir=init_dir,
            parent=self.root,
        ):
            self.base_dir.set(directory)

    def _get_source_dir(self, *args) -> None:
        if self.source_dir.get():
            init_dir = self.source_dir.get()
        else:
            init_dir = self.base_dir.get()

        if directory := filedialog.askdirectory(
            initialdir=init_dir,
            parent=self.root,
        ):
            self.source_dir.set(directory)

    def _get_desktop_file(self, *args) -> None:
        initialdir = config.desktop_directory
        if self.desktop_file.get():
            initialdir = Path(self.desktop_file.get()).parent
        path = self.ask_save_path(initialdir)

        if path:
            self.desktop_file.set(path)

    def _get_script(self, *args) -> None:
        initialdir = config.script_directory
        if self.script.get():
            initialdir = Path(self.script.get()).parent
        path = self.ask_save_path(initialdir)

        if path:
            self.script.set(path)

    def ask_save_path(self, initialdir: Path):
        path = filedialog.asksaveasfilename(
            title="Choose file",
            initialdir=initialdir,
            confirmoverwrite=False,
        )

        if not path:
            return None  # user cancelled dialog

        if os.path.exists(path):
            # file exists → just return it (or optionally confirm overwrite)
            return path
        else:
            # file does not exist → ask to create
            create = messagebox.askyesno(
                "Create file?", f"{path} does not exist.\nCreate it?"
            )
            if create:
                with open(path, "w") as f_script:
                    f_script.write("")
                return path
            else:
                return None

    def _check_value_changed(self, *args) -> None:
        enable = self._record_changes()
        self.button_frame.enable(enable)
        self.script_button.enable(Path(self.script.get()).is_file())
        self.desktop_button.enable(Path(self.desktop_file.get()).is_file())

    def _record_changes(self) -> dict:
        changes = {}
        if self.project.name != self.project_name.get():
            changes["project_name"] = (
                self.project.name,
                self.project_name.get(),
            )
        if self.project.base_dir != self.base_dir.get():
            changes["base_dir"] = (
                self.project.base_dir,
                self.base_dir.get(),
            )

        if self.project.source_dir != self.source_dir.get():
            changes["source_dir"] = (
                self.project.source_dir,
                self.source_dir.get(),
            )
        if self.project.pypi != self.pypi.get():
            changes["pypi"] = (self.project.pypi, self.pypi.get())
        if self.project.build_for_windows != self.build_for_windows.get():
            changes["build_for_windows"] = (
                self.project.build_for_windows,
                self.build_for_windows.get(),
            )
        if self.project.script != self.script.get():
            changes["script"] = (self.project.script, self.script.get())

        if self.project.desktop_file != self.desktop_file.get():
            changes["desktop_file"] = (
                self.project.desktop_file,
                self.desktop_file.get(),
            )

        if self.project.repository != self.repository.get():
            changes["repository"] = (
                self.project.repository,
                self.repository.get(),
            )

        return changes

    def _project_colours(self, *args) -> None:
        dlg = IdeColoursFrame(self.root, self.project)
        self.root.wait_window(dlg.root)
        pass

    def _edit_script(self, *args) -> None:
        self.open_kate(self.project.script)

    def _edit_desktop(self, *args) -> None:
        self.open_kate(self.project.desktop_file)

    def open_kate(self, file_path: str) -> None:
        call_process(["kate", file_path])

    def _save(self, *args) -> None:
        changes = self._record_changes()
        if self.mode == Mode.NEW:
            self.project = Project()
            self.project.name = self.project_name.get()
            data_store.projects[self.project.name] = self.project

            logger.info("New project", name=self.project.name)

        self.project.base_dir = self.base_dir.get()
        self.project.source_dir = self.source_dir.get()
        self.project.pypi = self.pypi.get()
        self.project.build_for_windows = self.build_for_windows.get()
        self.project.script = self.script.get()
        self.project.desktop_file = self.desktop_file.get()
        self.project.repository = self.repository.get()

        # for key in self.project.workbench_colours.keys():
        #     colour = getattr(self, key).get()
        #     self.project.workbench_colours[key] = colour

        logger.info("Project changed", changes=changes)
        data_store.save_projects(data_store.projects)
        self.project_version.set(self.project.version_text)
        self.status = Status.UPDATED
        self._dismiss()

    def _dismiss(self, *args) -> None:
        self.root.destroy()
