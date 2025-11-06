"""Log any imports that do not have an explicit package reference."""

import os
from pathlib import Path
import re

from projects import logger


TEST_DIR = '/home/jeff/projects/utilities/projects/src/projects'

STARTS_WITH = ('from', 'import')
IMPORTS = (
    'psiutils',
)


def check_imports(package: str, source_dir: str) -> None:
    modules = _get_modules(source_dir)
    for path in modules.values():
        text = _get_text(path)
        _check_imports(list(modules), package, source_dir, path.stem, text)


def _get_modules(module_dir: str) -> dict:
    modules = {}
    for directory_name, subdir_list, file_list in os.walk(module_dir):
        del subdir_list
        for file_name in file_list:
            file_path = Path(directory_name, file_name)
            if file_path.suffix == '.py':
                modules[file_path.stem] = file_path
    return modules


def _get_text(path: str) -> list:
    with open(path, 'r', encoding='utf-8') as f_module:
        return f_module.read().split('\n')


def _check_imports(
        modules: list,
        package: str,
        source_dir: str,
        module_name: str,
        text: list) -> None:
    """Log any imports that do not have an explicit package reference."""
    for index, line in enumerate(text):
        import_line = any(line.startswith(start) for start in STARTS_WITH)
        if not import_line:
            continue

        imported_package = (line.split()[1]).split('.')[0]
        if imported_package in IMPORTS:
            continue

        for module in modules:
            module_re = rf'\b{module}\b'
            if re.search(module_re, line) and f'{package}.' not in line:
                print(module_name, module, line)
                logger.warning(
                    (f'Missing package definition in '
                     f'{source_dir}/{module_name}: {index+1}'))


if __name__ == "__main__":
    check_imports('package', TEST_DIR)
