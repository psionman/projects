"""Process the upgrade of the module."""

import os
import shutil
import subprocess
from contextlib import chdir
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from psiutils.constants import Status

from projects import logger
from projects.modules import check_imports
from projects.project import Project

try:
    load_dotenv()
    os.environ["UV_PUBLISH_TOKEN"] = os.getenv("UV_PUBLISH_TOKEN")
    UV_PUBLISH_TOKEN = True
except TypeError:
    logger.error("No .env file found in root dir, or invalid content.")
    UV_PUBLISH_TOKEN = False


@dataclass
class BuildData:
    project: Project
    delete_build: bool
    version: str
    current_version: str
    history: str
    previous_history: str
    test_build: bool
    sync_repository: str
    commit_text: str
    git_commit: bool


def update_module(build_data: dict) -> int:
    project = build_data.project
    logger.info(
        "Starting build process",
        project=project.name,
    )
    if not build_data.git_commit:
        check_imports(project.name, project.source_dir)
        project.update_pyproject()

    if not build_data.test_build:
        if _update_version(build_data) == Status.ERROR:
            return Status.ERROR
        if _update_history(build_data) == Status.ERROR:
            return Status.ERROR
        if _delete_build_dirs(build_data) == Status.ERROR:
            return Status.ERROR

    if not build_data.git_commit:
        if _build(project) != Status.SUCCESS:
            _restore_project(build_data)
            return Status.ERROR

    if project.pypi:
        if _pypi_push(project, build_data.test_build) != Status.SUCCESS:
            _restore_project(build_data)
            return Status.ERROR

    if _git_push(build_data) != Status.SUCCESS:
        return Status.ERROR

    return Status.SUCCESS


def _update_version(build_data: dict) -> Status:
    if build_data.project.update_version(build_data.version) != Status.SUCCESS:
        return Status.ERROR
    logger.info(
        "Update version",
        project=build_data.project.name,
        version=build_data.version,
    )
    return Status.SUCCESS


def _update_history(build_data: dict) -> Status:
    if build_data.project.save_history(build_data.history) != Status.SUCCESS:
        return Status.ERROR
    logger.info("Update history", project=build_data.project.name)
    return Status.SUCCESS


def _delete_build_dirs(build_data: dict) -> int:
    project = build_data.project
    if not build_data.delete_build:
        return Status.SUCCESS
    for build_dir in [
        "dist",
        "build",
        f"{project.name}.egg-info",
    ]:
        path = Path(project.base_dir, build_dir)
        if path.is_dir():
            try:
                shutil.rmtree(path)
                logger.info(
                    "Removing path",
                    project=project.name,
                    path=str(path),
                )
            except OSError:
                logger.exception(f"Failed to remove {path}")
                return Status.ERROR
    logger.info(
        "Build directories removed",
        project=project.name,
    )
    return Status.SUCCESS


def _restore_project(build_data: dict) -> None:
    project = build_data.project
    logger.info(
        "Restoring project",
        project=project.name,
    )
    _update_version(project, build_data.current_version)
    project.save_history(build_data.previous_history)


def _build(project: Project) -> int:
    try:
        with chdir(str(project.base_dir)):
            subprocess.call(["uv", "build"])
    except FileNotFoundError as error:
        logger.warning(
            "Build failed",
            error=error,
        )
        return Status.ERROR
    logger.info(
        "Build project",
        project=project.name,
    )
    return Status.SUCCESS


def _pypi_push(project: Project, test_build: bool = False) -> int:
    """
    The PyPi token is stored in the environmental variable UV_PUBLISH_TOKEN
    the value is kept in Documents/pypi folder
    """
    try:
        with chdir(str(project.base_dir)):
            if test_build:
                proc = subprocess.Popen(["uv", "publish", "--dry-run"])
            else:
                proc = subprocess.Popen(["uv", "publish"])
        proc.wait()
        (stdout, stderr) = proc.communicate()
        del stdout, stderr

        if proc.returncode == 0:
            logger.info(
                "Package uploaded",
                project=project.name,
            )
        else:
            logger.exception(
                f"Package not uploaded! Return code: {proc.returncode}",
                project=project.name,
            )
            return Status.ERROR

    except FileNotFoundError as error:
        logger.exception(
            f"Error! {error}",
            project=project.name,
        )
        return Status.ERROR
    return Status.SUCCESS


def _git_push(build_data: dict) -> int:
    """Save the version to remote git repository."""
    if not build_data.sync_repository:
        return Status.SUCCESS

    project = build_data.project
    returncode = _proc_action(project, ["git", "add", "."])
    returncode += _proc_action(
        project, ["git", "commit", "-m", build_data.commit_text]
    )
    returncode += _proc_action(project, ["git", "push", "origin", "master"])

    if returncode == 0:
        logger.info(
            "git repository uploaded",
            project=project.name,
        )
        return Status.SUCCESS

    logger.exception(
        f"git repository not uploaded, Return code: {returncode}",
        project=project.name,
    )
    return Status.ERROR


def _proc_action(project: Project, action: list[str]) -> int:
    with chdir(str(project.base_dir)):
        proc = subprocess.Popen(action)
    proc.wait()
    (stdout, stderr) = proc.communicate()
    del stdout, stderr
    return proc.returncode
