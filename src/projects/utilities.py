import subprocess
import threading
from typing import Any


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
