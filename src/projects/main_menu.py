import tkinter as tk
from tkinter import messagebox

from psiutils.menus import Menu, MenuItem
from psiutils.constants import Mode, Status

from projects.constants import AUTHOR, APP_TITLE
from projects._version import __version__
from projects.text import Text

from projects.forms.frm_config import ConfigFrame
from projects.forms.frm_project_edit import ProjectEditFrame
from projects.forms.frm_search import SearchFrame


txt = Text()
SPACES = ' '*20


class MainMenu():
    def __init__(self, parent) -> None:
        self.parent = parent
        self.root = parent.root
        self.projects = parent.projects
        self.project_server = parent.project_server
        self.status = Status.NULL

    def create(self) -> None:
        menubar = tk.Menu()
        self.root['menu'] = menubar

        # File menu
        file_menu = Menu(menubar, self._file_menu_items())
        menubar.add_cascade(menu=file_menu, label='File')

        # File menu
        project_menu = Menu(menubar, self._project_menu_items())
        menubar.add_cascade(menu=project_menu, label='Projects')

        # Help menu
        help_menu = Menu(menubar, self._help_menu_items())
        menubar.add_cascade(menu=help_menu, label='Help')

    def _file_menu_items(self) -> list:
        # pylint: disable=no-member)
        return [
            MenuItem(f'{txt.CONFIG}{txt.ELLIPSIS}', self._config_frame),
            MenuItem(txt.QUIT, self._dismiss),
        ]

    def _project_menu_items(self) -> list:
        # pylint: disable=no-member)
        return [
            MenuItem(f'{txt.NEW}{txt.ELLIPSIS}', self._new_project),
            MenuItem(f'{txt.SEARCH}{txt.ELLIPSIS}', self._search_for_content),
        ]

    def _help_menu_items(self) -> list:
        # pylint: disable=no-member)
        return [
            MenuItem(f'About{txt.ELLIPSIS}', self._show_about),
        ]

    def _config_frame(self) -> None:
        """Display the config frame."""
        dlg = ConfigFrame(self)
        self.root.wait_window(dlg.root)

    def _show_about(self) -> None:
        about = (f'{APP_TITLE}\n'
                 f'Version: {__version__}\n'
                 f'Author: {AUTHOR} {SPACES}')
        messagebox.showinfo(title=f'About {APP_TITLE}', message=about)

    def _new_project(self, *args) -> None:
        # pylint: disable=no-member)
        dlg = ProjectEditFrame(self, Mode.NEW)
        self.root.wait_window(dlg.root)
        self.parent.update_projects(dlg)
        self.status = dlg.status

    def _search_for_content(self, * args):
        dlg = SearchFrame(self)
        self.root.wait_window(dlg.root)

    def _dismiss(self) -> None:
        """Quit the application."""
        self.root.destroy()
