"""
GUI for comparing and building Python package versions.

This module defines the ProjectVersionsFrame class, which provides a
Tkinter-based interface for selecting, comparing, and
building different development versions of a Python package project.
It interacts with project configuration data, performs version comparisons,
and integrates build and compare workflows via modular frames.

Intended for use within the PSI package build system.
"""
import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from psiutils.constants import PAD, Status, Mode
from psiutils.buttons import ButtonFrame
from psiutils.utilities import window_resize, geometry

from projects.project import Project
from projects.config import read_config
from projects.compare import compare
from projects.project_utilities import update_project
from projects.build import UV_PUBLISH_TOKEN
from projects import logger

from projects.forms.frm_compare import CompareFrame
from projects.forms.frm_build import BuildFrame

FRAME_TITLE = 'Project compare versions'

DEFAULT_DEV_DIR = str(Path(Path.home(), '.pyenv', 'versions'))
DEFAULT_PROJECT_DIR = str(Path(Path.home(), 'projects'))


class ProjectVersionsFrame():
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
            self,
            parent,
            mode: int,
            project: Project = None,
            refresh: bool = False) -> None:
        self.root = tk.Toplevel(parent.root)
        self.parent = parent
        self.config = read_config()
        self.mode = mode
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
        self.source_dir = tk.StringVar(value=project.source_dir)
        self.project_version = tk.StringVar(value=self.project.version_text)
        self.version = tk.StringVar()

        # Trace
        self.project_name.trace_add('write', self._values_changed)
        self.env_dir.trace_add('write', self._values_changed)
        self.source_dir.trace_add('write', self._values_changed)
        self.version.trace_add('write', self._values_changed)

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
        frame = ttk.Frame(master)
        frame.rowconfigure(5, weight=1)
        frame.columnconfigure(2, weight=1)

        label = ttk.Label(frame, text='Project name')
        label.grid(row=0, column=0, sticky=tk.E, pady=PAD)

        state = 'readonly' if self.mode == Mode.EDIT else 'normal'
        entry = ttk.Entry(frame, textvariable=self.project_name, state=state)
        entry.grid(row=0, column=1, sticky=tk.EW, padx=PAD)
        entry.focus_set()

        label = ttk.Label(frame, text='(Used to find dirs in virtual envs)')
        label.grid(row=1, column=1, sticky=tk.W, pady=0)

        label = ttk.Label(frame, text='Current_version')
        label.grid(row=2, column=0, sticky=tk.E, pady=PAD)

        entry = ttk.Entry(
            frame, textvariable=self.project_version, state='readonly')
        entry.grid(row=2, column=1, sticky=tk.EW, padx=PAD)

        label = ttk.Label(frame, text='Project dir')
        label.grid(row=3, column=0, sticky=tk.E, pady=PAD)

        entry = ttk.Entry(
            frame, textvariable=self.source_dir, state='readonly')
        entry.grid(row=3, column=1, columnspan=2, padx=PAD, sticky=tk.EW)

        label = ttk.Label(frame, text='Development version')
        label.grid(row=4, column=1, sticky=tk.W, pady=PAD)

        self.versions_frame = self._versions_frame(frame)
        self.versions_frame.grid(row=5, column=0, columnspan=3, sticky=tk.NSEW)

        self.button_frame = self._button_frame(frame)
        self.button_frame.grid(row=0, column=4, rowspan=9,
                               sticky=tk.NS, padx=PAD, pady=PAD)
        return frame

    def _versions_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ttk.Frame(master, relief="sunken", borderwidth=2)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(frame, borderwidth=0)
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas_frame = self._canvas_frame(self.canvas)
        self.canvas_frame.bind("<Button-4>", self._on_mouse_wheel)
        self.canvas_frame.bind("<Button-5>", self._on_mouse_wheel)

        v_scroll = tk.Scrollbar(
            frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scroll.grid(row=0, column=1, sticky=tk.NS)

        self.canvas.configure(yscrollcommand=v_scroll.set)
        self.canvas_frame_id = self.canvas.create_window(
            (4, 4), window=self.canvas_frame, anchor=tk.NW)
        self._populate_versions_frame()
        return frame

    def _on_canvas_configure(self, event):
        # Match inner frame’s width to canvas’s width
        self.canvas.itemconfig(self.canvas_frame_id, width=event.width)

    def _button_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ButtonFrame(master, tk.VERTICAL)
        frame.buttons = [
            frame.icon_button('build', self._build_project),
            frame.icon_button('compare', self._compare_project, True),
            frame.icon_button('update', self._update_project, True),
            frame.icon_button('code', self._open_code, True),
            frame.icon_button('exit', self._dismiss),
        ]
        frame.enable(False)
        return frame

    def _canvas_frame(self, master) -> tk.Frame:
        frame = tk.Frame(master, background='#ccc')
        frame.bind("<Configure>", self._frame_configure)
        return frame

    def _frame_configure(self, *args):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _populate_versions_frame(self) -> None:
        self.project.env_versions = self.project.get_versions(self.refresh)
        if self.refresh:
            self.project_server.save_projects()
        self.refresh = False
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        versions = self.project.env_versions
        for row, name in enumerate(sorted(list(versions))):
            version = versions[name]
            style = ''
            (missing, mismatches) = compare(self.project.source_dir,
                                            version.dir)
            style = ''
            mismatch_str = ''
            style = 'green-fg.TRadiobutton'
            missing_files = []
            for count, item in enumerate(missing):
                if count < 5:
                    if item[0]:
                        missing_files.append(item[0])

                    if item[1]:
                        missing_files.append(item[1])

            if missing or mismatches:
                style = 'red-fg.TRadiobutton'
                # style.config('width', 500)
                if '_version.py' in mismatches:
                    mismatches.remove('_version.py')
                mismatch_str = ' '.join(mismatches + missing_files)
                if len(mismatch_str) > 50:
                    mismatch_str = f'{mismatch_str[:50]} ...'
            display_text = (f'{name} : ({version.version}) '
                            f'{mismatch_str}')

            button = ttk.Radiobutton(
                self.canvas_frame,
                text=display_text,
                variable=self.version,
                value=version.name,
                style=style,
            )
            button.grid(row=row, column=0, sticky=tk.W)

    def _on_mouse_wheel(self, event):
        if event.num == 4:   # Linux scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.yview_scroll(1, "units")
        else:                # Windows / macOS
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def _values_changed(self, *args) -> None:
        enable = bool(self.project_name.get())
        self.button_frame.enable(enable)

    def _compare_project(self) -> None:
        if not Path(self.project.env_dir).is_dir():
            messagebox.showerror(
                'Path error',
                f'{self.project.env_dir} \nis not a directory!',
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
            self.version.get(), env_version, self.project.name)

        if returncode == 0:
            self._populate_versions_frame()
            messagebox.showinfo('', 'Package updated')

        self.refresh = True
        self._populate_versions_frame()

    def _build_project(self, *args) -> None:
        if not UV_PUBLISH_TOKEN:
            messagebox.showerror('', 'UV_PUBLISH_TOKEN not set.')
            return

        if not self._is_valid():
            return

        dlg = BuildFrame(self, self.project)
        self.root.wait_window(dlg.root)

    def _is_valid(self) -> bool:
        if self.project.py_project_missing:
            messagebox.showerror('', 'py_project.toml missing')
            return False
        return True

    def _open_code(self, *args) -> None:
        env_version = self.project.env_versions[self.version.get()]
        subprocess.call(['codium', '-n', env_version.dir])

    def _dismiss(self, *args) -> None:
        """
        Close the window and destroy the Toplevel widget.

        Typically bound to an exit button or key event to _dismiss the frame.
        """
        self.root.destroy()
