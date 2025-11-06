"""
Text module that merges psiutils.text.strings with project-level strings.

Usage:
    from text_module import Text

    txt = Text()
    print(txt.SELECT)   # Access as attribute
    print(txt.DELETE_PROMPT)
"""

from dataclasses import dataclass, field
from psiutils.text import Text as PsiText

strings = {
    'ACCEPT': 'Accept',
    'BUILD_FOR_WINDOWS': 'Build for Windows',
    'CONFIG': 'Preferences',
    'DELETE_PROMPT': 'Are you sure you wish to delete this record?',
    'EDIT_SCRIPT': 'Edit script',
    'KONSOLE': 'Konsole',
    'NOT_IN_PROJECT_DIR': 'Not working in project\'s directory',
    'RUN_SCRIPT': 'Run script',
    'SELECT': 'Select',
}


@dataclass
class Text:
    """Combines package-level (psiutils) and project-level strings.

    Attributes from `psiutils.text.strings` are loaded first, then overridden
    or extended by the local `strings` dictionary.
    """

    display: bool = field(default=False, repr=False)

    def __post_init__(self) -> None:
        """Populate the dataclass instance with string attributes."""
        # Load psiutils strings
        psi_text = PsiText()
        psi_strings = psi_text.strings
        for key, string in psi_strings.items():
            setattr(self, key, string)

        # Override or add project-level strings
        for key, string in strings.items():
            setattr(self, key, string)

        # Optionally display contents of `text`
        if self.display:
            psi_text.display(strings)
