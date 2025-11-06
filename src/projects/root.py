import sys
import tkinter as tk
import contextlib

from psiutils.widgets import get_styles


from projects.constants import ICON_FILE
from projects.forms.frm_main import MainFrame
from projects.module_caller import ModuleCaller


class Root():
    def __init__(self) -> None:
        self.root = tk.Tk()

        self.show()

    def show(self) -> None:
        """Create the app's root and loop."""
        root = self.root
        root.option_add('*tearOff', False)
        with contextlib.suppress(tk.TclError):
            root.iconphoto(False, tk.PhotoImage(file=ICON_FILE))
        root.protocol("WM_DELETE_WINDOW", root.destroy)

        get_styles()

        dlg = None
        if len(sys.argv) > 1:
            module = sys.argv[1]
            dlg = ModuleCaller(root, module)

        if not dlg or dlg.invalid:
            MainFrame(self)

        root.mainloop()
