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
            "main": (None, "Call main function"),
            "list": (None, "List module definitions"),
            "config": (self._config, None),
            "edit": (self._edit, "Param: project name"),
            "search": (self._search, "Param: search term or ''"),
            "build": (self._build, "Param: project name"),
            "compare": (
                self._compare,
                "Params: project name, secondary project name",
            ),
            "versions": (self._versions, "Param: project name"),
            "notes": (self._notes, None),
        }

        if self._select_module():
            self.root = root
            self.root.after(100, self._run_module)
        else:
            root.destroy()

    def _run_module(self) -> None:
        try:
            self.modules[self.args.module][0]()
        except ValueError as e:
            print(f"Error running module: {e}")
        finally:
            self.root.destroy()

    def _select_module(self) -> bool:
        """Return True if a valid, runnable module was selected."""
        module = self.args.module
        if module in ("list", None) or module not in self.modules:
            if module not in ("list", "main", None):
                print(f"*** Invalid function name: {module} ***")
            self._list()
            return False
        return True

    def _list(self) -> None:
        keys = sorted(self.modules.keys())
        padding = max(len(key) for key in keys)
        for key in keys:
            _, help_text = self.modules[key]
            if help_text:
                print(f"{key:.<{padding}} {help_text}")
            else:
                print(key)

    def _require(self, attr: str, message: str) -> str:
        """Return the named CLI arg, or raise ValueError if missing."""
        value = getattr(self.args, attr)
        if not value:
            raise ValueError(message)
        return value

    def _get_project(self, project_name: str):
        try:
            return data_store.projects[project_name]
        except KeyError:
            raise ValueError(f"Unknown project: {project_name!r}") from None

    def _config(self) -> None:
        dlg = ConfigFrame(self)
        self.root.wait_window(dlg.root)

    def _compare(self) -> None:
        project_name = self._require("project", "No project name provided")
        secondary_name = self._require(
            "secondary", "No secondary name provided"
        )

        project = self._get_project(project_name)
        project.env_versions = get_versions(project)

        try:
            env_version = project.env_versions[secondary_name]
        except KeyError:
            raise ValueError(
                f"Unknown environment version: {secondary_name!r}. "
                f"Available: {list(project.env_versions.keys())}"
            ) from None

        print(f"Comparing...{project_name!r} vs {secondary_name!r}")
        dlg = CompareFrame(self, project, env_version)
        self.root.wait_window(dlg.root)

    def _versions(self) -> None:
        project_name = self._require("project", "No project name provided")
        project = self._get_project(project_name)
        print(f"Getting versions for project: {project_name}")
        project.env_versions = get_versions(project)
        dlg = ProjectVersionsFrame(self, project)
        self.root.wait_window(dlg.root)

    def _edit(self) -> None:
        project_name = self._require("project", "No project name provided")
        project = self._get_project(project_name)
        print(f"Editing project: {project_name}")
        dlg = ProjectEditFrame(self, Mode.EDIT, project)
        self.root.wait_window(dlg.root)

    def _notes(self) -> None:
        print("Editing notes")
        dlg = NotesFrame(self)
        self.root.wait_window(dlg.root)

    def _build(self) -> None:
        project_name = self._require("project", "No project name provided")
        project = self._get_project(project_name)
        print(f"Building...{project_name!r}")
        dlg = BuildFrame(self, project, False)
        self.root.wait_window(dlg.root)

    def _search(self) -> None:
        search_term = self.args.project if self.args.project else ""
        print(f"Searching...{search_term!r}")
        dlg = SearchFrame(self, search_term)
        self.root.wait_window(dlg.root)
