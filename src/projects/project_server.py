"""Project server for package application."""

from pathlib import Path

import projects.projects_io as io
from projects.config import config
from projects.constants import CACHED_ENVS_FILE, USER_DATA_DIR
from projects.project import Project


class ProjectServer:
    """Handle projects."""

    def __init__(self) -> None:
        self.project_file = Path(USER_DATA_DIR, config.project_file)
        self.projects = self._get_projects()

    def _get_projects(self) -> dict[str, Project]:
        project_dict = {}
        projects_raw = io.read_json_file(self.project_file)
        cached_envs = self._get_cached_envs()
        for key, item in projects_raw.items():
            item["name"] = key
            item["cached_envs"] = cached_envs.get(key, {})

            project = Project()
            project.deserialize(item)
            project_dict[key] = project
        return project_dict

    def save_projects(self, projects: dict[str, Project] = None) -> int:
        if not projects:
            projects = self.projects
        self.projects = projects
        output = {
            name: project.serialize() for name, project in projects.items()
        }

        cached_envs = {}
        for project in self.projects.values():
            project.save_project_colours()
            cached_envs[project.name] = {
                key: item for key, item in project.cached_envs.items()
            }
        if cached_envs:
            self._save_cached_envs(cached_envs)
        return io.update_json_file(self.project_file, output)

    def _get_cached_envs(self) -> dict:
        """Get the cached environments for a project."""
        cached_envs_file = Path(USER_DATA_DIR, CACHED_ENVS_FILE)
        try:
            cached_envs = io.read_json_file(cached_envs_file)
            return cached_envs
        except FileNotFoundError:
            return {}

    def _save_cached_envs(self, cached_envs: dict) -> None:
        output = {}
        for project_name, env in cached_envs.items():
            project_envs = {}
            for key, item in env.items():
                project_envs[key] = item.serialize()
            if project_envs:
                output[project_name] = project_envs
        """Save the cached environments for a project."""
        cached_envs_file = Path(USER_DATA_DIR, CACHED_ENVS_FILE)
        io.update_json_file(cached_envs_file, output)
