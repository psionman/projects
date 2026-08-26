"""Main procedure for package"""

import argparse
import sys
import tkinter as tk

from psiutils.utilities import display_icon
from psiutils.widgets import get_styles

from projects import __app_name__, __version__, logger
from projects.constants import APP_TITLE, ICON_FILE
from projects.data_store import store
from projects.forms.frm_main import AppFrame
from projects.module_caller import ModuleCaller


def main() -> None:
    """Call the Root loop."""
    # initialize the project store
    _ = store

    parser = argparse.ArgumentParser(description=APP_TITLE)
    parser.add_argument(
        "module", nargs="?", default=None, help="Module to load"
    )
    args = parser.parse_args()

    root = tk.Tk()
    root.title(APP_TITLE)
    display_icon(root, ICON_FILE, ignore_error=True)

    root.protocol("WM_DELETE_WINDOW", root.destroy)

    get_styles()

    if args.module:
        try:
            dlg = ModuleCaller(root, args.module)
            if dlg.invalid:
                logger.error("Invalid module", module=args.module)
                AppFrame(root)
        except Exception as e:
            logger.error(f"Failed to load module '{args.module}'", error=e)
            AppFrame(root)
    else:
        AppFrame(root)

    root.mainloop()


if __name__ == "__main__":
    if "--version" in sys.argv:
        print(f"{__app_name__}. Version: {__version__}")
        sys.exit(0)
    main()
