import os
import json
import sys
import argparse
from typing import TypedDict, Optional


class Config(TypedDict, total=False):
    output: Optional[str]
    input: Optional[str]
    key: Optional[str]
    device: Optional[str]
    pull_device: Optional[str]
    push_device: Optional[str]
    dry_run: Optional[bool]


CONFIG_FILENAME = "config.json"


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Loads configuration from a JSON file.
    If config_path is not provided, looks for config.json in CWD.
    """
    if not config_path:
        config_path = os.path.join(os.getcwd(), CONFIG_FILENAME)

    if not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}")
        print("A config.json file is required.")
        sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Config file {config_path} is not valid JSON.")
        sys.exit(1)


def resolve_path(
    path_str: Optional[str],
    base_dir: Optional[str] = None
) -> Optional[str]:
    """
    Resolves a path string.
    If absolute, returns as is.
    If relative, returns resolved against base_dir (default: CWD).
    """
    if not path_str:
        return None

    if os.path.isabs(path_str):
        return path_str

    base = base_dir if base_dir else os.getcwd()
    return os.path.join(base, path_str)


def merge_args_with_config(args: argparse.Namespace, config: Config) -> None:
    """
    Merges configuration values into the arguments namespace.
    Modifies args in-place.
    """
    # 1. Resolve 'output'
    cli_output: Optional[str] = getattr(args, 'output', None)
    config_output: Optional[str] = config.get('output')

    final_output = cli_output or config_output

    if not final_output:
        final_output = os.path.join(os.getcwd(), "output")
    else:
        final_output = resolve_path(final_output)

    args.output = final_output

    # 2. Resolve 'input'
    if hasattr(args, 'input'):
        cli_input: Optional[str] = args.input
        config_input: Optional[str] = config.get('input')

        final_input = cli_input or config_input

        # Fallback to output if input is not set
        if not final_input:
            final_input = args.output
        else:
            final_input = resolve_path(final_input)

        args.input = final_input

    # 3. Resolve 'key'
    if hasattr(args, 'key') and args.key is None:
        args.key = config.get('key')

    # Validation (only if the arg exists)
    if hasattr(args, 'key') and not args.key:
        print("Error: 'key' is required (via CLI or config.json).")
        sys.exit(1)

    # 4. Resolve 'device'
    if hasattr(args, 'device') and args.device is None:
        args.device = config.get('device')

    # 5. Resolve 'pull_device' and 'push_device'
    if hasattr(args, 'pull_device') and args.pull_device is None:
        args.pull_device = config.get('pull_device')

    if hasattr(args, 'push_device') and args.push_device is None:
        args.push_device = config.get('push_device')

    # 6. Resolve 'dry_run'
    if hasattr(args, 'dry_run') and args.dry_run is None:
        args.dry_run = config.get('dry_run', False)
