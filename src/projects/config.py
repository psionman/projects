from pathlib import Path

from psiconfig import ConfigField, TomlConfig

from projects.constants import CONFIG_PATH, USER_DATA_DIR

# FIELDS for config, and to create tkinter variables in frm_config.py
# e.g. self.data_directory is a tk.StringVar
FIELDS = {
    "data_directory": ConfigField(str, USER_DATA_DIR),
    "script_directory": ConfigField(str, Path(Path.home(), ".scripts")),
    "desktop_directory": ConfigField(str, Path(USER_DATA_DIR, "applications")),
}

DEFAULT_CONFIG = {
    "data_directory": USER_DATA_DIR,
    "last_project": "",
    "script_directory": "",
    "desktop_directory": "",
    "project_file": "projects.json",
    "ignore": [],
    "geometry": {
        "frm_main": "1400x600",
        "frm_config": "800x200",
        "frm_build": "700x900",
        "frm_compare": "1100x900",
        "frm_project": "800x400",
    },
    "horizontal_sashes": [(1, 250)],
}


def read_config() -> TomlConfig:
    """Return the config file."""
    return TomlConfig(path=CONFIG_PATH, defaults=DEFAULT_CONFIG)


def save_config(config: TomlConfig) -> TomlConfig | None:
    result = config.save()
    if result != config.STATUS_OK:
        return None
    config = TomlConfig(CONFIG_PATH)
    return config


config = read_config()
