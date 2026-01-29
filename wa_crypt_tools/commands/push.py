
import os
import subprocess
import argparse
from pathlib import Path
from typing import Optional

from ..adb import get_adb_base


def push_whatsapp(
    input_path: Path,
    device_id: Optional[str] = None,
    dry_run: bool = False
) -> bool:
    """
    Pushes local WhatsApp folder to a connected Android device.

    Args:
        input_path: Path to the directory CONTAINING the 'WhatsApp' folder/file
                    (e.g. if input_path is .../output, we look for
                     .../output/WhatsApp)
        device_id: Optional ADB serial ID.
        dry_run: If True, simulate the push without executing actual commands.

    Returns:
        bool: True on success, False on failure.
    """
    input_str = str(input_path.resolve())
    local_wa = os.path.join(input_str, "WhatsApp")

    if not os.path.exists(local_wa):
        if dry_run:
            print(f"[DRY-RUN] Local WhatsApp folder not found at {local_wa}. "
                  "Assuming it was created in a previous step.")
        else:
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
    if dry_run:
        print(f"[DRY-RUN] Would run: adb shell mkdir -p {target_base}")
    else:
        try:
            subprocess.check_call(adb_base + ["shell", f"mkdir -p {target_base}"])
        except subprocess.CalledProcessError:
            print(f"Error: Could not create target directory {target_base}")
            return False

    # 4. Push
    print("[3/3] Pushing files... (This may take a while)")
    if dry_run:
        print(f"[DRY-RUN] Would push {local_wa} to {target_base}")
    else:
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


def run(args: argparse.Namespace) -> int:
    """Entry point for the push command invoked from CLI."""
    input_path = Path(args.input or "output").resolve()
    success = push_whatsapp(
        input_path,
        args.device,
        dry_run=args.dry_run
    )
    return 0 if success else 1


if __name__ == "__main__":
    import argparse
    from wa_crypt_tools.config import load_config, merge_args_with_config
    
    parser = argparse.ArgumentParser(description="Push WhatsApp data to device")
    parser.add_argument("--input", "-i", help="Base input directory containing WhatsApp folder")
    parser.add_argument("--device", "-d", help="Specific device ID")
    parser.add_argument("--config", "-c", help="Config file path")
    parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()
    config = load_config(args.config)
    merge_args_with_config(args, config)
    
    exit(run(args))
