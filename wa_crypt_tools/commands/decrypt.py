
import os
import sys
import subprocess
import argparse
from typing import Optional

from wa_crypt_tools.config import Config, load_config, merge_args_with_config
from wa_crypt_tools.env_utils import ensure_venv, get_venv_path


def decrypt_database(
    config: Config,
    input_dir: Optional[str] = None,
    key: Optional[str] = None
) -> int:
    """
    Decrypts the WhatsApp database using a local virtualenv.
    Returns 0 on success, 1 on failure.
    """
    print("--- WhatsApp Database Decrypter (Python) ---")

    dry_run = config.get('dry_run', False)

    # Resolve Key
    key_hex = key or config.get('key')
    if not key_hex:
        print("Error: 'key' is required (via CLI or config.json).")
        return 1

    if len(key_hex) != 64:
        print("Warning: Key does not look like a 64-digit hex string. "
              "Attempting anyway...")

    # Resolve Input Directory
    # Priority: Explicit input -> Config input -> Config output -> Default
    input_dir_base = input_dir or config.get('input') or config.get('output')

    if not input_dir_base:
        # Fallback to current directory or output?
        # In wa_tool.py fallback is args.output, which defaults to ./output
        input_dir_base = os.path.join(os.getcwd(), "output")

    # Ensure absolute path
    input_dir_base = os.path.abspath(input_dir_base)

    # Potential locations for crypt files
    db_folder = os.path.join(input_dir_base, "WhatsApp", "Databases")
    backup_folder = os.path.join(input_dir_base, "WhatsApp", "Backups")

    # 1. Decrypt msgstore
    msgstore_crypt = os.path.join(db_folder, "msgstore.db.crypt15")
    # Output to ROOT input_dir_base (matching best practice/wa_tool behavior)
    msgstore_out = os.path.join(input_dir_base, "msgstore.db")

    if not os.path.exists(msgstore_crypt):
        if not dry_run:
            print(f"Warning: Main database not found at {msgstore_crypt}")
    else:
        print(f"Found msgstore: {msgstore_crypt}")

    # Setup Venv
    if dry_run:
        print("[DRY-RUN] Would ensure virtual environment existence.")
    else:
        ensure_venv()

    # Decrypt
    # Prepare decryptor path
    venv_path = get_venv_path()
    wadecrypt_path = os.path.join(venv_path, "bin", "wadecrypt")

    # Helper for decryption
    def perform_decrypt(input_f: str, output_f: str, name: str) -> None:
        if not os.path.exists(input_f):
            return

        print(f"Decrypting {name}...")
        if dry_run:
            print(f"[DRY-RUN] Would run: {wadecrypt_path} <KEY> {input_f} {output_f}")
        else:
            try:
                subprocess.check_call([wadecrypt_path, key_hex, input_f, output_f])
                print(f"Success! {name} decrypted to: {output_f}")
            except subprocess.CalledProcessError:
                print(f"Error: Failed to decrypt {name}.")

    # Run decryptions
    perform_decrypt(msgstore_crypt, msgstore_out, "msgstore.db")

    # 2. Decrypt wa.db
    # Look in Databases and Backups
    wadb_crypt_paths = [
        os.path.join(db_folder, "wa.db.crypt15"),
        os.path.join(backup_folder, "wa.db.crypt15")
    ]
    wadb_crypt = None
    for p in wadb_crypt_paths:
        if os.path.exists(p):
            wadb_crypt = p
            break

    if wadb_crypt:
        print(f"Found wa.db at: {wadb_crypt}")
        wadb_out = os.path.join(input_dir_base, "wa.db")
        perform_decrypt(wadb_crypt, wadb_out, "wa.db")
    else:
        if not dry_run:
            print("wa.db.crypt15 not found. Skipping wa.db decryption.")

    return 0


def run(args: argparse.Namespace) -> int:
    """
    Entry point for the decrypt command invoked from CLI.
    """
    config: Config = {}
    if hasattr(args, 'input'):
        config['input'] = args.input
    if hasattr(args, 'key'):
        config['key'] = args.key

    # Note: args.input and args.key might be None if not passed,
    # relying on config or merge_args_with_config if called from main.

    return decrypt_database(
        config,
        getattr(args, 'input', None),
        getattr(args, 'key', None)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decrypt WhatsApp database")
    parser.add_argument(
        "key", help="64-digit hex key", nargs='?', default=None
    )
    parser.add_argument("--input", "-i", help="Base input directory")
    parser.add_argument("--config", "-c", help="Config file path")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    config = load_config(args.config)
    merge_args_with_config(args, config)

    sys.exit(run(args))
