import os
import argparse
import subprocess
from typing import Optional
from wa_crypt_tools.adb import (
    get_adb_base, run_adb_command, check_connection, AdbError
)
from wa_crypt_tools.config import Config, load_config, merge_args_with_config


def pull_data(config: Config, device_id: Optional[str] = None) -> int:
    """
    Pulls WhatsApp data from a connected Android device.
    Returns 0 on success, 1 on failure.
    """
    print("--- WhatsApp Full Folder Puller (Python) ---")

    # Resolving Output Directory
    # config['output'] should already be resolved by merge_args_with_config
    local_dest_base = config.get('output')
    if not local_dest_base:
        # Fallback shouldn't really happen if config is loaded properly
        local_dest_base = os.path.join(os.getcwd(), "output")

    dest_dir = os.path.join(local_dest_base, "WhatsApp")

    # Device ID priority: argument > config
    target_device = (
        device_id or config.get('pull_device') or config.get('device')
    )
    adb_base = get_adb_base(target_device)

    print(f"Output Directory: {local_dest_base}")
    if target_device:
        print(f"Target Device: {target_device}")

    # 1. Check ADB
    print("[1/5] Checking ADB connection...")
    if not check_connection(target_device):
        print("Error: No device connected via ADB. "
              "Please connect your phone and enable USB debugging.")
        return 1

    # Check destination
    if os.path.isdir(dest_dir) and os.listdir(dest_dir):
        print(f"Error: Destination directory {dest_dir} is not empty. "
              "Aborting to prevent overwrite.")
        return 1

    os.makedirs(os.path.join(dest_dir, "Databases"), exist_ok=True)

    # 2. Pull Contacts
    print("[2/5] Checking for contacts.vcf...")
    contacts_paths = ["/sdcard/Download/contacts.vcf", "/sdcard/contacts.vcf"]
    found_contact = None

    for path in contacts_paths:
        try:
            # Check file existence via shell
            run_adb_command(adb_base + ["shell", f"[ -f {path} ]"])
            found_contact = path
            break
        except AdbError:
            continue

    if found_contact:
        print(f"Found contacts at: {found_contact}")
        try:
            subprocess.check_call(
                adb_base + [
                    "pull",
                    found_contact,
                    os.path.join(local_dest_base, "contacts.vcf")
                ]
            )
            print("Contacts pulled successfully.")
        except subprocess.CalledProcessError:
            print("Error pulling contacts.")
    else:
        print("Warning: contacts.vcf not found in standard paths.")
        print("   To include contacts, export them to .vcf "
              "in your phone settings first.")

    # 3. Locate WhatsApp
    print("[3/5] Locating WhatsApp folder...")
    base_path = "/sdcard/Android/media/com.whatsapp/WhatsApp"
    try:
        run_adb_command(adb_base + ["shell", f"[ -d {base_path} ]"])
        print(f"Found WhatsApp folder at: {base_path}")
    except AdbError:
        print(f"Error: WhatsApp folder not found at {base_path}")
        return 1

    # 4. Pull Databases (msgstore and wa)
    print("[4/6] Pulling Databases...")

    # msgstore
    target_msgstore = "msgstore.db.crypt15"
    try:
        subprocess.check_call(
            adb_base + [
                "pull",
                f"{base_path}/Databases/{target_msgstore}",
                os.path.join(dest_dir, "Databases/")
            ],
            stderr=subprocess.DEVNULL
        )
        print(f"Pulled {target_msgstore}")
    except subprocess.CalledProcessError:
        print(f"Warning: {target_msgstore} not found in Databases.")

    # wa.db
    target_wadb = "wa.db.crypt15"
    # Try Databases folder first
    try:
        subprocess.check_call(
            adb_base + [
                "pull",
                f"{base_path}/Databases/{target_wadb}",
                os.path.join(dest_dir, "Databases/")
            ],
            stderr=subprocess.DEVNULL
        )
        print(f"Pulled {target_wadb}")
    except subprocess.CalledProcessError:
        # Try Backups folder if not in Databases
        # (sometimes it's there per user)
        try:
            subprocess.check_call(
                adb_base + [
                    "pull",
                    f"{base_path}/Backups/{target_wadb}",
                    os.path.join(dest_dir, "Databases/")
                ],
                stderr=subprocess.DEVNULL
            )
            print(f"Pulled {target_wadb} (from Backups)")
        except subprocess.CalledProcessError:
            print(f"Warning: {target_wadb} not found in Databases or Backups.")

    # 5. Pull Backups
    print("[5/6] Pulling Backups folder...")
    try:
        subprocess.check_call(
            adb_base + ["pull", f"{base_path}/Backups", dest_dir]
        )
    except subprocess.CalledProcessError:
        print("Warning: Failed to pull Backups folder.")

    # 6. Pull Media
    print("[6/6] Pulling Media folder...")
    media_path = f"{base_path}/Media"
    try:
        subprocess.check_call(
            adb_base + ["pull", media_path, dest_dir]
        )
    except subprocess.CalledProcessError:
        print("Warning: Failed to pull Media folder.")

    print("----------------------------")
    print(f"Success! WhatsApp data pulled to: {dest_dir}")
    return 0


def run(args: argparse.Namespace) -> int:
    """
    Entry point for the pull command invoked from CLI.
    """
    # Reconstruct a partial config for the function signature
    config: Config = {}
    if hasattr(args, 'output'):
        config['output'] = args.output
    if hasattr(args, 'pull_device'):
        config['pull_device'] = args.pull_device
    if hasattr(args, 'device'):
        config['device'] = args.device

    return pull_data(config, getattr(args, 'device', None))


if __name__ == "__main__":
    # Allow running this module directly
    parser = argparse.ArgumentParser(description="Pull WhatsApp data")
    parser.add_argument("--output", "-o", help="Base download directory")
    parser.add_argument("--device", "-d", help="Device ID")
    parser.add_argument("--config", "-c", help="Config file path")

    args = parser.parse_args()

    config = load_config(args.config)
    merge_args_with_config(args, config)

    exit(run(args))
