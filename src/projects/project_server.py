"""Project server for package application."""
from pathlib import Path

from projects.config import config
from projects.project import Project
from projects.env_version import EnvironmentVersion
from projects.constants import DATA_DIR
import projects.projects_io as io


class ProjectServer():
    """Handle projects."""
    def __init__(self) -> None:
        # pylint: disable=no-member
        self.project_file = Path(DATA_DIR, config.project_file)
        self.projects = self._get_projects()

    def _get_projects(self) -> dict[str, Project]:
        project_dict = {}
        projects_raw = io.read_json_file(self.project_file)
        for key, item in projects_raw.items():
            project = Project()
            project.name = key
            project_dict[key] = project

            project.source_dir = item['dir']
            project.pypi = item['pypi']
            if 'build_for_windows' not in item:
                item['build_for_windows'] = False
            project.build_for_windows = item['build_for_windows']
            if 'repository' in item:
                project.repository_name = item['repository']
            project.cached_envs = {key: EnvironmentVersion(data)
                                   for key, data
                                   in item['cached_envs'].items()}
            if 'script' in item:
                project.script = item['script']
            project.get_project_data()
        return project_dict

    def save_projects(self, projects: dict[str, Project] = None) -> int:
        if not projects:
            projects = self.projects
        self.projects = projects
        output = {name: project.serialize()
                  for name, project in projects.items()}
        return io.update_json_file(self.project_file, output)
