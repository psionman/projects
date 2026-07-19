"""Project utilities for package application."""

import subprocess

from projects import logger
from projects.data_store import store as data_store
from projects.env_version import EnvironmentVersion
from projects.project import Project


def update_project(
    version: str, env_version: EnvironmentVersion, project: Project
) -> int:
    print(f"version: {version}")
    print(f"env_version: {env_version}")
    print(f"project: {project}")
    print("b", "directors_rota" in data_store.projects)
    print("c", "bbo rota" in data_store.projects)
    for x in data_store.projects.keys():
        print(f"project: {x}")
    base_dir = data_store.projects[env_version.name].base_dir

    venv_python = env_version.get_venv_python()
    if not venv_python:
        logger.warning(
            "No venv python found for environment",
            environment=env_version,
            project=project,
        )
        return 1

    logger.info(
        "Update .venv dependencies",
        dependency=version,
        project=project,
    )

    lock_command = [
        "uv",
        "lock",
        "--upgrade-package",
        project.name,
        "--refresh-package",
        project.name,
        "--python",
        str(venv_python),
    ]
    try:
        subprocess.run(
            lock_command,
            cwd=base_dir,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.warning(
            "uv lock failed",
            dependency=version,
            project=project,
            stderr=exc.stderr,
        )
        return 1

    sync_command = ["uv", "sync", "--python", str(venv_python)]
    try:
        subprocess.run(
            sync_command,
            cwd=base_dir,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.warning(
            "uv sync failed",
            dependency=version,
            project=project,
            stderr=exc.stderr,
        )
        return 1

    logger.info(
        "Update .venv dependencies update package",
        dependency=version,
        project=project,
    )
    return 0
