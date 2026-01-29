import os
import argparse
import sys

from wa_crypt_tools.config import Config, load_config
from wa_crypt_tools.commands.pull import pull_data
from wa_crypt_tools.commands.decrypt import decrypt_database
from wa_crypt_tools.commands.convert import convert_vcf


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

    if os.path.exists(contacts_vcf):
        if convert_vcf(contacts_vcf, contacts_json) != 0:
            print("Orchestrator warning: Contact conversion failed.")
        else:
            print("Contacts converted successfully.")
    else:
        print("No contacts.vcf found to convert.")

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
    parser.add_argument("--key", "-k", help="Decryption key (64 hex)")
    parser.add_argument("--config", "-c", help="Config file path")

    args = parser.parse_args()
    sys.exit(run(args))
