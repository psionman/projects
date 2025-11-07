
"""MainFrame for project management."""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess

from psiutils.constants import PAD, Status
from psiutils.buttons import ButtonFrame, IconButton
from psiutils.treeview import sort_treeview
from psiutils.menus import Menu, MenuItem
from psiutils.utilities import window_resize, geometry

from projects.project_server import ProjectServer
from projects.config import read_config
from projects.build import UV_PUBLISH_TOKEN
from projects.text import Text

from projects.main_menu import MainMenu
from projects.forms.frm_project_edit import ProjectEditFrame
from projects.forms.frm_project_versions import ProjectVersionsFrame
from projects.forms.frm_build import BuildFrame
from projects.forms.frm_search import SearchFrame

txt = Text()

FRAME_TITLE = 'Project management'

TREE_COLUMNS = (
    ('name', 'Project', 50),
    ('script', 'Script', 1),
    ('main', 'Source dir', 400),
)


class MainFrame():
    """
    MainFrame for project management.

    Explanation:
        Represents the main frame for comparing packages.
        It provides functionality to interact with projects,
        display project information, and perform various actions
        like building projects or editing project details.
    """
    def __init__(self, parent):
        self.root = parent.root
        self.parent = parent
        self.config = read_config()

        self.project_server = ProjectServer()
        self.projects = self.project_server.projects
        self.project = None

        self.tree = None
        self.build_button = None
        self.compare_button = None
        self.refresh_button = None
        self.script_button = None
        self.run_script_button = None
        self.windows_build_button = None

        self.build_menu_item = None
        self.compare_menu_item = None
        self.refresh_menu_item = None
        self.edit_script_menu_item = None
        self.run_script_menu_item = None
        self.windows_build_menu_item = None

        self._show()

    def _show(self):
        root = self.root
        root.geometry(geometry(self.config, __file__))
        root.title(FRAME_TITLE)
        root.bind('<Control-x>', self._dismiss)
        root.bind('<Configure>',
                  lambda event, arg=None: window_resize(self, __file__))

        main_menu = MainMenu(self)
        main_menu.create()

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        main_frame = self._main_frame(root)
        main_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=PAD, pady=PAD)

        self.button_frame = self._button_frame(root)
        self.button_frame.grid(row=0, column=1, rowspan=9,
                               sticky=tk.NS, padx=PAD, pady=PAD)

        sizegrip = ttk.Sizegrip(root)
        sizegrip.grid(column=1, sticky=tk.SE)

        self.context_menu = self._context_menu()

    def _main_frame(self, master: tk.Frame) -> ttk.Frame:
        frame = ttk.Frame(master)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.tree = self._get_tree(frame)
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        self._populate_tree()

        return frame

    def _get_tree(self, master: tk.Frame) -> ttk.Treeview:
        """Return  a tree widget for events."""
        tree = ttk.Treeview(
            master,
            selectmode='browse',
            height=15,
            show='headings',
            )
        tree.bind('<<TreeviewSelect>>', self._tree_clicked)
        tree.bind('<Button-3>', self._show_context_menu)

        col_list = tuple(col[0] for col in TREE_COLUMNS)
        tree['columns'] = col_list
        for col in TREE_COLUMNS:
            (col_key, col_text, col_width) = (col[0], col[1], col[2])
            tree.heading(col_key, text=col_text,
                         command=lambda c=col_key:
                         sort_treeview(tree, c, False))
            tree.column(col_key, width=col_width, anchor=tk.W)
        return tree

    def _populate_tree(self) -> None:
        # pylint: disable=no-member)
        self.tree.delete(*self.tree.get_children())
        projects = {key: self.projects[key]
                    for key in sorted(self.projects.keys())}
        for project in projects.values():
            values = (
                project.name,
                project.script.replace(
                    f'{self.config.script_directory}/', ''),
                project.source_dir_short,)
            item = self.tree.insert('', 'end', values=values)

            # pylint: disable=no-member
            if self.project and project.name == self.project.name:
                self.tree.selection_set(item)
            elif self.config.last_project == project.name:
                self.tree.selection_set(item)

    def _tree_clicked(self, *args) -> None:
        if not (values := self.tree.item(self.tree.selection())['values']):
            return

        self.project = self.projects[values[0]]
        self.button_frame.enable(True)
        self.context_menu.enable(True)

        self.script_button.disable()
        self.run_script_button.disable()
        self.edit_script_menu_item.disable()
        self.run_script_menu_item.disable()
        if self.project.script:
            self.script_button.enable()
            self.run_script_button.enable()
            self.edit_script_menu_item.enable()
            self.run_script_menu_item.enable()

        if not self.project.pypi:
            self._disable_non_pypi_buttons()

        self.windows_build_button.disable()
        self.windows_build_menu_item.disable()
        if self.project.build_for_windows:
            self.windows_build_button.enable()
            self.windows_build_menu_item.enable()

        self.config.update('last_project', values[0])
        self.config.save()

    def _disable_non_pypi_buttons(self) -> None:
        self.build_button.disable()
        self.compare_button.disable()
        self.refresh_button.disable()
        self.build_menu_item.disable()
        self.compare_menu_item.disable()
        self.refresh_menu_item.disable()

    def _show_context_menu(self, event) -> None:
        self.context_menu.tk_popup(event.x_root, event.y_root)
        selected_item = self.tree.identify_row(event.y)
        self.tree.selection_set(selected_item)

    def _button_frame(self, master: tk.Frame) -> tk.Frame:
        # pylint: disable=no-member)
        frame = ButtonFrame(master, tk.VERTICAL)
        self.build_button = frame.icon_button(
            'build', self._build_project, True)
        self.compare_button = frame.icon_button(
            'compare', self._compare_project, True)
        self.refresh_button = frame.icon_button(
            'refresh', self._refresh_project, True)
        konsole_button = IconButton(
            frame, txt.KONSOLE, 'gear', self._konsole)
        self.script_button = IconButton(
            frame, txt.EDIT_SCRIPT, 'script', self._edit_script)
        self.run_script_button = IconButton(
            frame, txt.RUN_SCRIPT, 'start', self._run_script)
        self.windows_build_button = IconButton(
            frame, txt.BUILD_FOR_WINDOWS, 'windows', self._build_for_windows)
        frame.buttons = [
            # frame.icon_button('new', self._new_project),
            frame.icon_button('edit', self._edit_project, True),
            self.build_button,
            frame.icon_button('update', self._update_pyproject),
            frame.icon_button('code', self._open_code, True),
            konsole_button,
            self.script_button,
            self.run_script_button,
            self.compare_button,
            self.refresh_button,
            self.windows_build_button,
            # frame.icon_button('search', self._search_for_content, True),
            frame.icon_button('delete', self._delete_project, True),
            frame.icon_button('close', self._dismiss),
        ]
        self.script_button.disable()
        self.run_script_button.disable()
        self.windows_build_button.disable()
        frame.enable(False)
        return frame

    def _context_menu(self) -> tk.Menu:
        # pylint: disable=no-member)
        self.build_menu_item = MenuItem(
            txt.BUILD, self._build_project, dimmable=True)
        self.compare_menu_item = MenuItem(
            txt.COMPARE, self._compare_project, dimmable=True)
        self.refresh_menu_item = MenuItem(
            txt.REFRESH, self._refresh_project, dimmable=True)
        self.edit_script_menu_item = MenuItem(
            txt.EDIT_SCRIPT, self._edit_script, dimmable=True)
        self.run_script_menu_item = MenuItem(
            txt.RUN_SCRIPT, self._run_script, dimmable=True)
        self.windows_build_menu_item = MenuItem(
            txt.BUILD_FOR_WINDOWS, self._build_for_windows, dimmable=True)
        menu_items = [
            # MenuItem(txt.NEW, self._new_project, dimmable=False),
            MenuItem(txt.EDIT, self._edit_project, dimmable=True),
            self.build_menu_item,
            MenuItem(txt.UPDATE, self._update_pyproject, dimmable=True),
            MenuItem(txt.CODE, self._open_code, dimmable=True),
            MenuItem(txt.KONSOLE, self._konsole, dimmable=True),
            self.edit_script_menu_item,
            self.run_script_menu_item,
            self.compare_menu_item,
            self.refresh_menu_item,
            self.windows_build_menu_item,
            MenuItem(txt.DELETE, self._delete_project, dimmable=True),
        ]
        context_menu = Menu(self.root, menu_items)
        context_menu.enable(False)
        return context_menu

    def _new_project(self, *args) -> None:
        # pylint: disable=no-member)
        dlg = ProjectEditFrame(self, txt.NEW)
        self.root.wait_window(dlg.root)
        self.update_projects(dlg)

    def _edit_project(self, *args) -> None:
        # pylint: disable=no-member)
        dlg = ProjectEditFrame(self, txt.EDIT, self.project)
        self.root.wait_window(dlg.root)
        self.update_projects(dlg)

    def _compare_project(self, refresh: bool = False) -> None:
        # pylint: disable=no-member)
        dlg = ProjectVersionsFrame(self, txt.EDIT, self.project, refresh)
        self.root.wait_window(dlg.root)
        self.update_projects(dlg)

    def _refresh_project(self, *args) -> None:
        self._compare_project(True)

    def _delete_project(self, *args) -> None:
        dlg = messagebox.askyesno(
            'Delete project',
            f'Are you sure you want to delete {self.project.name}?',
            parent=self.root,
        )
        if dlg is False:
            return
        del self.projects[self.project.name]
        self._save_projects()

    def update_projects(self, dlg: ttk.Frame) -> None:
        if dlg.status != Status.UPDATED:
            return
        self.projects[dlg.project.name] = dlg.project
        self._save_projects()

    def _save_projects(self) -> None:
        result = self.project_server.save_projects(self.projects)
        if result == Status.ERROR:
            messagebox.showerror(
                'Save',
                'Save failed',
                parent=self.root
            )
            return
        self._populate_tree()

    def _build_project(self, *args) -> None:
        if not UV_PUBLISH_TOKEN:
            messagebox.showerror('', 'UV_PUBLISH_TOKEN not set.')
            return

        dlg = BuildFrame(self, self.project)
        self.root.wait_window(dlg.root)

    def _update_pyproject(self, *args) -> None:
        code = self.project.update_pyproject()
        if code == 0:
            messagebox.showinfo('', 'Project updated')
        else:
            messagebox.showerror(
                '', f'Project not updated - code: {code}')

    def _open_code(self, *args) -> None:
        try:
            subprocess.call(['codium', '-n', self.project.base_dir])
        except FileNotFoundError:
            messagebox.showerror('', "codium not found.")

    def _konsole(self, *args) -> None:
        return subprocess.Popen(
                ['konsole', '--workdir', self.project.base_dir]
            )

    def _edit_script(self, *args) -> None:
        return subprocess.Popen(
                ['kate', self.project.script]
            )

    def _run_script(self, *args) -> None:
        return subprocess.Popen(
                [self.project.script]
            )

    def _build_for_windows(self, *args) -> None:
        # env_version = self.project.env_versions[self.project.name]
        # ic (env_version.python_version)
        return subprocess.Popen(
                ['windows-converter', 'project', self.project.name]
            )

    def _search_for_content(self, * args):
        dlg = SearchFrame(self)
        self.root.wait_window(dlg.root)

    def _dismiss(self, *args) -> None:
        self.root.destroy()
