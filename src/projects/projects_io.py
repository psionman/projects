"""I/O operations for projects.py."""
from pathlib import Path
import json

from psiutils.constants import Status
from projects import logger


def read_text_file(path: str) -> str:
    """
    Reads and returns the content of a text file.

    Args:
        path (str): The path to the text file.

    Returns:
        str: The content of the text file, or Status.ERROR
        if the file is not found.
    """
    try:
        with open(path, 'r', encoding='utf8') as f_text:
            return f_text.read()
    except FileNotFoundError:
        logger.warning(f'File not found {path}')
        return Status.ERROR


def update_file(pyproject_path: str, output: str) -> int:
    """
    Update the file with the provided output.

    Args:
        pyproject_path (str): The path to the file to be updated.
        output (str): The content to write to the file.

    Returns:
        int: The status of the update operation (Status.OK
        or Status.ERROR).
    """
    try:
        with open(
                pyproject_path, 'w', encoding='utf8') as f_output:
            f_output.write(output)
        return Status.OK
    except NotADirectoryError:
        logger.warning(f'Cannot find directory: {Path(pyproject_path).parent}')
        return Status.ERROR
    except FileNotFoundError:
        logger.warning(f'Cannot find file: {pyproject_path}')
        return Status.ERROR


def read_json_file(path: str) -> dict:
    """
    Reads and returns the JSON data from a file.

    Args:
        path (str): The path to the JSON file.

    Returns:
        dict: The JSON data read from the file, or an empty dictionary
        if the file is not found or cannot be decoded.
    """
    try:
        with open(path, 'r', encoding='utf8') as f_json:
            try:
                return json.load(f_json)
            except json.decoder.JSONDecodeError:
                return {}
    except FileNotFoundError:
        logger.warning(f'File not found {path}')
        return {}


def update_json_file(path: str, output: dict) -> int:
    """
    Update the JSON file with the provided output.

    Args:
        path (str): The path to the JSON file to be updated.
        output (dict): The JSON data to write to the file.

    Returns:
        int: The number of characters written to the file,
        or Status.ERROR if the file is not found.
    """

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf8') as f_json:
            return json.dump(output, f_json)
    except NotADirectoryError:
        logger.warning(f'Cannot find directory: {Path(path).parent}')
        return {}
