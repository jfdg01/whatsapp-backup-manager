import subprocess
from typing import List, Dict, Optional


class AdbError(Exception):
    """Base exception for ADB-related errors."""
    pass


def get_adb_base(device_id: Optional[str] = None) -> List[str]:
    """Returns the base adb command list, optionally with device serial."""
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    return cmd


def run_adb_command(cmd: List[str], check: bool = True) -> str:
    """Runs an ADB command and returns the output as string."""
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else "Unknown ADB error"
        raise AdbError(
            f"ADB command failed: {' '.join(cmd)}\nError: {error_msg}"
        )


def check_connection(device_id: Optional[str] = None) -> bool:
    """Checks if a specific device (or any device) is connected."""
    base = get_adb_base(device_id)
    try:
        run_adb_command(base + ["get-state"])
        return True
    except AdbError:
        return False


def get_product_model(device_id: str) -> str:
    """Attempts to get a descriptive product model for the device."""
    try:
        base = get_adb_base(device_id)
        return run_adb_command(base + ["shell", "getprop", "ro.product.model"])
    except AdbError:
        return "Unknown Model"


def list_devices() -> List[Dict[str, str]]:
    """
    Lists connected ADB devices with details.
    Returns a list of dicts: {'id': str, 'model': str, 'state': str}
    """
    try:
        output = run_adb_command(["adb", "devices", "-l"])
    except AdbError:
        return []

    lines = output.splitlines()
    if not lines:
        return []

    # Skip header "List of devices attached"
    lines = lines[1:]

    devices = []
    for line in lines:
        if not line.strip():
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        device_id = parts[0]
        state = parts[1]

        # Parse model from "model:Pixel_6 ..."
        model = "Unknown"
        for chunk in parts:
            if chunk.startswith("model:"):
                model = chunk.replace("model:", "").replace("_", " ")

        devices.append({
            "id": device_id,
            "state": state,
            "model": model
        })

    return devices
