"""
GUI for comparing and building Python package versions.

This module defines the ProjectVersionsFrame class, which provides a
Tkinter-based interface for selecting, comparing, and
building different development versions of a Python package project.
It interacts with project configuration data, performs version comparisons,
and integrates build and compare workflows via modular frames.

Intended for use within the PSI package build system.
"""

import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from psiutils.constants import PAD, Mode, Status, WidgetState
from psiutils.utilities import geometry, window_resize
from psiutils.widgets import ScrollingCanvas

from projects.build import UV_PUBLISH_TOKEN
from projects.buttons import ButtonFrame
from projects.compare import compare
from projects.config import read_config
from projects.constants import VERSION_FILE
from projects.forms.frm_build import BuildFrame
from projects.forms.frm_compare import CompareFrame
from projects.project import Project
from projects.project_utilities import update_project
from projects.utilities import call_process

FRAME_TITLE = "Project compare versions"

DEFAULT_DEV_DIR = str(Path(Path.home(), ".pyenv", "versions"))
DEFAULT_PROJECT_DIR = str(Path(Path.home(), "projects"))


UP_TO_DATE_STYLE = "green-fg.TRadiobutton"
OUT_OF_DATE_STYLE = "blue-fg.TRadiobutton"
MODIFIED_STYLE = "red-fg.TRadiobutton"


class ProjectVersionsFrame:
    """
    A GUI frame for selecting, comparing, and building project versions.

    This class provides a Tkinter-based interface for working with multiple
    development versions of a Python projects. It allows the user to:

    - View and select available development versions.
    - Compare selected versions to the main project directory.
    - Build a selected version after validation.

    Attributes:
        root (tk.Toplevel): The top-level window for this frame.
        parent: The parent window or frame.
        config (dict): Configuration values loaded via `read_config`.
        mode (int): Determines whether fields are editable (e.g., `Mode.EDIT`).
        project (Project): The project currently being displayed
            and manipulated.
        projects (list): A list of available projects from the parent.
        save_button: Optional save button (currently unused).
        versions_frame (tk.Frame): Frame containing version selection buttons.
        button_frame (tk.Frame):
            Frame containing action buttons (Compare, Build, Exit).
        project_name, env_dir, source_dir, project_version,
            version (tk.StringVar):

        Tkinter variables bound to GUI widgets,
            used for user input and display.

    Methods:
        show(): Initializes and lays out the main GUI window.
        _dismiss(): Closes the window.
        _main_frame(master): Creates the main layout frame with widgets.
        _versions_frame(master): Creates the container for version options.
        _button_frame(master): Sets up action buttons.
        _populate_versions_frame(): Fills the versions frame with radio buttons
            and version info.
        _values_changed(*args): Enables/disables buttons based on
            field changes.
        _compare_project(): Launches comparison window for selected version.
        _build_project(): Opens build dialog for selected version.
        _is_valid(): Checks project integrity before building.
    """

    def __init__(
        self, parent, project: Project = None, refresh: bool = False
    ) -> None:
        self.root = tk.Toplevel(parent.root)
        self.parent = parent
        self.config = read_config()
        self.mode = Mode.VIEW
        self.project = project
        self.project_server = parent.project_server
        self.save_button = None
        self.versions_frame = None
        self.button_frame = None
        self.canvas = None
        self.canvas_frame = None
        self.canvas_frame_id = None

        if not project.cached_envs:
            refresh = True
        self.refresh = refresh

        self.status = Status.NULL

        if not project:
            project = Project()
            project.env_dir = DEFAULT_DEV_DIR
            project.source_dir = DEFAULT_PROJECT_DIR
        self.project = project

        # tk variables
        self.project_name = tk.StringVar(value=project.name)
        self.env_dir = tk.StringVar(value=project.env_dir)
        self.base_dir = tk.StringVar(value=project.base_dir)
        self.project_version = tk.StringVar(value=self.project.version_text)
        self.version = tk.StringVar()

        # Trace
        self.project_name.trace_add("write", self._values_changed)
        self.env_dir.trace_add("write", self._values_changed)
        self.base_dir.trace_add("write", self._values_changed)
        self.version.trace_add("write", self._values_changed)

        self._show()
        self._populate_versions_frame()

    def _show(self) -> None:
        """
        Display the project version selection window.

        Sets up and displays the Toplevel window with layout, event bindings,
        title, geometry, and resizing behaviour. Builds the main interface
        frame and adds a size grip for window resizing.

        Typically called during initialization to render the window.
        """
        root = self.root
        root.geometry(geometry(self.config, __file__))
        root.title(FRAME_TITLE)
        root.transient(self.parent.root)
        root.bind("<Control-x>", self._dismiss)
        root.bind(
            "<Configure>",
            lambda event, arg=None: window_resize(self, __file__),
        )

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        main_frame = self._main_frame(root)
        main_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=PAD, pady=PAD)

        sizegrip = ttk.Sizegrip(root)
        sizegrip.grid(sticky=tk.SE)

    def _main_frame(self, master: tk.Frame) -> ttk.Frame:
        frame = ttk.Frame(master)
        frame.rowconfigure(5, weight=1)
        frame.columnconfigure(2, weight=1)

        row = 0
        label = ttk.Label(frame, text="Project name")
        label.grid(row=row, column=0, sticky=tk.E, pady=PAD)

        state = (
            WidgetState.NORMAL
            if self.mode == Mode.EDIT
            else WidgetState.READONLY
        )
        entry = ttk.Entry(frame, textvariable=self.project_name, state=state)
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD)
        if state == WidgetState.NORMAL:
            entry.focus_set()

        label = ttk.Label(frame, text="(Used to find dirs in virtual envs)")
        label.grid(row=row, column=2, sticky=tk.W, pady=0)

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
        label = ttk.Label(frame, text="Project dir")
        label.grid(row=row, column=0, sticky=tk.E, pady=PAD)

        entry = ttk.Entry(
            frame, textvariable=self.base_dir, state=WidgetState.READONLY
        )
        entry.grid(row=row, column=1, columnspan=2, padx=PAD, sticky=tk.EW)

        row += 1
        label = ttk.Label(frame, text="Development versions")
        label.grid(row=row, column=0, sticky=tk.W, pady=PAD)

        row += 2  # !!!
        self.versions_frame = ScrollingCanvas(
            frame,
            relief=tk.SUNKEN,
            borderwidth=2,
        )
        self.versions_frame.grid(
            row=row, column=0, columnspan=3, sticky=tk.NSEW
        )

        self.button_frame = self._button_frame(frame)
        self.button_frame.grid(
            row=0, column=4, rowspan=999, sticky=tk.NS, padx=PAD, pady=PAD
        )
        return frame

    def _button_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ButtonFrame(master, tk.VERTICAL)
        frame.buttons = [
            frame.icon_button("build", self._build_project),
            frame.icon_button("folder-open", self._open_dolphin, True),
            frame.icon_button("compare-orange", self._compare_project, True),
            frame.icon_button("update", self._update_project, True),
            frame.icon_button("code-blue", self._open_code, True),
            frame.icon_button("windsurf", self._open_windsurf, True),
            frame.icon_button("exit-orange", self._dismiss),
        ]
        frame.enable(False)
        return frame

    def _populate_versions_frame(self) -> None:
        self.project.env_versions = self.project.get_versions(self.refresh)
        if self.refresh:
            self.project_server.save_projects()
        self.refresh = False

        versions = self.project.env_versions
        for row, name in enumerate(sorted(list(versions))):
            version = versions[name]
            (missing, mismatches) = compare(
                self.project.source_dir, version.dir
            )

            mismatch_str = self._get_mismatch_str(missing, mismatches)
            display_text = f"{name} : ({version.version}) {mismatch_str}"
            button_style = self._button_style(version, mismatch_str)

            button = ttk.Radiobutton(
                self.versions_frame.content,
                text=display_text,
                variable=self.version,
                value=version.name,
                style=button_style,
            )
            button.grid(row=row, column=0, sticky=tk.W)

    def _button_style(self, version, mismatch_str: str) -> str:
        if "999" in version.version:
            return MODIFIED_STYLE
        if mismatch_str:
            return OUT_OF_DATE_STYLE
        return UP_TO_DATE_STYLE

    def _get_mismatch_str(self, missing: list, mismatches: list) -> str:
        if not missing and not mismatches:
            return ""
        missing_files = self._missing_files(missing)
        if VERSION_FILE in mismatches:
            mismatches.remove(VERSION_FILE)
        return self._mismatch_str(missing_files, mismatches)

    def _missing_files(self, missing: list) -> list:
        missing_files = []
        for item in missing:
            missing_files.append(item.file_name)
        return missing_files[:5]

    def _mismatch_str(self, missing_files: list, mismatches: list) -> str:
        mismatch_str = " ".join(mismatches + missing_files)
        if len(mismatch_str) > 50:
            mismatch_str = f"{mismatch_str[:50]} ..."
        return mismatch_str

    def _values_changed(self, *args) -> None:
        enable = bool(self.project_name.get())
        self.button_frame.enable(enable)

    def _compare_project(self) -> None:
        if not Path(self.project.env_dir).is_dir():
            messagebox.showerror(
                "Path error",
                f"{self.project.env_dir} \nis not a directory!",
                parent=self.root,
            )
            return

        env_version = self.project.env_versions[self.version.get()]
        dlg = CompareFrame(self, self.project, env_version)
        self.root.wait_window(dlg.root)
        self._populate_versions_frame()

    def _update_project(self) -> None:
        env_version = self.project.env_versions[self.version.get()]
        returncode = update_project(
            self.version.get(), env_version, self.project.name
        )

        if returncode == 0:
            self._populate_versions_frame()
            messagebox.showinfo("", "Project updated")

        self.refresh = True
        self._populate_versions_frame()

    def _build_project(self, *args) -> None:
        if not UV_PUBLISH_TOKEN:
            messagebox.showerror("", "UV_PUBLISH_TOKEN not set.")
            return

        if not self._is_valid():
            return

        dlg = BuildFrame(self, self.project)
        self.root.wait_window(dlg.root)

    def _is_valid(self) -> bool:
        if self.project.py_project_missing:
            messagebox.showerror("", "py_project.toml missing")
            return False
        return True

    def _open_dolphin(self, *args) -> None:
        env_version = self.project.env_versions[self.version.get()]
        subprocess.call(["dolphin", env_version.dir])

    def _open_code(self, *args) -> None:
        env_version = self.project.env_versions[self.version.get()]
        subprocess.call(["codium", "-n", env_version.dir])

    def _open_windsurf(self, *args) -> None:
        env_version = self.project.env_versions[self.version.get()]
        print(f"Opening windsurf for {env_version.dir}")
        try:
            return call_process(["windsurf", env_version.dir])
        except FileNotFoundError:
            messagebox.showerror("", "windsurf not found.")

    def _dismiss(self, *args) -> None:
        """
        Close the window and destroy the Toplevel widget.

        Typically bound to an exit button or key event to _dismiss the frame.
        """
        self.root.destroy()
