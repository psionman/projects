import sys

from psiutils.constants import Mode

from projects.project_server import ProjectServer
from projects.forms.frm_config import ConfigFrame
from projects.forms.frm_project_edit import ProjectEditFrame
from projects.forms.frm_build import BuildFrame
from projects.forms.frm_search import SearchFrame

# from projects.github import upload


class ModuleCaller():
    def __init__(self, root, module) -> None:
        modules = {
            'config': self._config,
            'project': self._project,
            'search': self._search,
            'build': self._build,
            # 'github': self._github,
            }
        self.projects = ProjectServer().projects

        self.invalid = False
        if module == '-h':
            for key in sorted(list(modules.keys())+['main']):
                print(key)
            self.invalid = True
            return

        if module not in modules:
            if module != 'main':
                print(f'*** Invalid function name: {module} ***')
            self.invalid = True
            return

        self.root = root
        modules[module]()
        self.root.destroy()
        return

    def _config(self) -> None:
        dlg = ConfigFrame(self)
        self.root.wait_window(dlg.root)

    def _project(self) -> None:
        self.project_server = ProjectServer()
        dlg = ProjectEditFrame(self, Mode.EDIT, self.projects['psiutils'])
        self.root.wait_window(dlg.root)

    def _build(self) -> None:
        dlg = BuildFrame(self, self.projects['bfgbidding'])
        self.root.wait_window(dlg.root)

    def _search(self) -> None:
        search_term = sys.argv[2] if len(sys.argv) > 2 else ''
        dlg = SearchFrame(self, search_term)
        self.root.wait_window(dlg.root)

    def _github(self):
        upload(self.projects['sudoku'])
