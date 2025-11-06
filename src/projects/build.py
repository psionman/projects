"""Process the upgrade of the module."""
from contextlib import chdir
import os
import subprocess
import shutil
from pathlib import Path
from dotenv import load_dotenv

from psiutils.constants import Status
from projects import logger

from projects.project import Project
from projects.modules import check_imports

try:
    load_dotenv()
    os.environ["UV_PUBLISH_TOKEN"] = os.getenv("UV_PUBLISH_TOKEN")
    UV_PUBLISH_TOKEN = True
except TypeError:
    logger.error("No .env file found in root dir, or invalid content.")
    UV_PUBLISH_TOKEN = False


def update_module(context: dict) -> int:

    project = context['project']
    logger.info(
        "Starting build process",
        project=project.name,
    )
    check_imports(project.name, project.source_dir)

    if not context['test_build']:
        if _update_version(project, context['version']) != Status.OK:
            return Status.ERROR

        if project.update_history(context['history']) != Status.OK:
            return Status.ERROR
        logger.info(
            "Update history",
            project=project.name,
        )

        if (context['delete_build']
                and _delete_build_dirs(project) != Status.OK):
            return Status.ERROR

    if _build(project) != Status.OK:
        _restore_project(context)
        return Status.ERROR

    if _upload(project, context['test_build']) != Status.OK:
        _restore_project(context)
        return Status.ERROR

    if _git_push(context) != Status.OK:
        return Status.ERROR

    return Status.OK


def _update_version(project: Project, version: str) -> int:
    if project.update_version(version) != Status.OK:
        return Status.ERROR
    logger.info(
        "Update version",
        project=project.name,
        version=version
    )

    if project.update_pyproject_version(version) != Status.OK:
        return Status.ERROR
    logger.info(
        "Update pyproject version",
        project=project.name,
        version=version
    )

    return Status.OK


def _restore_project(context: dict) -> None:
    project = context['project']
    logger.info(
        "Restoring project",
        project=project.name,
    )
    _update_version(project, context['current_version'])
    project.update_history(context['current_history'])


def _build(project: Project) -> int:
    try:
        with chdir(str(project.base_dir)):
            subprocess.call(['uv', 'build'])
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
    return Status.OK


def _upload(project: Project, test_build: bool = False) -> int:
    """
        The PyPi token is stored in the environmental variable UV_PUBLISH_TOKEN
        the value is kept in Documents/pypi folder
    """
    try:
        with chdir(str(project.base_dir)):
            if test_build:
                proc = subprocess.Popen(['uv', 'publish', '--dry-run'])
            else:
                proc = subprocess.Popen(['uv', 'publish'])
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
                f'Package not uploaded! Return code: {proc.returncode}',
                project=project.name,
                )
            return Status.ERROR

    except FileNotFoundError as error:
        logger.exception(
            f'Error! {error}',
            project=project.name,
            )
        return Status.ERROR
    return Status.OK


def _git_push(context: dict) -> int:
    """Save the version to remote git repository."""
    if not context['sync_repository']:
        return Status.OK

    project = context['project']
    returncode = _proc_action(project, ['git', 'add', '.'])
    returncode += _proc_action(
        project, ['git', 'commit', '-m', context['commit_text']])
    returncode += _proc_action(project, ['git', 'push', 'origin', 'master'])

    if returncode == 0:
        logger.info(
            "git repository uploaded",
            project=project.name,
        )
        return Status.OK
    else:
        logger.exception(
            f'git repository not uploaded, Return code: {returncode}',
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


def _delete_build_dirs(project: Project) -> int:
    logger.info(
        "Removing build directories",
        project=project.name,
    )
    for build_dir in [
        'dist',
        'build',
        f'{project.name}.egg-info',
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
                logger.exception(f'Failed to remove {path}')
                return Status.ERROR
    return Status.OK
