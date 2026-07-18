import subprocess
import threading
from typing import Any

from projects.constants import HOME_DIR


def open_in_kate(file_path: str) -> None:
    call_process(["kate", file_path])
    _activate_kate(file_path)


def _activate_kate(file_path: str) -> None:
    subprocess.run(
        [
            "gdbus",
            "call",
            "--session",
            "--dest",
            "org.kde.kate",
            "--object-path",
            "/MainApplication",
            "--method",
            "org.kde.Kate.Application.activate",
            f"file://{file_path}",
        ],
        check=False,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            "kdotool",
            "search",
            "--name",
            "kate",
            "windowactivate",
        ],
        check=False,
    )


def call_process(process: list) -> Any:
    threading.Thread(
        target=_call_process_worker,
        args=(process,),
        daemon=True,
    ).start()


def _call_process_worker(process: list) -> None:
    proc = subprocess.Popen(
        process,
        stdout=subprocess.PIPE,
        text=True,
    )

    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        error = "None"
        if stderr:
            error = stderr.strip().split("\n")[-1]
        logger.error("Process failed", process=process, error=error)

        # self.root.after(
        #     0, lambda: messagebox.showerror("", "Process failed")
        # )


def collapse_home(path: str) -> str:
    return path.replace(HOME_DIR, "~")


def expand_home(path: str) -> str:
    return path.replace("~", HOME_DIR)


def open_dolphin(path) -> None:
    path = str(path)
    service = _find_dolphin_service()
    if service:
        subprocess.call(
            [
                "qdbus6",
                service,
                "/dolphin/Dolphin_1",
                "org.kde.dolphin.MainWindow.openDirectories",
                f"file://{path}",
                "false",
            ]
        )
    else:
        subprocess.Popen(["dolphin", path])


def _find_dolphin_service() -> str | None:
    """Return a running Dolphin's D-Bus service name, if any."""
    result = subprocess.run(
        ["qdbus6"], capture_output=True, text=True, check=True
    )
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("org.kde.dolphin"):
            return line
    return None
