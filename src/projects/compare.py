"""Compare the files in two directories."""
from pathlib import Path

from projects.config import config


def compare(source_dir: str, env_dir: str) -> list[str]:
    """Compare the standard and dev versions of the projects."""
    # comparison is a dict keyed on file name
    # each element contains 'project' and 'env' entries if the file exists in
    # the relevant directories
    comparison = {}
    comparison = _build_comparison(comparison, source_dir, 'project')
    comparison = _build_comparison(comparison, env_dir, 'env')

    missing = _compare_existence(comparison)
    mismatches = _compare_contents(comparison)
    return (missing, mismatches)


def _compare_existence(comparison: dict) -> list:
    missing = []
    for name, files in comparison.items():
        if 'project' not in files:
            missing.append((name, ''))
        if 'env' not in files:
            missing.append(('', name))
    return missing


def _compare_contents(comparison: dict) -> list:
    mismatches = []
    for name, files in comparison.items():
        if 'project' in files and 'env' in files:
            contents_0 = _file_contents(files['project'])
            contents_1 = _file_contents(files['env'])
            if contents_0 != contents_1:
                mismatches.append(name)
    return mismatches


def _file_contents(path: str) -> str:
    if not path.is_file():
        file_list = list(path.iterdir())
        return len(file_list)
    with open(path, 'r', encoding='utf-8') as f_contents:
        return f_contents.read()


def _build_comparison(
        comparison: dict, search_path: str, location: str) -> dict:
    # pylint: disable=no-member)
    search_dir = Path(search_path)
    file_list = []
    try:
        file_list.extend(
            name
            for name in search_dir.iterdir()
            if name.is_file() or name.is_dir()
        )
    except FileNotFoundError:
        return {str(search_dir): 'xxx'}

    # try:
    #     file_list = [name for name in search_dir.iterdir()
    #                  if name.is_file() or name.is_dir()]
    # except FileNotFoundError:
    #     return {}

    for path in file_list:
        file_name = path.name
        if file_name in config.ignore:
            continue
        if file_name not in comparison:
            comparison[file_name] = {}

        comparison[file_name][location] = path
    return comparison
