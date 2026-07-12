"""
environment_version
====================

Provides tools for representing and managing Python virtual environment
metadata, including directory paths, Python versions, and version
information from a `_version.py` file.

Classes
-------
EnvironmentData : NamedTuple
    Immutable data container holding the environment's name, directory,
    and Python version.

EnvironmentVersion
    Represents and manages the details of a Python environment.
    Can serialize/deserialize environment data, locate the
    environment's Python binary, and extract version numbers from
    `_version.py` files.

Usage Example
-------------
>>> data = EnvironmentData(
...     name="my_env",
...     dir="/path/to/project/.venv",
...     python_version="3.11.4"
... )
>>> env = EnvironmentVersion(data)
>>> env.version
'1.0.0'
>>> env.venv_python
'/path/to/project/.venv/bin/python'
>>> env.dir_short
'~/projects/project/.venv'

Notes
-----
- Version extraction looks for a semantic version pattern (e.g.,
'1.2.3') in `_version.py`.
- Supports `.venv` and `.pyenv` layouts when locating the Python
executable.
"""

import os
import re
from pathlib import Path
from typing import NamedTuple

from projects import logger


class EnvironmentData(NamedTuple):
    project: str
    name: str
    dir: str
    python_version: str


class EnvironmentVersion:
    """
    EnvironmentVersion:
    Class for handling environment version information.

    __init__:
    Initialize the EnvironmentVersion instance with optional data
    and set attributes. Deserialize data if provided and get the version.

    serialize:
    Return a tuple of the version for JSON serialization.

    deserialize:
    Deserialize the version from JSON data.

    _get_version:
    Get the version from a file in the directory.

    get_venv_python:
    Get the path to the Python executable in a virtual environment.

    dir_short:
    Property method to return a shortened directory path.
    """

    def __init__(self, data: EnvironmentData = None) -> None:
        self.project = ""
        self.name = ""
        self.dir = ""
        self.python_version = ""
        self.type = ""

        if data:
            self.deserialize(data)

        self.version = self._get_version()

    def __repr__(self) -> str:
        return (
            "EnvironmentVersion("
            f"project='{self.project}', "
            f"name='{self.name}', "
            f"dir='{self.dir}', "
            f"python_version='{self.python_version}')"
        )

    def serialize(self) -> tuple:
        """Return a tuple of the env version for json serialization.

        NB serialize does not contain the project name
        """
        return (
            self.name,
            str(self.dir),
            self.python_version,
        )

    def deserialize(self, data: list | tuple) -> None:
        """Deserialize the env version from json."""
        environ = EnvironmentData(*data)

        self.project = environ.project
        self.name = environ.name
        self.dir = environ.dir
        self.python_version = environ.python_version
        self.version = self._get_version()
        self.venv_python = self.get_venv_python()

    def _get_version(self):
        project_re = rf"{re.escape(self.project)}-(\d[\d.]+)\.dist-info"
        package_dir = Path(self.dir).parent
        try:
            for meta_dir in os.listdir(package_dir):
                match = re.search(project_re, meta_dir)
                if match:
                    return match.group(1)
        except FileNotFoundError:
            logger.warning(f"Package directory not found: {package_dir}")

        return "Version error"

    def get_venv_python(self) -> str:
        parts = Path(self.dir).parts
        if ".venv" in parts:
            index = parts.index(".venv")
            source_dir = Path(*parts[:index])
            return os.path.join(source_dir, ".venv", "bin", "python")
        if ".pyenv" in parts:
            index = parts.index("versions")
            source_dir = Path(*parts[: index + 2])
            return os.path.join(source_dir, "bin", "python")
        return ""
