"""Project server for package application."""

from pathlib import Path

import json5

import projects.projects_io as io
from projects.config import config
from projects.constants import HOME_DIR, USER_DATA_DIR
from projects.env_version import EnvironmentVersion
from projects.project import DEFAULT_COLOURS, Project


class ProjectServer:
    """Handle projects."""

    def __init__(self) -> None:
        self.project_file = Path(USER_DATA_DIR, config.project_file)
        self.projects = self._get_projects()

    def _get_projects(self) -> dict[str, Project]:
        project_dict = {}
        projects_raw = io.read_json_file(self.project_file)
        for key, item in projects_raw.items():
            project = Project()
            project.name = key
            project_dict[key] = project

            project.source_dir = item["source_dir"].replace("~", HOME_DIR)
            project.base_dir = item["base_dir"].replace("~", HOME_DIR)
            project.pypi = item["pypi"]
            if "build_for_windows" not in item:
                item["build_for_windows"] = False
            project.build_for_windows = item["build_for_windows"]
            if "repository" in item:
                project.repository_name = item["repository"]
            project.cached_envs = {
                key: EnvironmentVersion(data)
                for key, data in item["cached_envs"].items()
            }
            if "script" in item:
                project.script = item["script"]
            if "desktop_file" in item:
                project.desktop_file = item["desktop_file"]
            project.get_project_data()
            self.get_project_colours(project)
        return project_dict

    def save_projects(self, projects: dict[str, Project] = None) -> int:
        if not projects:
            projects = self.projects
        self.projects = projects
        output = {
            name: project.serialize() for name, project in projects.items()
        }
        for project in self.projects.values():
            self.save_project_colours(project)
        return io.update_json_file(self.project_file, output)

    def get_project_colours(self, project: Project) -> None:
        """Get the colours for a project."""

        settings_file = Path(
            Path(project.source_dir).parent.parent, ".vscode", "settings.json"
        )
        try:
            with open(settings_file, encoding="utf-8") as f:
                settings = json5.load(f)
        except FileNotFoundError:
            return

        if "workbench.colorCustomizations" in settings:
            colour_customizations = settings["workbench.colorCustomizations"]
            for key, value in colour_customizations.items():
                if key in project.workbench_colours:
                    project.workbench_colours[key] = value

    def save_project_colours(self, project: Project) -> None:
        """Save the colours for a project."""
        settings_file = Path(
            Path(project.source_dir).parent.parent, ".vscode", "settings.json"
        )
        try:
            with open(settings_file, encoding="utf-8") as f:
                settings = json5.load(f)
        except FileNotFoundError:
            return
        if project.workbench_colours != DEFAULT_COLOURS:
            settings["workbench.colorCustomizations"] = (
                project.workbench_colours
            )
            with open(settings_file, "w", encoding="utf-8") as f:
                json5.dump(settings, f, indent=2)
            #     print(project.name)
            # print(settings[
            #     "workbench.colorCustomizations"])
