# buttons.py
import tkinter as tk
from collections.abc import Callable

from psiutils.buttons import ButtonFrame as ButtonFrameBase
from psiutils.buttons import IconButton as IconButtonBase

from .constants import BUTTON_CONFIG_PATH, BUTTON_ICON_PATH
from .text import Text

txt = Text()


class IconButton(IconButtonBase):
    def __init__(
        self,
        master: tk.Frame,
        text: str,
        icon: str,
        command: Callable | None = None,
        dimmable: bool = False,
        *,
        sticky: str = "",
        icon_path: str = BUTTON_ICON_PATH,
        icon_colour: str | tuple[int] = "",
        text_colour: str | tuple[int] = "",
        tag: str = "",
        **kwargs,
    ):
        super().__init__(
            master,
            text,
            icon,
            command,
            dimmable,
            sticky=sticky,
            icon_path=icon_path,
            icon_colour=icon_colour,
            text_colour=text_colour,
            tag=tag,
            **kwargs,
        )


class ButtonFrame(ButtonFrameBase):
    def __init__(
        self,
        master: tk.Frame,
        orientation: str = tk.HORIZONTAL,
        button_config_path: str = BUTTON_CONFIG_PATH,
        icon_path: str = BUTTON_ICON_PATH,
        **kwargs: dict,
    ):
        super().__init__(
            master,
            orientation,
            button_config_path,
            icon_path=icon_path,
            **kwargs,
        )
