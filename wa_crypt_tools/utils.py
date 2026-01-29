import os
import sys


def get_script_dir() -> str:
    """
    Returns the directory of the main script or executable.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.getcwd()
