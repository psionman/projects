from psiutils.buttons import ButtonFrame as PsiButtonFrame
from psiutils.buttons import IconButton

from projects.constants import ICON_DIR
from projects.text import Text

txt = Text()

buttons = {
    "console": ("Konsole", "console"),
    "help": ("Help", "help"),
    "folder-open": ("Open here", "folder-open"),
    "windsurf": (txt.WINDSURF, "windsurf"),
}


class ButtonFrame(PsiButtonFrame):
    def __init__(
        self,
        *args,
        sticky: str = "",
        dimmable: bool = False,
        **kwargs: dict,
    ) -> None:
        super().__init__(*args, **kwargs)
        for name, button in buttons.items():
            self.icon_buttons[name] = IconButton(
                self, button[0], button[1], icon_path=ICON_DIR
            )
