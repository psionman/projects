"""Constants for Project Management."""

from pathlib import Path

from appdirs import user_config_dir, user_data_dir
from psiutils.known_paths import resolve_path

from projects import __app_name__, __author__

PROJECT_DIR = Path(__file__).parent.parent

# File names
DATA_FILE = "projects.json"

HISTORY_FILE = "HISTORY.md"
VERSION_FILE = "_version.py"
VERSION_TEXT = "__version__"
PYPROJECT_TOML = "pyproject.toml"
REQUIREMENTS_FILE = "requirements.txt"


# General
HTML_DIR = resolve_path("html", __file__)
HELP_URI = ""

# Paths
HOME_DIR = str(Path.home())
CONFIG_PATH = Path(user_config_dir(__app_name__, __author__), "config.toml")
USER_DATA_DIR = Path(user_data_dir(__app_name__, __author__))
USER_DATA_DIR.mkdir(exist_ok=True)

ICON_FILE = Path(Path(__file__).parent, "images", "rocket-launch-outline.png")
ICON_DIR = f"{Path(__file__).parent}/icons/"
USER_DATA_FILE = Path(USER_DATA_DIR, "data.json")
CACHED_ENVS_FILE = "cached_envs.json"

# GUI
APP_TITLE = "Project management"
DEFAULT_GEOMETRY = "300x250"
