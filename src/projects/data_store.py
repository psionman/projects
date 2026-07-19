"""Central store for all Data instances.

Import `store` from this module anywhere it's needed —
it's a singleton, so every importer shares the same instance.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

import projects.projects_io as io
from projects.config import config
from projects.constants import CACHED_ENVS_FILE, NOTES_FILE, USER_DATA_DIR
from projects.env_version import EnvironmentVersion
from projects.project import Project

Listener = Callable[[], None]

PROJECT_FILE = Path(USER_DATA_DIR, config.project_file)


class ProjectStore:
    """Single source of truth for all projects in the app."""

    def __init__(self) -> None:
        self._projects: dict[str, Project] = self._get_projects()
        self.notes: dict[str, str] = self._get_notes()
        self._listeners: list[Listener] = []

    # -- data access -----------------------------------------------
    @property
    def projects(self) -> dict[str, Project]:
        """Read-only view; mutate via add/remove/update below."""
        return dict(self._projects)

    @projects.setter
    def projects(self, projects: dict[str, Project]) -> None:
        self._projects = projects
        self._notify()

    def get(self, name: str) -> Project | None:
        return self._projects.get(name)

    def add(self, project: Project) -> None:
        self._projects[project.name] = project
        self._notify()

    def remove(self, name: str) -> None:
        self._projects.pop(name, None)
        self._notify()

    def update(self, project: Project) -> None:
        self._projects[project.name] = project
        self._notify()

    def load(self, projects: dict[str, Project]) -> None:
        """Bulk-replace, e.g. after reading from disk on startup."""
        self._projects = dict(projects)
        self._notify()

    # -- observer pattern for UI refresh -----------------------------
    def subscribe(self, listener: Listener) -> None:
        self._listeners.append(listener)

    def unsubscribe(self, listener: Listener) -> None:
        self._listeners.remove(listener)

    def _notify(self) -> None:
        for listener in self._listeners:
            listener()

    def _get_projects(self) -> dict[str, Project]:
        project_dict = {}
        projects_raw = io.read_json_file(PROJECT_FILE)
        cached_envs = self._get_cached_envs()
        for project_name, project_data in projects_raw.items():
            project_data["name"] = project_name
            project_cached_envs = []
            for cached_env in cached_envs.get(project_name, {}):
                project_cached_envs.append(cached_env)

            project = Project()
            project_data["cached_envs"] = project_cached_envs
            project.deserialize(project_data)
            project_dict[project_name] = project
        return project_dict

    def _get_notes(self) -> dict[str, str]:
        return io.read_json_file(NOTES_FILE)

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
        return io.update_json_file(PROJECT_FILE, output)

    def save_notes(self) -> int:
        return io.update_json_file(NOTES_FILE, self.notes)

    def _get_cached_envs(self) -> dict:
        """Get the cached environments for a project."""
        try:
            cached_envs = io.read_json_file(CACHED_ENVS_FILE)
            return cached_envs
        except FileNotFoundError:
            return {}

    def _save_cached_envs(self, cached_envs: dict) -> None:
        output = {}
        for project_name, env in cached_envs.items():
            project_envs = []
            for item in env.values():
                project_envs.append(item.serialize())
            if project_envs:
                output[project_name] = project_envs
        """Save the cached environments for a project."""
        io.update_json_file(CACHED_ENVS_FILE, output)


def get_versions(
    project: Project, refresh: bool = False
) -> list[dict[EnvironmentVersion]]:
    """Return a list of environment versions of the project."""
    if not refresh:
        return project.cached_envs

    env_versions = {}  # dict of EnvironmentVersion

    pyenv_dir = Path(Path.home(), ".pyenv", "versions")
    pyenv_versions = _get_versions_from_dir(project, pyenv_dir)

    venv_dir = Path(Path.home(), "projects")
    venv_versions = _get_versions_from_dir(project, venv_dir)

    env_versions = {**pyenv_versions, **venv_versions}
    project.cached_envs = env_versions
    return env_versions


def _get_versions_from_dir(project: Project, path: str) -> dict:
    env_versions = {}  # dict of EnvironmentVersion

    for candidate in store.projects.values():
        for directory, subdirs, files in os.walk(
            candidate.base_dir, followlinks=False
        ):
            del subdirs, files
            if not Path(directory).is_dir():
                continue

            parts = Path(directory).parts
            project_name_index, python_version_index = _get_part_index(parts)
            if project_name_index == 0 or python_version_index == 0:
                continue

            if len(parts) <= project_name_index:
                continue

            if (
                project.name == parts[project_name_index]
                and candidate.name not in env_versions
            ):
                data = (
                    project.name,
                    candidate.name,
                    directory,
                    parts[python_version_index],
                )
                env_versions[candidate.name] = EnvironmentVersion(data)
    return env_versions


def _get_part_index(parts: tuple) -> tuple:
    """Get the project name and python version indices from parts."""
    project_name_index = 0
    python_version_index = 0
    if ".venv" in parts:
        start_index = parts.index(".venv")
        project_name_index = start_index + 4
        python_version_index = start_index + 2
    elif ".pyenv" in parts:
        start_index = parts.index(".pyenv")
        project_name_index = start_index + 6
        python_version_index = start_index + 4
    return project_name_index, python_version_index


# Module-level singleton - this is the instance everyone imports.
store = ProjectStore()
