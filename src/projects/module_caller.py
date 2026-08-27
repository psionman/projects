from psiutils.constants import Mode
from psiutils.module_caller import ModuleCaller as ModuleCallerBase

from projects.data_store import get_versions
from projects.data_store import store as data_store
from projects.forms.frm_build import BuildFrame
from projects.forms.frm_compare import CompareFrame
from projects.forms.frm_config import ConfigFrame
from projects.forms.frm_notes import NotesFrame
from projects.forms.frm_project_edit import ProjectEditFrame
from projects.forms.frm_project_versions import ProjectVersionsFrame
from projects.forms.frm_search import SearchFrame


class ModuleCaller(ModuleCallerBase):
    def __init__(self, root, parsed_args: dict) -> None:
        self.modules = {
            "config": (self._config, None),
            "edit": (self._edit, "Edit a project. Param: project name"),
            "search": (
                self._search,
                "Search for usage of a string. Param: search term or ''",
            ),
            "build": (self._build, "Build the project. Param: project name"),
            "usage": (
                self._usage,
                "Projects using the package, Param: project name",
            ),
            "compare": (
                self._compare,
                "Compare module between Package and usage. "
                "Params: project name, secondary project name",
            ),
            # "versions": (self._versions, "Param: project name"),
            "notes": (self._notes, None),
        }
        super().__init__(root, parsed_args)

    def _get_project(self, project_name: str):
        try:
            return data_store.projects[project_name]
        except KeyError:
            raise ValueError(f"Unknown project: {project_name!r}") from None

    def _config(self) -> None:
        dlg = ConfigFrame(self)
        self.root.wait_window(dlg.root)

    def _usage(self) -> None:
        project_name = self._require("project", "No project name provided")
        project = self._get_project(project_name)
        print(f"Usage for...{project_name!r}")

        dlg = ProjectVersionsFrame(self, project, False)
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

    # def _versions(self) -> None:
    #     project_name = self._require("project", "No project name provided")
    #     project = self._get_project(project_name)
    #     print(f"Getting versions for project: {project_name}")
    #     project.env_versions = get_versions(project)
    #     dlg = ProjectVersionsFrame(self, project)
    #     self.root.wait_window(dlg.root)

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
