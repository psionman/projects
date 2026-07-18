# forms.frm_notes.py

"""NotesFrame for Projects."""

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from psiutils.buttons import ButtonFrame
from psiutils.constants import PAD
from psiutils.utilities import window_resize
from psiutils.widgets import ScrollingCanvas

from projects.config import config
from projects.constants import APP_TITLE, DEFAULT_GEOMETRY
from projects.data_store import store as data_store
from projects.text import Text

txt = Text()

FRAME_TITLE = f"{APP_TITLE} - Notes"


class NotesFrame:
    def __init__(self, parent: tk.Frame) -> None:
        self.root = tk.Toplevel(parent.root)
        self.main_frame = None
        self.notes_area = None
        self.save_button = None
        self.delete_button = None
        self.notes = data_store.notes.copy()

        # tk variables
        self.note_id = tk.StringVar()

        self.show()
        self._populate_selection_frame()

    def show(self) -> None:
        root = self.root
        try:
            root.geometry(config.geometry[Path(__file__).stem])
        except KeyError:
            root.geometry(DEFAULT_GEOMETRY)
        root.title(FRAME_TITLE)

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        row = 0
        self.main_frame = self._main_frame(root)
        self.main_frame.grid(
            row=row, column=0, sticky=tk.NSEW, padx=PAD, pady=PAD
        )

        self.button_frame = self._button_frame(root)
        self.button_frame.grid(
            row=row, column=1, rowspan=9, sticky=tk.NS, padx=PAD, pady=PAD
        )

        sizegrip = ttk.Sizegrip(root)
        sizegrip.grid(column=1, sticky=tk.SE)

        self.root.update_idletasks()

        if config.horizontal_sashes:
            for index, sash in enumerate(config.horizontal_sashes):
                self.main_frame.sash_place(index, 0, sash[1])

        root.bind("<Control-x>", self._dismiss)
        root.bind(
            "<Configure>", lambda e: window_resize(root, __file__, config)
        )

    def _main_frame(self, master: tk.Frame) -> tk.PanedWindow:
        frame = tk.PanedWindow(master, orient=tk.VERTICAL)
        frame.columnconfigure(0, weight=1)
        self.notes_area = None
        self.selection_frame = self._selection_frame(frame)
        frame.add(self.selection_frame)

        self.notes_frame = self._notes_frame(frame)
        frame.add(self.notes_frame)

        return frame

    def _selection_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ScrollingCanvas(
            master,
            relief=tk.SUNKEN,
            borderwidth=2,
        )
        frame.columnconfigure(0, weight=1)

        return frame

    def _notes_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ScrollingCanvas(
            master,
            relief=tk.SUNKEN,
            borderwidth=2,
        )
        frame.canvas.rowconfigure(0, weight=1)
        frame.canvas.columnconfigure(0, weight=1)

        self.notes_area = tk.Text(frame.canvas)
        self.notes_area.grid(row=0, column=0, sticky=tk.NSEW)
        self.notes_area.bind("<KeyRelease>", self._check_value_changed)

        return frame

    def _button_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ButtonFrame(master, tk.VERTICAL)
        frame.buttons = [
            frame.icon_button("new", self._new_note),
            frame.icon_button("save", self._save_notes, True, tag="save"),
            frame.icon_button("delete", self._delete_note, True, tag="delete"),
            frame.icon_button("exit", self._dismiss),
        ]
        self.save_button = frame.get_button("save")
        self.delete_button = frame.get_button("delete")
        frame.enable(False)
        return frame

    def _rb_selected(self, *args) -> None:
        notes = self.notes[self.note_id.get()]
        self.notes_area.delete("0.0", tk.END)
        self.notes_area.insert("0.0", notes)
        self.delete_button.enable(True)

    def _populate_selection_frame(self) -> None:
        for widget in self.selection_frame.content.winfo_children():
            widget.destroy()

        for row, note_id in enumerate(self.notes.keys()):
            button = ttk.Radiobutton(
                self.selection_frame.content,
                text=note_id,
                value=note_id,
                variable=self.note_id,
                command=self._rb_selected,
            )
            button.grid(row=row, column=0, sticky=tk.W, padx=PAD)

    def _populate_notes_frame(self) -> None:
        pass

    def _new_note(self, *args) -> None:
        title = tk.simpledialog.askstring("New Note", "Enter note title:")
        if title:
            self.notes_area.delete("0.0", tk.END)
            self.notes[title] = ""
            self._populate_selection_frame()
            self.note_id.set(title)
            self.delete_button.enable(True)
            self.notes_area.focus_set()

    def _save_notes(self, *args) -> None:
        data_store.notes = self.notes.copy()
        data_store.save_notes()
        self.save_button.enable(False)

    def _delete_note(self, *args) -> None:
        dlg = tk.messagebox.askyesno(
            "Delete Note",
            "Are you sure you want to delete this note?",
            parent=self.root,
        )
        if not dlg:
            return
        self.notes.pop(self.note_id.get())
        self.notes_area.delete("0.0", tk.END)
        self.note_id.set("")
        self._populate_selection_frame()
        self._check_value_changed()

    def _check_value_changed(self, *args) -> None:
        if self.note_id.get():
            self.notes[self.note_id.get()] = self.notes_area.get(
                "0.0", tk.END
            )[:-1]
        self.save_button.enable(False)
        if self.notes != data_store.notes:
            self.save_button.enable(True)

    def _save_sashes(self) -> None:
        horizontal_sashes = [
            self.main_frame.sash_coord(index)
            for index in range(len(config.horizontal_sashes))
        ]
        config.update("horizontal_sashes", horizontal_sashes)
        config.save()

    def _dismiss(self, *args) -> None:
        self._save_sashes()
        self.root.destroy()
