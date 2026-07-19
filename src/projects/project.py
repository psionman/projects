"""Project data for Compare."""

import subprocess
import tomllib
from datetime import datetime
from pathlib import Path

import json5
import tomli_w
from psiutils.constants import Status

import projects.projects_io as io
from projects import logger
from projects.constants import (
    DEFAULT_COLOURS,
    DEFAULT_VERSION_TEXT,
    HISTORY_FILE,
    PYPROJECT_TOML,
    VERSION_FILE,
)
from projects.env_version import EnvironmentVersion
from projects.utilities import collapse_home, expand_home

SERIALIZABLE_FIELDS = [
    "base_dir",
    "source_dir",
    "script",
    "desktop_file",
    "pypi",
    "repository",
    "build_for_windows",
    "modified_versions",
]

DIR_FIELDS = ["base_dir", "source_dir", "script", "desktop_file"]


class Project:
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

        self.name: str = ""
        self.source_dir: str = ""
        self.base_dir: str = ""
        self.env_dir: str = ""
        self.description: str = ""
        self.version: str = DEFAULT_VERSION_TEXT
        self.history: list[str] = []
        self.new_history: list[str] = []
        self._pyproject_list = []
        self.env_versions: dict = {}
        self.cached_envs = {}
        self.pyproject_data: dict = {}
        self.script: str = ""
        self.desktop_file: str = ""
        self.repository: str = ""
        self.pypi = False
        self.build_for_windows = False
        self.workbench_colours: dict = {}
        self.modified_versions = []
        self.notes = ""

    def __repr__(self) -> str:
        """
        Returns a string representation of the Projects object.

        Returns:
            str: A string representation of the Projects object.
        """

        return f"Project: {self.name}"

    @property
    def requirements_path(self) -> Path:
        """Return path to requirements file."""
        return Path(self.base_dir, "requirements.txt")

    @property
    def history_path(self) -> Path:
        """Return path to History file."""
        return Path(self.base_dir, HISTORY_FILE)

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
        history = self.history
        date = datetime.now().strftime("%d %B %Y")
        version = f"## Version {self.next_version()} - {date}"
        insertion = ["", version, "1.", ""]
        return "\n".join([history[0]] + insertion + history[2:])

    def next_version(self) -> str:
        """Return the next version string."""
        version = self.version.split(".")
        if "missing" in version[0]:
            path = Path(self.source_dir, VERSION_FILE)
            logger.warning(
                f"version file missing: {path}",
                project=self.name,
            )
            return ""
        if len(version) != 3:
            logger.warning(
                f"Invalid version (structure) {self.version}",
                project=self.name,
            )
            return ""
        if not version[2].isnumeric():
            logger.warning(
                f"Invalid version (non-numeric) {self.version}",
                project=self.name,
            )
            return ""
        return f"{version[0]}.{version[1]}.{int(version[2]) + 1}"

    @staticmethod
    def _clean_string(text: str) -> str:
        text = text.strip()
        text = text.replace('"', "")
        return text.replace("'", "")

    def _get_project_meta_data(self) -> str:
        """Get the description for a project."""
        try:
            with open(Path(self.base_dir, self.pyproject_path), "rb") as f:
                self.pyproject_data = tomllib.load(f)
            self.version = self.pyproject_data["project"]["version"]
            self.description = self.pyproject_data["project"]["description"]
        except FileNotFoundError:
            logger.warning(f"pyproject.toml not found: Project: {self.name}")
            return ""

    def _get_history(self) -> list[str]:
        """Get the history for a project."""
        try:
            with open(Path(self.base_dir, self.history_path)) as f:
                return f.read().split("\n")
        except FileNotFoundError:
            logger.warning(f"history.md not found: Project: {self.name}")
            return []

    def serialize(self) -> dict:
        """
        Serializes the Project object into a dictionary.

        Returns:
            dict: A dictionary containing serialized project data.
        """
        output = {}
        for key in SERIALIZABLE_FIELDS:
            if getattr(self, key):
                if key in DIR_FIELDS:
                    output[key] = collapse_home(getattr(self, key))
                else:
                    output[key] = getattr(self, key)
        return output

    def deserialize(self, data: dict) -> None:
        """Deserialize the project from a dictionary."""
        self.name = data["name"]
        for key in SERIALIZABLE_FIELDS:
            if key in data:
                setattr(self, key, data[key])
            if key in DIR_FIELDS:
                setattr(self, key, expand_home(getattr(self, key)))

        self._get_project_meta_data()
        self.history = self._get_history()
        self.new_history = self._get_new_history()
        self.workbench_colours = self._get_workbench_colours()
        self.cached_envs = self._get_cached_envs(data)

    def _get_cached_envs(self, data: dict) -> None:
        """Get the cached environments for a project."""
        cached_envs = {}
        if "cached_envs" in data:
            for env in data["cached_envs"]:
                env.insert(0, self.name)
                env_version = EnvironmentVersion(env)
                cached_envs[env_version.name] = env_version
        return cached_envs

    def save_project_colours(self) -> None:
        """Save the colours for a project."""
        settings_file = Path(
            Path(self.source_dir).parent.parent, ".vscode", "settings.json"
        )
        try:
            with open(settings_file, encoding="utf-8") as f:
                settings = json5.load(f)
        except FileNotFoundError:
            return
        if self.workbench_colours != DEFAULT_COLOURS:
            settings["workbench.colorCustomizations"] = self.workbench_colours
            with open(settings_file, "w", encoding="utf-8") as f:
                json5.dump(settings, f, indent=2)

    def update_version(self, version: str) -> int:
        self.pyproject_data["project"]["version"] = version
        with open(Path(self.base_dir, self.pyproject_path), "wb") as f:
            tomli_w.dump(self.pyproject_data, f)

        return Status.SUCCESS

    def update_history(self, history: str) -> int:
        return io.update_file(self.history_path, history)

    def update_pyproject(self) -> int:
        """Create a requirements.txt and update pyproject.toml accordingly."""
        logger.info(
            "Starting pyproject.toml update process",
            project=self.name,
        )
        self._install_pip()
        self._create_requirements()
        return self._update_pyproject()

    def _update_pyproject(self) -> int:
        pyproject = self._read_pyproject()

        dev_dependencies = {}
        if "dependency-groups" in pyproject:
            dev_dependencies = self._build_dependency_dict(
                pyproject["dependency-groups"]["dev"]
            )

        requirements = self._build_dependency_dict(self._read_requirements())

        logger.info(
            "Update project dependencies: read requirements",
            project=self.name,
        )

        for item in dev_dependencies:
            if item in requirements:
                del requirements[item]

        for key, item in requirements.items():
            requirements[key] = item.replace("==", ">=")

        self._write_requirements("\n".join(list(requirements.values())))

        code = 0
        return code

    def _build_dependency_dict(self, dependencies: dict) -> dict:
        output = {}
        for item in dependencies:
            if item.startswith("#"):
                continue
            if item.startswith("-"):
                continue
            if ">" in item:
                key = item[: item.index(">")]
                output[key] = item
            elif "=" in item:
                key = item[: item.index("=")]
                output[key] = item
            else:
                output[item] = ""
        return output

    def _read_pyproject(self) -> dict:
        with open(self.pyproject_path, "rb") as f_pyproject:
            return tomllib.load(f_pyproject)

    def _read_requirements(self) -> list[str]:
        requirements = io.read_text_file(self.requirements_path).strip()
        return requirements.split("\n")

    def _write_requirements(self, requirements: str) -> None:
        io.update_file(self.requirements_path, requirements)

    def _create_requirements(self) -> int:
        with open(
            self.requirements_path, "w", encoding="utf-8"
        ) as f_requirements:
            subprocess.run(
                [f"{self.base_dir}/.venv/bin/pip3", "freeze"],
                stdout=f_requirements,
                check=True,
            )
            logger.info(
                "Update project dependencies: requirements_created",
                project=self.name,
            )

    def _install_pip(self) -> int:
        path = f"{self.base_dir}/.venv/bin/python"
        if subprocess.run([path, "-m", "ensurepip", "-U"], check=True):
            logger.info(
                "Update project dependencies: pip installed",
                project=self.name,
            )

    def _get_workbench_colours(self) -> None:
        """Get the colours for the project."""
        settings_file = Path(Path(self.base_dir), ".vscode", "settings.json")
        try:
            with open(settings_file, encoding="utf-8") as f:
                settings = json5.load(f)
        except FileNotFoundError:
            return DEFAULT_COLOURS.copy()

        workbench_colours = {}
        if "workbench.colorCustomizations" in settings:
            colour_customizations = settings["workbench.colorCustomizations"]
            for key, value in colour_customizations.items():
                workbench_colours[key] = value
        if workbench_colours:
            return workbench_colours
        return DEFAULT_COLOURS.copy()
