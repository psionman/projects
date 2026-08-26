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


class ModuleCaller:
    def __init__(self, root, parsed_args) -> None:
        self.args = parsed_args
        self.modules = {
            "config": self._config,
            "project": self._project,
            "search": self._search,
            "build": self._build,
            "compare": self._compare,
            "versions": self._versions,
            "notes": self._notes,
        }

        self._select_module()

        self.root = root
        self.modules[self.args.module]()
        self.root.destroy()
        return

    def _select_module(self) -> None:
        self.project_name = self.args.project
        if self.args.module == "list":
            self._list()
            return

        if self.args.module not in self.modules:
            if self.args.module != "main":
                print(f"*** Invalid function name: {self.args.module} ***")
            self._list()
            return

    def _list(self) -> None:
        for key in sorted(list(self.modules.keys()) + ["main", "list"]):
            print(key)

    def _config(self) -> None:
        dlg = ConfigFrame(self)
        self.root.wait_window(dlg.root)

    def _compare(self) -> None:
        project_name = self.project_name
        project = data_store.projects[project_name]
        project.env_versions = get_versions(project)
        print(f"Comparing...{self.args.project!r} vs {self.args.secondary!r}")
        dlg = CompareFrame(
            self, project, project.env_versions[self.args.secondary]
        )
        self.root.wait_window(dlg.root)

    def _versions(self) -> None:
        project_name = self.args.project
        project = data_store.projects[project_name]
        project.env_versions = get_versions(project)
        dlg = ProjectVersionsFrame(self, project)
        self.root.wait_window(dlg.root)

    def _project(self) -> None:
        project_name = self.args.project
        print(f"Editing project: {project_name}")
        dlg = ProjectEditFrame(
            self, Mode.EDIT, data_store.projects[project_name]
        )
        self.root.wait_window(dlg.root)

    def _notes(self) -> None:
        dlg = NotesFrame(self)
        self.root.wait_window(dlg.root)

    def _build(self) -> None:
        project_name = self.args.project
        project = data_store.projects[project_name]
        print(f"Building...{project_name!r}")
        dlg = BuildFrame(self, project, False)
        self.root.wait_window(dlg.root)

    def _search(self) -> None:
        search_term = (
            self.args.search_term if len(self.args.search_term) > 0 else ""
        )
        dlg = SearchFrame(self, search_term)
        self.root.wait_window(dlg.root)
