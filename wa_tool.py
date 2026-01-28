#!/usr/bin/env python3
import argparse
import time
import os
import subprocess
import sys
import shutil
from pathlib import Path

import json

# --- Constants ---
# Determine script directory to make it portable
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

VENV_NAME = "wa-crypt-tools"
VENV_PATH = os.path.join(SCRIPT_DIR, VENV_NAME)
CONFIG_FILENAME = "config.json"

def load_config(config_path=None):
    # If config_path is not provided, look for config.json in SCRIPT_DIR
    if not config_path:
        config_path = os.path.join(SCRIPT_DIR, CONFIG_FILENAME)
        
    if not os.path.exists(config_path):
        # Enforce existence if it's the default file or explicit arg
        print(f"Error: Config file not found at {config_path}")
        print("A config.json file is required.")
        sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Config file {config_path} is not valid JSON.")
        sys.exit(1)

def resolve_path(path_str):
    """
    Resolves a path string. 
    If absolute, returns as is.
    If relative, returns resolved against SCRIPT_DIR.
    """
    if not path_str:
        return None
    p = Path(path_str)
    if p.is_absolute():
        return str(p)
    return os.path.join(SCRIPT_DIR, path_str)

def merge_args_with_config(args, config):
    # 1. Resolve 'output'
    # Priority: CLI -> Config -> Default (SCRIPT_DIR/output)
    
    cli_output = getattr(args, 'output', None)
    config_output = config.get('output')
    
    final_output = cli_output or config_output
    
    if not final_output:
        final_output = os.path.join(SCRIPT_DIR, "output")
    else:
        final_output = resolve_path(final_output)
        
    args.output = final_output
    
    # 2. Resolve 'input' (for decrypt)
    # Priority: CLI -> Config input -> Config output -> Default (args.output base)
    
    if hasattr(args, 'input'):
        cli_input = args.input
        config_input = config.get('input')
        
        final_input = cli_input or config_input
        
        # Fallback to output if input is not set (common scenario)
        if not final_input:
             # args.output is already resolved and absolute by now
             final_input = args.output
        else:
             final_input = resolve_path(final_input)
             
        args.input = final_input

    # 3. Resolve 'key'
    if hasattr(args, 'key') and args.key is None:
        args.key = config.get('key')
        
    # Validation
    if hasattr(args, 'key') and not args.key:
         print("Error: 'key' is required (via CLI or config.json).")
         sys.exit(1)


def ensure_venv():
    """Ensures the virtual environment exists and has required packages."""
    if not os.path.isdir(VENV_PATH):
        print(f"Creating virtual environment '{VENV_NAME}'...")
        subprocess.check_call([sys.executable, "-m", "venv", VENV_PATH])
    
    # We always attempt to install/upgrade deps to ensure they are present
    # Using pip in quiet mode to avoid noise if already installed
    pip_path = os.path.join(VENV_PATH, "bin", "pip")
    
    # Check if we need to install/update (naive check: just run install)
    # Silence output unless error
    try:
        # Installing both wa-crypt-tools and vobject
        # Using subprocess to install
        subprocess.check_call([pip_path, "install", "wa-crypt-tools", "vobject"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Warning: Failed to install dependencies in venv.")
        # We continue, as they might be there


# --- Subcommands ---

def measure_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            end_time = time.time()
            print(f"Total time for '{func.__name__}': {end_time - start_time:.2f} seconds.")
    return wrapper

def _internal_parse_vcf_logic(vcf_path, output_path):
    """
    Internal logic to parse VCF. 
    This MUST be run in an environment where 'vobject' is installed.
    """
    import vobject
    
    print(f"Parsing {vcf_path}...")
    
    with open(vcf_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    # Pre-process lines to handle Quoted-Printable continuations and standard VCF folding
    processed_lines = []
    skip_photo = False
    for line in lines:
        raw_line = line.rstrip('\r\n')
        if not raw_line:
            continue
            
        # Check if we should start skipping a PHOTO field
        if raw_line.upper().startswith('PHOTO'):
            skip_photo = True
            continue
            
        # If we are skipping, and the line starts with a space/tab, it's a continuation of the PHOTO
        if skip_photo and (raw_line.startswith(' ') or raw_line.startswith('\t')):
            continue
        else:
            skip_photo = False

        if processed_lines and (processed_lines[-1].endswith('=') or raw_line.startswith(' ') or raw_line.startswith('\t')):
            if processed_lines[-1].endswith('='):
                # QP continuation: remove the '=' and append the line
                processed_lines[-1] = processed_lines[-1][:-1] + raw_line
            else:
                # Standard folding: remove the leading space/tab and append
                processed_lines[-1] = processed_lines[-1] + raw_line.lstrip(' \t')
        else:
            processed_lines.append(raw_line)
            
    vcf_content = '\n'.join(processed_lines)
    
    cards = vobject.readComponents(vcf_content)
    result = []
    for card in cards:
        card_data = {}
        if hasattr(card, 'fn'):
            card_data['name'] = card.fn.value
        
        card_data['phones'] = []
        if hasattr(card, 'tel'):
            for tel in card.tel_list:
                card_data['phones'].append({
                    'type': getattr(tel, 'type_param', ['unknown']),
                    'number': tel.value
                })
        
        if hasattr(card, 'email'):
            card_data['emails'] = [e.value for e in card.email_list]
            
        result.append(card_data)
        
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully converted to {output_path}")

@measure_time
def cmd_convert_vcf(args):
    """Converts contacts.vcf to contacts.json using the venv."""
    print("--- WhatsApp VCF to JSON Converter ---")
    
    ensure_venv()
    
    input_path = args.input
    output_path = args.output
    
    if not input_path:
        # Default input: args.output/contacts.vcf (since args.output acts as base dir if not file)
        # But wait, args.output handling in merge_args_with_config is tricky.
        # Let's rely on what passes in.
        pass
        
    # We need to re-resolve paths possibly if they are defaults
    # But let's assume valid paths for now or check existence
    
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return 1
        
    # Python executable in venv
    venv_python = os.path.join(VENV_PATH, "bin", "python")
    
    # Run the internal command
    # We pass the Absolute paths to ensure consistency
    cmd = [
        venv_python, 
        sys.argv[0], # The script itself
        "_internal_parse_vcf", 
        "--input", str(Path(input_path).absolute()),
        "--output", str(Path(output_path).absolute())
    ]
    
    try:
        subprocess.check_call(cmd)
        return 0
    except subprocess.CalledProcessError:
        print("Error during VCF conversion.")
        return 1

def cmd_internal_parse_vcf_entry(args):
    """Entry point for the internal VCF parsing (called from venv)."""
    try:
        _internal_parse_vcf_logic(args.input, args.output)
        return 0
    except Exception as e:
        print(f"Internal Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


@measure_time
def cmd_pull(args):
    """Pulls WhatsApp data from a connected Android device."""
    print("--- WhatsApp Full Folder Puller (Python) ---")
    
    # Directory should already be resolved in merge_args_with_config
    local_dest_base = args.output 
    dest_dir = os.path.join(local_dest_base, "WhatsApp")
    
    print(f"Output Directory: {local_dest_base}")

    # 1. Check ADB
    print("[1/5] Checking ADB connection...")
    try:
        subprocess.check_call(["adb", "get-state"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Error: No device connected via ADB. Please connect your phone and enable USB debugging.")
        return 1

    # Check destination
    if os.path.isdir(dest_dir) and os.listdir(dest_dir):
         print(f"Error: Destination directory {dest_dir} is not empty. Aborting to prevent overwrite.")
         return 1
    
    os.makedirs(os.path.join(dest_dir, "Databases"), exist_ok=True)

    # 2. Pull Contacts
    print("[2/5] Checking for contacts.vcf...")
    contacts_paths = ["/sdcard/Download/contacts.vcf", "/sdcard/contacts.vcf"]
    found_contact = None
    
    for path in contacts_paths:
        try:
            # Check file existence via shell
            subprocess.check_call(["adb", "shell", f"[ -f {path} ]"])
            found_contact = path
            break
        except subprocess.CalledProcessError:
            continue
            
    if found_contact:
        print(f"Found contacts at: {found_contact}")
        # Output contacts directly to base output dir
        subprocess.check_call(["adb", "pull", found_contact, os.path.join(local_dest_base, "contacts.vcf")])
        print("Contacts pulled successfully.")
    else:
        print("Warning: contacts.vcf not found in standard paths.")
        print("   To include contacts, export them to .vcf in your phone settings first.")

    # 3. Locate WhatsApp
    print("[3/5] Locating WhatsApp folder...")
    base_path = "/sdcard/Android/media/com.whatsapp/WhatsApp"
    try:
         subprocess.check_call(["adb", "shell", f"[ -d {base_path} ]"])
         print(f"Found WhatsApp folder at: {base_path}")
    except subprocess.CalledProcessError:
         print(f"Error: WhatsApp folder not found at {base_path}")
         return 1

    # 4. Pull Database
    # 4. Pull Databases (msgstore and wa)
    print(f"[4/6] Pulling Databases...")
    
    # msgstore
    target_msgstore = "msgstore.db.crypt15"
    try:
        subprocess.check_call(["adb", "pull", f"{base_path}/Databases/{target_msgstore}", os.path.join(dest_dir, "Databases/")], stderr=subprocess.DEVNULL)
        print(f"Pulled {target_msgstore}")
    except subprocess.CalledProcessError:
        print(f"Warning: {target_msgstore} not found in Databases.")

    # wa.db
    target_wadb = "wa.db.crypt15"
    # Try Databases folder first
    try:
        subprocess.check_call(["adb", "pull", f"{base_path}/Databases/{target_wadb}", os.path.join(dest_dir, "Databases/")], stderr=subprocess.DEVNULL)
        print(f"Pulled {target_wadb}")
    except subprocess.CalledProcessError:
        # Try Backups folder if not in Databases (sometimes it's there per user)
        try:
             subprocess.check_call(["adb", "pull", f"{base_path}/Backups/{target_wadb}", os.path.join(dest_dir, "Databases/")], stderr=subprocess.DEVNULL)
             print(f"Pulled {target_wadb} (from Backups)")
        except subprocess.CalledProcessError:
             print(f"Warning: {target_wadb} not found in Databases or Backups.")

    # 5. Pull Backups
    print("[5/6] Pulling Backups folder...")
    subprocess.check_call(["adb", "pull", f"{base_path}/Backups", dest_dir])

    # 6. Pull Media
    print("[6/6] Pulling Media folder...")
    media_path = f"{base_path}/Media"
    subprocess.check_call(["adb", "pull", media_path, dest_dir])
    
    print("----------------------------")
    print(f"Success! WhatsApp data pulled to: {dest_dir}")
    return 0


@measure_time
def cmd_decrypt(args):
    """Decrypts the WhatsApp database using a local virtualenv."""
    print("--- WhatsApp Database Decrypter (Python) ---")
    
    key_hex = args.key
    # Key existence checked in merge_args
    
    if len(key_hex) != 64:
         print("Warning: Key does not look like a 64-digit hex string. Attempting anyway...")

    input_dir_base = args.input
    
    # Potential locations for crypt files
    db_folder = os.path.join(input_dir_base, "WhatsApp", "Databases")
    backup_folder = os.path.join(input_dir_base, "WhatsApp", "Backups")

    # 1. Decrypt msgstore
    msgstore_crypt = os.path.join(db_folder, "msgstore.db.crypt15")
    # Output to ROOT input_dir_base
    msgstore_out = os.path.join(input_dir_base, "msgstore.db")

    if not os.path.exists(msgstore_crypt):
        print(f"Warning: Main database not found at {msgstore_crypt}")
    else:
        print(f"Found msgstore: {msgstore_crypt}")

    # Setup Venv
    ensure_venv()

    # Decrypt
    # Prepare decryptor path
    wadecrypt_path = os.path.join(VENV_PATH, "bin", "wadecrypt")
    
    # Helper for decryption
    def perform_decrypt(input_f, output_f, name):
        if not os.path.exists(input_f):
            return
            
        print(f"Decrypting {name}...")
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
        print("wa.db.crypt15 not found. Skipping wa.db decryption.")
        
    return 0


@measure_time
def cmd_push(args):
    """Pushes local WhatsApp folder to a connected Android device."""
    print("--- WhatsApp Restore/Push Tool (Python) ---")
    
    # 1. Resolve Input
    # Input is already resolved by merge_args_with_config
    local_base = args.input 
    local_wa = os.path.join(local_base, "WhatsApp")
    
    if not os.path.isdir(local_wa):
        print(f"Error: Local WhatsApp folder not found at {local_wa}")
        print("       Ensure your input directory contains a 'WhatsApp' folder.")
        return 1

    print(f"Source: {local_wa}")

    # 2. Check ADB
    print("[1/3] Checking ADB connection...")
    try:
        subprocess.check_call(["adb", "get-state"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Error: No device connected via ADB. Please connect your phone and enable USB debugging.")
        return 1

    # 3. Define Target
    # Target: /sdcard/Android/media/com.whatsapp/WhatsApp
    target_base = "/sdcard/Android/media/com.whatsapp"
    target_wh = os.path.join(target_base, "WhatsApp")
    
    print(f"Target Base: {target_base}")
    
    # Check if target base exists, if not create it
    print("[2/3] Preparing target directory...")
    try:
        subprocess.check_call(["adb", "shell", f"mkdir -p {target_base}"])
    except subprocess.CalledProcessError:
        print(f"Error: Could not create target directory {target_base}")
        return 1
        
    # 4. Push
    print(f"[3/3] Pushing files... (This may take a while)")
    try:
        subprocess.check_call(["adb", "push", local_wa, target_base])
        print("Push completed successfully.")
    except subprocess.CalledProcessError:
        print("Error during push.")
        return 1
        
    print("----------------------------")
    print("Success! Data pushed to device.")
    print("Next steps:")
    print("1. Force Stop WhatsApp on the device.")
    print("2. Go to App Info -> Storage -> Clear Cache (and maybe Data if doing a full restore).")
    print("3. Open WhatsApp and proceed with the setup verifying your number.")
    print("4. It should detect the local backup.")
    return 0


@measure_time
def cmd_all(args):
    """Orchestrates pull and decrypt."""
    print("=== Auto-WhatsApp Orchestrator ===")
    
    # Pull
    print("\n>>> Running Pull...")
    # args.output is already resolved
    pull_args = argparse.Namespace(output=args.output)
    if cmd_pull(pull_args) != 0:
        print("Pull failed.")
        return 1
        
    # Decrypt
    print("\n>>> Running Decrypt...")
    # Decrypt input should match Pull output (which is now in args.output)
    decrypt_args = argparse.Namespace(key=args.key, input=args.output)
    if cmd_decrypt(decrypt_args) != 0:
        print("Decryption failed.")
        return 1
        
    print("\n>>> Running Convert VCF...")
    # Convert VCF
    # Input: output/contacts.vcf, Output: output/contacts.json
    vcf_in = os.path.join(args.output, "contacts.vcf")
    json_out = os.path.join(args.output, "contacts.json")
    
    if os.path.exists(vcf_in):
        convert_args = argparse.Namespace(input=vcf_in, output=json_out)
        if cmd_convert_vcf(convert_args) != 0:
            print("VCF Conversion failed.")
            # Non-critical, so maybe don't return 1? but let's stick to strict
            return 1
    else:
        print("contacts.vcf not found, skipping conversion.")

    print("\n=== All Done ===")
    return 0


# --- Main ---

def main():
    # Parent parser for common arguments
    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument("--config", "-c", help="Path to JSON config file (default: config.json in script dir)")

    parser = argparse.ArgumentParser(description="WhatsApp Tools (Pull & Decrypt)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Pull Command
    p_pull = subparsers.add_parser("pull", help="Pull WhatsApp data from Android", parents=[config_parser])
    p_pull.add_argument("--output", "-o", help="Base download directory (default: ./output)", default=None)

    # Decrypt Command
    p_decrypt = subparsers.add_parser("decrypt", help="Decrypt WhatsApp database", parents=[config_parser])
    p_decrypt.add_argument("key", help="64-digit hex key", nargs='?', default=None)
    p_decrypt.add_argument("--input", "-i", help="Base input directory (default: same as output)", default=None)

    # Push Command
    p_push = subparsers.add_parser("push", help="Push WhatsApp data to Android", parents=[config_parser])
    p_push.add_argument("--input", "-i", help="Base input directory containing WhatsApp folder (default: ./output)", default=None)

    # All Command
    p_all = subparsers.add_parser("all", help="Pull and Decrypt sequence", parents=[config_parser])
    p_all.add_argument("key", help="64-digit hex key", nargs='?', default=None)
    p_all.add_argument("--output", "-o", help="Base directory for operations (default: ./output)", default=None)

    # Convert VCF Command
    p_convert = subparsers.add_parser("convert-vcf", help="Convert VCF to JSON", parents=[config_parser])
    p_convert.add_argument("--input", "-i", help="Input VCF file", required=True)
    p_convert.add_argument("--output", "-o", help="Output JSON file", required=True)

    # Internal Hidden Command
    p_internal = subparsers.add_parser("_internal_parse_vcf", help=argparse.SUPPRESS, parents=[config_parser])
    p_internal.add_argument("--input", "-i", required=True)
    p_internal.add_argument("--output", "-o", required=True)

    args = parser.parse_args()
    
    # Load config (from arg or default)
    config = load_config(args.config)
    # Merge and resolve paths
    merge_args_with_config(args, config)

    if args.command == "pull":
        sys.exit(cmd_pull(args))
    elif args.command == "push":
        sys.exit(cmd_push(args))
    elif args.command == "decrypt":
        sys.exit(cmd_decrypt(args))
    elif args.command == "all":
        sys.exit(cmd_all(args))
    elif args.command == "convert-vcf":
        sys.exit(cmd_convert_vcf(args))
    elif args.command == "_internal_parse_vcf":
        sys.exit(cmd_internal_parse_vcf_entry(args))

if __name__ == "__main__":
    main()
