import sys

from psiutils.constants import Mode

from projects.data_store import get_versions
from projects.data_store import store as data_store
from projects.forms.frm_build import BuildFrame
from projects.forms.frm_compare import CompareFrame
from projects.forms.frm_config import ConfigFrame
from projects.forms.frm_notes import NotesFrame
from projects.forms.frm_project_edit import ProjectEditFrame
from projects.forms.frm_project_versions import ProjectVersionsFrame
from projects.forms.frm_search import SearchFrame

# from projects.github import upload


class ModuleCaller:
    def __init__(self, root, module) -> None:
        modules = {
            "config": self._config,
            "project": self._project,
            "search": self._search,
            "build": self._build,
            "compare": self._compare,
            "versions": self._versions,
            "notes": self._notes,
            # 'github': self._github,
        }

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
        project_name = sys.argv[2]
        project = data_store.projects[project_name]
        project.env_versions = get_versions(project)
        dlg = CompareFrame(self, project, project.env_versions[sys.argv[3]])
        self.root.wait_window(dlg.root)

    def _versions(self) -> None:
        project_name = sys.argv[2]
        project = data_store.projects[project_name]
        project.env_versions = get_versions(project)
        dlg = ProjectVersionsFrame(self, project)
        self.root.wait_window(dlg.root)

    def _project(self) -> None:
        project_name = sys.argv[2]
        print(f"Editing project: {project_name}")
        dlg = ProjectEditFrame(
            self, Mode.EDIT, data_store.projects[project_name]
        )
        self.root.wait_window(dlg.root)

    def _notes(self) -> None:
        dlg = NotesFrame(self)
        self.root.wait_window(dlg.root)

    def _build(self) -> None:
        project_name = sys.argv[2]
        project = data_store.projects[project_name]
        dlg = BuildFrame(self, project)
        self.root.wait_window(dlg.root)

    def _search(self) -> None:
        search_term = sys.argv[2] if len(sys.argv) > 2 else ""
        dlg = SearchFrame(self, search_term)
        self.root.wait_window(dlg.root)
