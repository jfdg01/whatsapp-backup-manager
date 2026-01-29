import sys
import argparse
from pathlib import Path
from wa_crypt_tools.config import load_config, merge_args_with_config
from wa_crypt_tools.commands import (
    pull_data,
    push_whatsapp,
    decrypt_database,
    convert_vcf,
    run_orchestrator
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="WhatsApp Backup & Crypt Tools"
    )
    parser.add_argument(
        "--config", "-c", help="Path to config.json"
    )
    # Global overrides commonly used
    parser.add_argument(
        "--output", "-o", help="Output directory override"
    )
    parser.add_argument(
        "--device", "-d", help="ADB Device ID override"
    )
    parser.add_argument(
        "--key", "-k", help="Decryption key (64 hex)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate actions without executing them"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Pull
    p_pull = subparsers.add_parser("pull", help="Pull WhatsApp data")
    p_pull.add_argument(
        "--pull-device", help="Device ID specifically for pulling"
    )

    # Push
    p_push = subparsers.add_parser("push", help="Push WhatsApp data")
    p_push.add_argument(
        "--push-device", help="Device ID specifically for pushing"
    )
    p_push.add_argument("--input", "-i", help="Input directory to push from")

    # Decrypt
    p_decrypt = subparsers.add_parser("decrypt", help="Decrypt databases")
    p_decrypt.add_argument("--input", "-i", help="Input directory")

    # Convert
    p_convert = subparsers.add_parser("convert", help="Convert VCF to JSON")
    p_convert.add_argument(
        "--input", "-i", required=True, help="Input VCF file"
    )
    p_convert.add_argument(
        "--output", "-o", required=True, help="Output JSON file"
    )

    # All / Orchestrator
    p_all = subparsers.add_parser(
        "all", help="Run full pull->decrypt->convert->push workflow"
    )
    p_all.add_argument(
        "--pull-device", help="Device ID specifically for pulling"
    )
    p_all.add_argument(
        "--push-device", help="Device ID specifically for pushing"
    )

    args = parser.parse_args()

    # Load Config
    config = load_config(args.config)
    merge_args_with_config(args, config)

    # Sync resolved CLI overrides back to Config for subcommands that use it
    config['output'] = args.output
    if hasattr(args, 'input'):
        config['input'] = args.input
    if hasattr(args, 'key'):
        config['key'] = args.key
    if hasattr(args, 'device'):
        config['device'] = args.device
    if hasattr(args, 'pull_device'):
        config['pull_device'] = args.pull_device
    if hasattr(args, 'push_device'):
        config['push_device'] = args.push_device
    if hasattr(args, 'dry_run'):
        config['dry_run'] = args.dry_run

    # Dispatch
    if args.command == "pull":
        sys.exit(pull_data(config))
    elif args.command == "push":
        # Push expects Path and device_id, return bool
        # Input path logic: explicit arg -> config input -> config output
        # (fallback) -> cwd/output
        input_raw = (
            getattr(args, 'input', None) or
            config.get('input') or
            config.get('output')
        )
        if not input_raw:
            input_raw = "output"  # Default to 'output' folder in current dir

        input_path = Path(input_raw).resolve()
        # Device priority: specific push device -> global device ref -> None
        device_id = (
            getattr(args, 'push_device', None) or
            config.get('push_device') or
            config.get('device')
        )

        success = push_whatsapp(
            input_path,
            device_id,
            dry_run=config.get('dry_run', False)
        )
        sys.exit(0 if success else 1)

    elif args.command == "decrypt":
        # Decrypt command wrapping to match signature
        input_dir = getattr(args, 'input', None)
        sys.exit(decrypt_database(config, input_dir=input_dir))
    elif args.command == "convert":
        # Convert has a different signature (file paths, not config object
        # primarily). But we can still support it.
        sys.exit(convert_vcf(args.input, args.output))
    elif args.command == "all":
        sys.exit(run_orchestrator(config))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
