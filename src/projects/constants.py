"""Constants for Project Management."""
from pathlib import Path
from appdirs import user_config_dir, user_data_dir


PROJECT_DIR = Path(__file__).parent.parent

# Config
APP_NAME = 'projects'
APP_TITLE = 'Project management'
AUTHOR = 'Jeff Watkins'
ICON_FILE = Path(Path(__file__).parent, 'images', 'favicon.png')

DATA_FILE = 'projects.json'

HISTORY_FILE = 'HISTORY.md'
VERSION_FILE = '_version.py'
VERSION_TEXT = '__version__'

PYPROJECT_TOML = 'pyproject.toml'
REQUIREMENTS_FILE = 'requirements.txt'

CONFIG_PATH = Path(user_config_dir(APP_NAME, AUTHOR), 'config.toml')
DATA_DIR = str(Path(user_data_dir(APP_NAME, AUTHOR)))
