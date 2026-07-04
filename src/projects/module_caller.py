import sys

from psiutils.constants import Mode

from projects.forms.frm_build import BuildFrame
from projects.forms.frm_compare import CompareFrame
from projects.forms.frm_config import ConfigFrame
from projects.forms.frm_project_edit import ProjectEditFrame
from projects.forms.frm_project_versions import ProjectVersionsFrame
from projects.forms.frm_search import SearchFrame
from projects.project_server import ProjectServer

# from projects.github import upload

PROJECT_NAME = "script launcher"


class ModuleCaller:
    def __init__(self, root, module) -> None:
        modules = {
            "config": self._config,
            "project": self._project,
            "search": self._search,
            "build": self._build,
            "compare": self._compare,
            "versions": self._versions,
            # 'github': self._github,
        }
        self.project_server = ProjectServer()
        self.projects = self.project_server.projects

        self.invalid = False
        if module == "-h":
            for key in sorted(list(modules.keys()) + ["main"]):
                print(key)
            self.invalid = True
            return

        if module not in modules:
            if module != "main":
                print(f"*** Invalid function name: {module} ***")
            self.invalid = True
            return

        self.root = root
        modules[module]()
        self.root.destroy()
        return

    def _config(self) -> None:
        dlg = ConfigFrame(self)
        self.root.wait_window(dlg.root)

    def _compare(self) -> None:
        print(sys.argv)
        project_name = sys.argv[2]
        project = self.projects[project_name]
        project.env_versions = project.get_versions()
        dlg = CompareFrame(self, project, project.env_versions[sys.argv[3]])
        self.root.wait_window(dlg.root)

    def _versions(self) -> None:
        project_name = sys.argv[2]
        project = self.projects[project_name]
        project.env_versions = project.get_versions()
        dlg = ProjectVersionsFrame(self, project)
        self.root.wait_window(dlg.root)

    def _project(self) -> None:
        dlg = ProjectEditFrame(self, Mode.EDIT, self.projects[PROJECT_NAME])
        self.root.wait_window(dlg.root)

    def _build(self) -> None:
        project_name = sys.argv[2]
        project = self.projects[project_name]
        dlg = BuildFrame(self, project)
        self.root.wait_window(dlg.root)

    def _search(self) -> None:
        search_term = sys.argv[2] if len(sys.argv) > 2 else ""
        dlg = SearchFrame(self, search_term)
        self.root.wait_window(dlg.root)

    # def _github(self):
    #     upload(self.projects["sudoku"])
