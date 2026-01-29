import os
import sys
import subprocess
from typing import Optional

VENV_NAME = "wa-crypt-tools"


def get_venv_path(base_dir: Optional[str] = None) -> str:
    if base_dir is None:
        base_dir = os.getcwd()
    return os.path.join(base_dir, VENV_NAME)


def get_venv_python_path(base_dir: Optional[str] = None) -> str:
    venv_path = get_venv_path(base_dir)
    return os.path.join(venv_path, "bin", "python")


def ensure_venv(base_dir: Optional[str] = None) -> None:
    """Ensures the virtual environment exists and has required packages."""
    venv_path = get_venv_path(base_dir)

    if not os.path.isdir(venv_path):
        print(f"Creating virtual environment '{VENV_NAME}' at {venv_path}...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_path])

    # We always attempt to install/upgrade deps to ensure they are present
    # Using pip in quiet mode to avoid noise if already installed
    pip_path = os.path.join(venv_path, "bin", "pip")

    # Check if we need to install/update (naive check: just run install)
    # Silence output unless error
    try:
        pkgs = ["wa-crypt-tools", "vobject", "mypy", "flake8"]
        subprocess.check_call(
            [pip_path, "install"] + pkgs,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        print("Warning: Failed to install dependencies in venv.")
