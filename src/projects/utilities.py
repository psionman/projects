import subprocess
import threading
from pathlib import Path
from typing import Any

import dbus
import dbus.mainloop.glib

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


dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)


def open_dolphin(path: str | Path) -> None:
    path = Path(path).resolve()

    bus = dbus.SessionBus()

    service = _find_dolphin_service(bus)

    if service is None:
        subprocess.Popen(
            ["dolphin", str(path)],
            start_new_session=True,
        )
        return

    obj = bus.get_object(
        service,
        "/dolphin/Dolphin_1",
    )

    dolphin = dbus.Interface(
        obj,
        "org.kde.dolphin.MainWindow",
    )

    dolphin.openDirectories(
        dbus.Array(
            [path.as_uri()],
            signature="s",
        ),
        False,
    )


def _find_dolphin_service(bus) -> str | None:
    names = bus.list_names()

    services = [name for name in names if name.startswith("org.kde.dolphin-")]

    return services[0] if services else None
