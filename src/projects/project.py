"""Project data for Compare."""
import os
from pathlib import Path
from datetime import datetime
import re
import subprocess

from psiutils.constants import Status
from psi_toml.parser import TomlParser

from projects import logger
from projects.env_version import EnvironmentVersion
from projects.constants import (
    PYPROJECT_TOML, HISTORY_FILE, VERSION_FILE, VERSION_TEXT)

import projects.projects_io as io


class Project():
    """Project class to support the package module."""

    # base_dir is the base directory containing, e.g. HISTORY.md

    def __init__(self) -> None:
        """
            Initializes a Projects object.

            Args:
                self: The Projects object itself.

            Returns:
                None
        """

        self.name: str = ''
        self.source_dir: str = ''
        self._source_dir_short: str = ''
        self._base_dir: Path = None
        self.env_dir: str = ''
        self._env_dir_short: str = ''
        self.project_version: str = ''
        self.pyproject_version: str = ''
        self.history = ''
        self.new_history = ''
        self._pyproject_list = []
        self.env_versions: dict = {}
        self.cached_envs = {}
        self.py_project_missing = True
        self._version_text = ''
        self.script: str = ''
        self.repository_name: str = ''
        self.pypi = False
        self.build_for_windows = False

    def __repr__(self) -> str:
        """
        Returns a string representation of the Projects object.

        Returns:
            str: A string representation of the Projects object.
        """

        return f'Project: {self.name}'

    @property
    def env_dir_short(self) -> str:
        return self._short_dir(self.env_dir)

    @property
    def source_dir_short(self) -> str:
        return self._short_dir(self.source_dir)

    def serialize(self) -> dict:
        """
            Serializes the Projects object into a dictionary.

            Returns:
                dict: A dictionary containing serialized project data.
        """
        return {
            'dir': self.source_dir,
            'pypi': self.pypi,
            'repository': self .repository_name,
            'build_for_windows': self.build_for_windows,
            'cached_envs': {key: item.serialize()
                            for key, item in self.cached_envs.items()},
            'script': self.script,
            }

    @staticmethod
    def _short_dir(long_dir: str) -> str:
        return long_dir.replace(str(Path.home()), '~')

    def _get_env_version(self) -> str:
        raw_text = io.read_text_file(Path(self.env_dir, VERSION_FILE))
        return self._get_version_text(raw_text)

    def _get_project_version(self) -> str:
        raw_text = io.read_text_file(Path(self.source_dir, VERSION_FILE))
        if raw_text == Status.ERROR:
            return ''
        return self._get_version_text(raw_text)

    def _get_version_text(self, raw_text: str) -> str:
        for line in raw_text.split('\n'):
            if VERSION_TEXT in line and '=' in line:
                version_text = line.split('=')[1]
                version_text = version_text.strip()
                version_text = version_text.replace("'", '')
                return version_text
        return 'Version text missing'

    @property
    def base_dir(self) -> Path:
        """Return path to base directory of the project."""
        if not self._base_dir:
            self._base_dir = Path(self.source_dir).parent
            if not Path(self._base_dir, 'pyproject.toml').is_file():
                self._base_dir = self._base_dir.parent
        return self._base_dir

    @property
    def requirements_path(self) -> Path:
        """Return path to requirements file."""
        return Path(self.base_dir, 'requirements.txt')


    @property
    def history_path(self) -> Path:
        """Return path to History file."""
        return Path(self.base_dir, HISTORY_FILE)

    @property
    def version_text(self) -> str:
        """Return version as text."""
        if self._version_text:
            return self._version_text

        err_text = 'Version not found'
        version = self._get_project_version()
        version_re = r'^[0-9]{1,}.[0-9]{1,}.[0-9]{1,}$'
        self._version_text = (version if re.match(version_re, version)
                              else err_text)
        return self._version_text

    @version_text.setter
    def version_text(self, value: str) -> None:
        self._version_text = value

    @property
    def version_path(self) -> Path:
        """Return path to version file."""
        return Path(self.source_dir, VERSION_FILE)

    @property
    def pyproject_path(self) -> Path:
        """Return path to pyprojects file."""
        return Path(self.base_dir, PYPROJECT_TOML)

    def _get_new_history(self) -> str:
        if not self.history:
            return []
        history = self.history.split('\n')
        date = datetime.now().strftime('%d %B %Y')
        version = f'Version {self.next_version()} - {date}'
        insertion = ['', version, '', '1. ', '-'*30, '']
        return '\n'.join([history[0]] + insertion + history[2:])

    def next_version(self) -> str:
        """Return the next version string."""
        version = self.project_version.split('.')
        if 'missing' in version[0]:
            path = Path(self.source_dir, VERSION_FILE)
            logger.warning(
                f'version file missing: {path}',
                project=self.name,
            )
            return ''
        if len(version) != 3:
            logger.warning(
                f'Invalid version (structure) {self.project_version}',
                project=self.name,
            )
            return ''
        if not version[2].isnumeric():
            logger.warning(
                f'Invalid version (non-numeric) {self.project_version}',
                project=self.name,
            )
            return ''
        return f'{version[0]}.{version[1]}.{int(version[2]) + 1}'

    @staticmethod
    def _clean_string(text: str) -> str:
        text = text.strip()
        text = text.replace('"', '')
        return text.replace("'", '')

    def _get_pyproject_version(self) -> str:
        default = '-.-.-'
        self.py_project_missing = False

        pyproject_text = io.read_text_file(self.pyproject_path)
        if pyproject_text == Status.ERROR:
            self.py_project_missing = True
            print(f'pyproject.toml missing {self.pyproject_path}')
            return default

        self._pyproject_list = pyproject_text.split('\n')
        for line in self._pyproject_list:
            if 'version =' in line:
                line_list = line.split('=')
                if len(line_list) != 2:
                    err_str = 'pyproject.toml format error in'
                    print(f'{err_str} {self.pyproject_path}')
                    return default
                return self._clean_string(line_list[1])
        return

    def get_project_data(self) -> None:
        """Update project attributes."""
        self.project_version = self._get_project_version()
        self.history = io.read_text_file(self.history_path)
        if self.history == Status.ERROR:
            self.history = ''
        self.new_history = self._get_new_history()
        self.pyproject_version = self._get_pyproject_version()

    def update_version(self, version: str) -> int:
        output = f'{VERSION_TEXT} = \'{version}\''
        return io.update_file(self.version_path, output)

    def update_pyproject_version(self, version: str) -> int:
        for index, line in enumerate(self._pyproject_list):
            if 'version =' in line:
                line_list = line.split('=')
                if len(line_list) != 2:
                    print(f'Version format error in {self.version_path}')
                    return Status.ERROR
                version_text = f'{line_list[0].strip()} = "{version}"'

                output = self._pyproject_list[:index]
                output.append(version_text)
                output.extend(self._pyproject_list[index+1:])
                break

        return io.update_file(self.pyproject_path, '\n'.join(output))

    def update_history(self, history: str) -> int:
        return io.update_file(self.history_path, history)

    def get_versions(
            self, refresh: bool = False) -> list[dict[EnvironmentVersion]]:
        """Return a list of environment versions of the project."""
        if not refresh:
            return self.cached_envs

        env_versions = {}  # dict of EnvironmentVersion

        pyenv_dir = Path(Path.home(), '.pyenv', 'versions')
        pyenv_versions = self._get_versions_from_dir(pyenv_dir)

        venv_dir = Path(Path.home(), 'projects')
        venv_versions = self._get_versions_from_dir(venv_dir)

        env_versions = {**pyenv_versions, **venv_versions}
        self.cached_envs = env_versions
        return env_versions

    def _get_versions_from_dir(self, path: str) -> dict:
        env_versions = {}  # dict of EnvironmentVersion

        for directory, subdirs, files in os.walk(path, followlinks=False):
            del subdirs, files
            project_name_index, environment_index = 0, 0

            if not Path(directory).is_dir():
                continue

            parts = Path(directory).parts
            if '.venv' in parts:
                start_index = parts.index('.venv')
                project_name_index = start_index + 4
                environment_index = start_index - 1
                python_version_index = start_index + 2
            elif '.pyenv' in parts:
                start_index = parts.index('.pyenv')
                project_name_index = start_index + 6
                environment_index = start_index + 2
                python_version_index = start_index + 4
            else:
                continue

            if len(parts) <= project_name_index:
                continue

            if self.name == parts[project_name_index]:
                environment_name = parts[environment_index]
                if environment_name not in env_versions:
                    data = (
                        environment_name,
                        directory,
                        parts[python_version_index])
                    env_versions[environment_name] = EnvironmentVersion(data)
        return env_versions

    def update_pyproject(self) -> int:
        """Create a requirements.txt and update pyproject.tom accordingly."""

        logger.info(
            "Starting pyproject.toml update process",
            project=self.name,
        )
        self._install_pip()
        self._create_requirements()
        return self._update_pyproject()

    def _update_pyproject(self) -> int:
        pyproject = self._read_pyproject()

        dev_dependencies = self._build_dependency_dict(
            pyproject['dependency-groups']['dev'])

        requirements = self._build_dependency_dict(
            self._read_requirements())
        logger.info(
            "Update project dependencies: read requirements",
            project=self.name,
        )

        for item in dev_dependencies:
            if item in requirements:
                del requirements[item]

        for key, item in requirements.items():
            requirements[key] = item.replace('==', '>=')

        self._write_requirements('\n'.join(list(requirements.values())))

        code = subprocess.run(
                ['uv', 'add', '-r', self.requirements_path,],
                check=True,
                cwd=self.base_dir
            ).returncode
        if code == 0:
            logger.info(
                "Update project dependencies: requirements added",
                project=self.name,
            )
        else:
            logger.warning(
                "Update project dependencies: read requirements failed",
                project=self.name,
            )
        return code

    def _build_dependency_dict(self, dependencies: dict) -> dict:
        output = {}
        for item in dependencies:
            if item.startswith('#'):
                continue
            if item.startswith('-'):
                continue
            if '>' in item:
                key = item[:item.index('>')]
                output[key] = item
            elif '=' in item:
                key = item[:item.index('=')]
                output[key] = item
            else:
                output[item] = ''
        return output

    def _read_pyproject(self) -> dict:
        parser = TomlParser()
        with open(self.pyproject_path, 'r', encoding='utf-8') as f_pyproject:
            return parser.load(f_pyproject)

    def _read_requirements(self) -> list[str]:
        requirements = io.read_text_file(self.requirements_path).strip()
        return requirements.split('\n')

    def _write_requirements(self, requirements: str) -> None:
        io.update_file(self.requirements_path, requirements)

    def _create_requirements(self) -> int:
        with open(
                self.requirements_path,
                'w',
                encoding='utf-8') as f_requirements:
            subprocess.run(
                [f'{self.base_dir}/.venv/bin/pip3', 'freeze'],
                stdout=f_requirements,
                check=True
            )
            logger.info(
                "Update project dependencies: requirements_created",
                project=self.name,
            )

    def _install_pip(self) -> int:
        path = f'{self.base_dir}/.venv/bin/python'
        if subprocess.run([path, '-m', 'ensurepip', '-U'], check=True):
            logger.info(
                "Update project dependencies: pip installed",
                project=self.name,
            )
