
import os
import subprocess
from pathlib import Path
from typing import Optional

from ..adb import get_adb_base


def push_whatsapp(input_path: Path, device_id: Optional[str] = None) -> bool:
    """
    Pushes local WhatsApp folder to a connected Android device.

    Args:
        input_path: Path to the directory CONTAINING the 'WhatsApp' folder/file
                    (e.g. if input_path is .../output, we look for
                     .../output/WhatsApp)
        device_id: Optional ADB serial ID.

    Returns:
        bool: True on success, False on failure.
    """
    input_str = str(input_path.resolve())
    local_wa = os.path.join(input_str, "WhatsApp")

    if not os.path.exists(local_wa):
        print(f"Error: Local WhatsApp folder not found at {local_wa}")
        print("       Ensure your input directory contains a 'WhatsApp' "
              "folder.")
        return False

    print(f"Source: {local_wa}")

    adb_base = get_adb_base(device_id)
    if device_id:
        print(f"Target Device: {device_id}")

    # 1. Check ADB
    print("[1/3] Checking ADB connection...")
    try:
        subprocess.check_call(
            adb_base + ["get-state"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        print("Error: No device connected via ADB. Please connect your phone "
              "and enable USB debugging.")
        return False

    # 2. Define Target
    target_base = "/sdcard/Android/media/com.whatsapp"
    print(f"Target Base: {target_base}")

    # 3. Create target directory
    print("[2/3] Preparing target directory...")
    try:
        subprocess.check_call(adb_base + ["shell", f"mkdir -p {target_base}"])
    except subprocess.CalledProcessError:
        print(f"Error: Could not create target directory {target_base}")
        return False

    # 4. Push
    print("[3/3] Pushing files... (This may take a while)")
    try:
        # We push 'local_wa' (the folder) into 'target_base'.
        # ADB push source dest -> if source is folder, it goes INSIDE dest
        # or replaces dest?
        # wa_tool.py did:
        # subprocess.check_call(adb_base + ["push", local_wa, target_base])
        # if target_base exists, 'WhatsApp' folder will be created inside
        # 'target_base'.
        # resulting in /sdcard/Android/media/com.whatsapp/WhatsApp
        subprocess.check_call(adb_base + ["push", local_wa, target_base])
        print("Push completed successfully.")
    except subprocess.CalledProcessError:
        print("Error during push.")
        return False

    print("----------------------------")
    print("Success! Data pushed to device.")
    print("Next steps:")
    print("1. Force Stop WhatsApp on the device.")
    print("2. Clear Cache (and maybe Data) for WhatsApp.")
    print("3. Open WhatsApp and verify restoration.")
    return True
