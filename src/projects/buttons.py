# from psiutils.buttons import ButtonFrame as PsiButtonFrame
# from psiutils.buttons import IconButton

# from projects.constants import ICON_DIR
# from projects.text import Text

# txt = Text()

# buttons = {
#     "folder-open": ("Open here", "folder-open"),
#     "modified": ("Modified", "pencil"),
#     "not-modified": ("Mark modified", "pencil-outline"),
#     "accept": (txt.ACCEPT, "check-circle-outline"),
#     "devin": ("Devin", "devin-desktop-next"),
#     "git-push": (txt.GIT_PUSH, "git-branch"),
#     "git-apply": (txt.GIT_APPLY, "git-stash-apply"),
#     "refresh-view": (txt.REFRESH_DATABASE, "view-refresh"),
# }


# class ButtonFrame(PsiButtonFrame):
#     def __init__(
#         self,
#         *args,
#         sticky: str = "",
#         dimmable: bool = False,
#         **kwargs: dict,
#     ) -> None:
#         super().__init__(*args, **kwargs)
#         for name, button in buttons.items():
#             print(name)
#             self.icon_buttons[name] = IconButton(
#                 self, button[0], button[1], icon_path=ICON_DIR
#
#              )
# buttons.py
import os
import tkinter as tk

from dotenv import load_dotenv
from psiutils.buttons import ButtonFrame as ButtonFrameBase

load_dotenv()
ICON_IMAGE_PATH = os.getenv("ICON_IMAGE_PATH")
ICON_BUTTON_CONFIG_PATH = os.getenv("ICON_BUTTON_CONFIG_PATH")


class ButtonFrame(ButtonFrameBase):
    def __init__(
        self,
        master: tk.Frame,
        orientation: str = tk.HORIZONTAL,
        button_config_path: str = ICON_BUTTON_CONFIG_PATH,
        icon_path: str = ICON_IMAGE_PATH,
        **kwargs: dict,
    ):
        super().__init__(
            master,
            orientation,
            button_config_path,
            icon_path=icon_path,
            **kwargs,
        )
