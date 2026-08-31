from tkinter import messagebox

from psiutils.constants import Status

from projects.build import UV_PUBLISH_TOKEN
from projects.forms.frm_build import BuildFrame
from projects.project import Project


def build_project(
    parent: any, project: Project, git_commit: bool = False
) -> None:
    """Build a project."""
    if not UV_PUBLISH_TOKEN:
        messagebox.showerror("", "UV_PUBLISH_TOKEN not set.")
        return Status.ERROR

    if not _is_valid(project):
        return Status.ERROR

    dlg = BuildFrame(parent, project, git_commit)
    parent.root.wait_window(dlg.root)
    return Status.OK


def _is_valid(project: Project) -> bool:
    # if project.pyproject_missing:
    #     messagebox.showerror("", "pyproject.toml missing")
    #     return False
    return True
