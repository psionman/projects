"""Project utilities for package application."""

import os
import subprocess
from pathlib import Path

from projects import logger


def update_project(version: str, env_version: str, project: str) -> None:
    returncode = 0
    venv_python = _get_venv_python(env_version)
    if not venv_python:
        return 1

    logger.info(
        "Update .venv dependencies",
        dependency=version,
        project=project,
    )

    # Use the venv's python to run pip
    # ensure pip is installed
    command = [venv_python, '-m', 'ensurepip', '--upgrade']

    result = subprocess.run(command, check=True)
    returncode += result.returncode
    logger.info(
        "Update .venv dependencies install pip",
        dependency=version,
        project=project,
    )

    # upgrade package
    command = [venv_python, '-m', 'pip', 'install', '-U', project]
    result = subprocess.run(command, check=True)
    returncode += result.returncode

    if returncode == 0:
        logger.info(
            "Update .venv dependencies update package",
            dependency=version,
            project=project,
        )
    else:
        logger.warning(
            "Update .venv dependencies update package failed",
            dependency=env_version,
            project=project,
        )

    return returncode


def _get_venv_python(env_version: str) -> str:
    parts = Path(env_version.dir).parts
    if '.venv' in parts:
        index = parts.index('.venv')
        source_dir = Path(*parts[:index])
        return os.path.join(source_dir, '.venv', 'bin', 'python')
    if '.pyenv' in parts:
        index = parts.index('versions')
        source_dir = Path(*parts[:index+2])
        return os.path.join(source_dir, 'bin', 'python')

    return ''
