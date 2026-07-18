"""Main frame for ..."""

import shutil
import subprocess
import tkinter as tk
from functools import partial
from pathlib import Path
from tkinter import messagebox, ttk

from psiutils.buttons import ButtonFrame, IconButton
from psiutils.constants import PAD, PADB, PADT, WidgetState
from psiutils.utilities import geometry, window_resize
from psiutils.widgets import ScrollingCanvas

from projects import logger
from projects.compare import Missing, compare
from projects.config import config
from projects.env_version import EnvironmentVersion
from projects.project import Project
from projects.text import Text
from projects.utilities import collapse_home

txt = Text()
FRAME_TITLE = "Compare files across directories"
MODIFIED_ENTRY_STYLE = "red-fg.TEntry"
MODIFIED_LABEL_STYLE = "red-fg.TLabel"


class CompareFrame:
    """Define the Main frame."""

    def __init__(
        self,
        parent: ttk.Frame,
        project: Project,
        env_version: EnvironmentVersion,
    ) -> None:
        self.root = tk.Toplevel(parent.root)
        self.parent = parent
        self.project = project
        self.env_version = env_version
        self.missing_frame = None
        self.mismatch_frame = None

        self.missing_frame = None
        self.button_frame = None
        self.diff_buttons = {}
        self.diff_buttons = {}
        self.copy_to_env_buttons = {}
        self.copy_to_live_buttons = {}
        if self.env_version.name in self.project.modified_versions:
            env_version.version = f"{env_version.version} (modified)"

        # Tk Variables
        self.project_name = tk.StringVar(value=project.name)
        self.env_dir = tk.StringVar(value=collapse_home(env_version.dir))
        self.source_dir = tk.StringVar(value=collapse_home(project.source_dir))
        self.env_version_version = tk.StringVar(value=env_version.version)
        self.project_version = tk.StringVar(value=project.version)
        self.mismatch = tk.StringVar(value="")
        self._show()

        (self.missing, self.mismatches) = compare(
            self.project.source_dir, self.env_version.dir
        )
        self._populate_missing_frame()
        self._populate_mismatches()

    def _show(self):
        self._configure()

        main_frame = self._main_frame(self.root)
        main_frame.grid(row=0, column=0, sticky=tk.NSEW)

        sizegrip = ttk.Sizegrip(self.root)
        sizegrip.grid(sticky=tk.SE)

    def _configure(self) -> None:
        root = self.root
        root.update_idletasks()
        root.geometry(geometry(config, __file__))
        root.transient(self.parent.root)
        root.bind("<Control-x>", self._dismiss)
        root.bind(
            "<Configure>",
            lambda event, arg=None: window_resize(root, __file__, config),
        )

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        root.title(f"{FRAME_TITLE}")

    def _main_frame(self, master: ttk.Frame) -> ttk.Frame:
        frame = ttk.Frame(master)
        frame.columnconfigure(0, weight=1)

        row = 0
        project_frame = self._project_frame(frame)
        project_frame.grid(row=row, column=0, sticky=tk.EW, padx=PAD, pady=PAD)

        row += 1
        label = ttk.Label(
            frame, text="Missing files and dirs", style="blue-fg.TLabel"
        )
        label.grid(row=row, column=0, sticky=tk.W, padx=PAD, pady=PADT)

        row += 1
        self.missing_frame = ttk.Frame(frame, relief=tk.SUNKEN, borderwidth=2)
        self.missing_frame.grid(
            row=row, column=0, sticky=tk.NW, padx=PAD, pady=PAD
        )

        row += 1
        label = ttk.Label(frame, text="Mismatches", style="blue-fg.TLabel")
        label.grid(row=row, column=0, sticky=tk.W, padx=PAD, pady=PADT)

        row += 1
        frame.rowconfigure(row, weight=1)
        self.mismatch_frame = ScrollingCanvas(
            frame,
            relief=tk.SUNKEN,
            borderwidth=2,
        )
        self.mismatch_frame.grid(
            row=row, column=0, sticky=tk.NSEW, padx=PAD, pady=PAD
        )

        row += 1
        self.button_frame = self._button_frame(frame)
        self.button_frame.grid(
            row=row, column=0, sticky=tk.EW, padx=PAD, pady=PAD
        )

        return frame

    def _project_frame(self, master: ttk.Frame) -> ttk.Frame:
        frame = ttk.Frame(master)
        frame.columnconfigure(2, weight=1)

        row = 0
        label = ttk.Label(frame, text="Project")
        label.grid(row=row, column=0, sticky=tk.E)

        entry = ttk.Entry(
            frame, textvariable=self.project_name, state=WidgetState.READONLY
        )
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD)

        row += 1
        label = ttk.Label(frame, text="Project version")
        label.grid(row=row, column=0, sticky=tk.E)

        entry = ttk.Entry(
            frame,
            textvariable=self.project_version,
            state=WidgetState.READONLY,
        )
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD)

        entry = ttk.Entry(
            frame, textvariable=self.source_dir, state=WidgetState.READONLY
        )
        entry.grid(row=row, column=2, sticky=tk.EW, padx=PAD)

        row += 1
        label = ttk.Label(frame, text="Env version")
        if self.env_version.name in self.project.modified_versions:
            label.configure(style=MODIFIED_LABEL_STYLE)
        label.grid(row=row, column=0, sticky=tk.E)

        entry = ttk.Entry(
            frame,
            textvariable=self.env_version_version,
            state=WidgetState.READONLY,
        )
        if self.env_version.name in self.project.modified_versions:
            entry.configure(style=MODIFIED_ENTRY_STYLE)
        entry.grid(row=row, column=1, sticky=tk.EW, padx=PAD)

        entry = ttk.Entry(
            frame, textvariable=self.env_dir, state=WidgetState.READONLY
        )
        if self.env_version.name in self.project.modified_versions:
            entry.configure(style=MODIFIED_ENTRY_STYLE)
        entry.grid(row=row, column=2, sticky=tk.EW, padx=PAD)

        return frame

    def _button_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ButtonFrame(master, tk.HORIZONTAL)
        frame.buttons = [
            # frame.icon_button("diff", self._show_differences, True),
            frame.icon_button("exit-orange", self._dismiss),
        ]
        frame.enable(False)
        return frame

    def _populate_missing_frame(self) -> None:
        (self.missing, self.mismatches) = compare(
            self.project.source_dir, self.env_version.dir
        )
        self._clear_frame(self.missing_frame)

        missing_button = False
        for missing in self.missing:
            if not missing_button and missing.file_name.endswith(".orig"):
                button = IconButton(
                    self.missing_frame,
                    "Delete orig",
                    "delete",
                    self._delete_orig,
                )
                button.grid(row=0, column=2, padx=PAD, pady=PADB)
                print(f"Original file: {missing.file_name}")
                missing_button = True
        if not self.missing:
            self._populate_no_missing_items()
        self._populate_missing_items()

    def _populate_no_missing_items(self) -> None:
        row = 1
        label = ttk.Label(
            self.missing_frame, text="None", style="green-fg.TLabel"
        )
        label.grid(row=row, column=0)

    def _populate_missing_items(self) -> None:
        frame = self.missing_frame
        row = 0
        label = ttk.Label(frame, text="Env dir")
        label.grid(row=row, column=0, padx=PAD, sticky=tk.W)

        label = ttk.Label(frame, text="Project dir")
        label.grid(row=row, column=1, sticky=tk.W)

        for missing_file in self.missing:
            row += 1
            self._missing_files_labels(frame, missing_file, row)
            self._missing_button(frame, missing_file, row)

    def _missing_files_labels(
        self, frame: tk.Frame, missing_file: Missing, row: int
    ) -> None:
        missing_col = 0 if missing_file.missing_in_env else 1
        present_col = (missing_col + 1) % 2
        label = ttk.Label(frame, text=missing_file.file_name)
        label.grid(row=row, column=missing_col, padx=PAD, sticky=tk.W)
        label = ttk.Label(frame, text="missing", style="red-fg.TLabel")
        label.grid(row=row, column=present_col, padx=PAD, sticky=tk.W)

    def _missing_button(
        self, frame: tk.Frame, missing_file: Missing, row: int
    ) -> None:
        button = IconButton(frame, txt.COPY, "copy_docs")
        button.grid(row=row, column=2, padx=PAD, pady=PADB, sticky=tk.W)
        # TODO this should be a command
        button.widget.bind(
            "<Button-1>",
            partial(self._copy_missing_file, missing_file.file_name),
        )

    def _populate_mismatches(self) -> None:
        (self.missing, self.mismatches) = compare(
            self.project.source_dir, self.env_version.dir
        )
        if not self.mismatches:
            self._clear_frame(self.mismatch_frame.content)
            self._populate_no_mismatches()
            return
        self._populate_mismatched_files()

    def _populate_no_mismatches(self) -> None:
        label = ttk.Label(
            self.mismatch_frame.content, text="None", style="green-fg.TLabel"
        )
        label.grid(row=0, column=0, sticky=tk.E, padx=PAD, pady=PAD)

    def _populate_mismatched_files(self) -> None:
        self._clear_frame(self.mismatch_frame.content)
        self.diff_buttons = {}
        self.copy_to_env_buttons = {}
        self.copy_to_live_buttons = {}
        for index, item in enumerate(sorted(self.mismatches)):
            row = index + 2
            button = ttk.Radiobutton(
                self.mismatch_frame.content,
                text=item,
                value=item,
                variable=self.mismatch,
                command=self._rb_selected,
            )
            button.grid(row=row, column=0, sticky=tk.W, padx=PAD)

            diff_button = IconButton(
                self.mismatch_frame.content,
                txt.DIFF,
                "diff",
                partial(self._show_differences, item),
                True,
            )
            diff_button.grid(row=row, column=1, padx=PAD, pady=PADB)

            to_env_button = IconButton(
                self.mismatch_frame.content,
                "Copy to env",
                "copy_docs",
                partial(self._copy_live_to_env, item),
                True,
            )
            to_env_button.grid(row=row, column=2, padx=PAD, pady=PADB)

            to_live_button = IconButton(
                self.mismatch_frame.content,
                "Copy To live",
                "copy_docs",
                partial(self._copy_env_to_live, item),
                True,
            )
            to_live_button.grid(row=row, column=3, padx=PAD, pady=PADB)

            diff_button.enable(False)
            to_env_button.enable(False)
            to_live_button.enable(False)
            if item == self.mismatch.get():
                diff_button.enable(True)
                to_env_button.enable(True)
                to_live_button.enable(True)
            self.diff_buttons[item] = diff_button
            self.copy_to_env_buttons[item] = to_env_button
            self.copy_to_live_buttons[item] = to_live_button

    def _rb_selected(self, *args) -> None:
        for button in self.diff_buttons.values():
            button.enable(False)
        for button in self.copy_to_env_buttons.values():
            button.enable(False)
        for button in self.copy_to_live_buttons.values():
            button.enable(False)
        file = self.mismatch.get()
        self.diff_buttons[file].enable(True)
        self.copy_to_env_buttons[file].enable(True)
        self.copy_to_live_buttons[file].enable(True)
        self.button_frame.enable(True)

    def _show_differences(self, button_id: str, *args) -> None:
        print(button_id)
        file = self.mismatch.get()
        paths = [
            str(Path(self.env_version.dir, file)),
            str(Path(self.project.source_dir, file)),
        ]

        self.root.withdraw()
        # print(f"kdiff3 {paths[0]} {paths[1]} -o {paths[0]}")
        subprocess.run(["kdiff3", *paths, "-o", paths[0]])
        self.root.deiconify()
        (self.missing, self.mismatches) = compare(
            self.project.source_dir, self.env_version.dir
        )
        self._populate_mismatches()

    def _copy_env_to_live(self, file_name, *args) -> None:
        self._confirm_copy_file(file_name=file_name, direction="env_to_live")

    def _copy_live_to_env(self, file_name, *args) -> None:
        self._confirm_copy_file(file_name=file_name, direction="live_to_env")

    def _confirm_copy_file(self, file_name, direction: str):
        if direction == "env_to_live":
            source_str, destination_str = "env", "live"
            source = Path(self.env_version.dir, file_name)
            destination = Path(self.project.source_dir, file_name)
        elif direction == "live_to_env":
            source_str, destination_str = "live", "env"
            source = Path(self.project.source_dir, file_name)
            destination = Path(self.env_version.dir, file_name)

        response = messagebox.askyesno(
            "Copy file",
            (
                f"Are you sure you want to copy {file_name} "
                f"from {source_str} to {destination_str}?"
            ),
        )
        if response:
            shutil.copy2(source, destination)
            self._populate_mismatches()

    def _copy_missing_file(self, file_name, *args) -> None:
        source = Path(self.env_version.dir, file_name)
        destination = Path(self.project.source_dir, file_name)
        if not source.is_file():
            source = Path(self.project.source_dir, file_name)
            destination = Path(self.env_version.dir, file_name)

        if not self._confirm_copy(source, file_name):
            return

        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
            logger.info(
                "Copy directory",
                source=str(source),
                destination=str(destination),
            )
        else:
            logger.info(
                "Copy file", source=str(source), destination=str(destination)
            )
            shutil.copyfile(source, destination)
        (self.missing, self.mismatches) = compare(
            self.project.source_dir, self.env_version.dir
        )
        self._populate_missing_frame()

    def _confirm_copy(self, source: Path, file_name: str) -> bool:
        item = "directory" if source.is_dir() else "file"
        return messagebox.askokcancel(
            "", f"Copy this {item}? ({file_name})", parent=self.root
        )

    def _delete_orig(self, *args) -> None:
        dlg = messagebox.askyesno(
            "Delete orig", "Delete orig files?", parent=self.root
        )
        if dlg:
            for missing in self.missing:
                if missing.file_name.endswith(".orig"):
                    Path(self.project.source_dir, missing.file_name).unlink()
            self._populate_missing_frame()

    @staticmethod
    def _clear_frame(frame: tk.Frame) -> None:
        for widget in frame.winfo_children():
            widget.destroy()

    def _dismiss(self, *args) -> None:
        self.root.destroy()
