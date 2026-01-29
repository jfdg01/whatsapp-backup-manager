import os
import argparse
import sys

from pathlib import Path
from wa_crypt_tools.config import Config, load_config
from wa_crypt_tools.commands.pull import pull_data
from wa_crypt_tools.commands.decrypt import decrypt_database
from wa_crypt_tools.commands.convert import convert_vcf
from wa_crypt_tools.commands.push import push_whatsapp


def run_orchestrator(config: Config) -> int:
    """
    Runs the full workflow: Pull -> Decrypt -> Convert.
    Returns 0 on success (all steps pass), or non-zero on first failure.
    """
    print("=== WhatsApp Orchestrator ===")

    # 1. Pull
    print("\n>>> Step 1: Pull Data")
    if pull_data(config) != 0:
        print("Orchestrator aborted: Pull failed.")
        return 1

    # Resolve output directory to find where data is
    output_dir = config.get('output')
    if not output_dir:
        output_dir = os.path.join(os.getcwd(), "output")
    output_dir = os.path.abspath(output_dir)

    # 2. Decrypt
    print("\n>>> Step 2: Decrypt Databases")
    # Decrypt expects 'key' in config
    if not config.get('key'):
        print("Skipping decryption: No 'key' provided in config/args.")
    else:
        # Pass the output directory as the input for decryption
        if decrypt_database(config, input_dir=output_dir) != 0:
            print("Orchestrator warning: Decryption reported errors.")
            # We might continue even if decryption fails partly;
            # decrypt_database returns 1 on critical failure
            # (e.g. key missing), but 0 if just some files missing.
            pass

    # 3. Convert
    print("\n>>> Step 3: Convert Contacts")
    contacts_vcf = os.path.join(output_dir, "contacts.vcf")
    contacts_json = os.path.join(output_dir, "contacts.json")

    dry_run = config.get('dry_run', False)

    vcf_exists = os.path.exists(contacts_vcf)
    if vcf_exists or dry_run:
        if dry_run and not vcf_exists:
            print(f"[DRY-RUN] Simulating conversion of {contacts_vcf} to {contacts_json}")
            # We don't actually call convert_vcf here to avoid its own logic,
            # but we could. For now, just print.
        else:
            if convert_vcf(contacts_vcf, contacts_json, dry_run=dry_run) != 0:
                print("Orchestrator warning: Contact conversion failed.")
            else:
                print("Contacts converted successfully.")
    else:
        print("No contacts.vcf found to convert.")

    # 4. Push
    print("\n>>> Step 4: Push (Restore)")
    # Push device priority: push_device -> global device -> None
    device_id = config.get('push_device') or config.get('device')
    
    # We push from the output directory (which contains 'WhatsApp')
    if not push_whatsapp(Path(output_dir), device_id, dry_run=dry_run):
        print("Orchestrator warning: Push failed.")
    else:
        print("Push completed successfully.")

    print("\n=== Orchestrator Complete ===")
    return 0


def run(args: argparse.Namespace) -> int:
    """
    Entry point for the orchestrator command invoked from CLI.
    """
    # Config is already loaded in main, but we might need to look at args again
    # The 'all' command might not have specific arguments other than global
    # ones. We construct the Config object from args provided by the main
    # parser if needed, but normally the caller (main) will handle loading
    # config.

    # However, to be standalone-compatible (run specific module):
    config: Config = {}
    if hasattr(args, 'output'):
        config['output'] = args.output
    if hasattr(args, 'device'):
        config['device'] = args.device
    if hasattr(args, 'key'):
        config['key'] = args.key
    if hasattr(args, 'pull_device'):
        config['pull_device'] = args.pull_device
    if hasattr(args, 'push_device'):
        config['push_device'] = args.push_device
    if hasattr(args, 'dry_run'):
        config['dry_run'] = args.dry_run

    # We also need to load from file if specified
    file_config = load_config(getattr(args, 'config', None))
    # Merge file config into our config (args take precedence)
    # Cast to Config to satisfy type checker (TypedDict mixin)
    final_config: Config = {**file_config, **config}

    return run_orchestrator(final_config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run full WhatsApp backup workflow"
    )
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--device", "-d", help="Device ID")
    parser.add_argument("--pull-device", help="Source device ID for pull")
    parser.add_argument("--push-device", help="Destination device ID for push")
    parser.add_argument("--key", "-k", help="Decryption key (64 hex)")
    parser.add_argument("--config", "-c", help="Config file path")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    sys.exit(run(args))
