import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any

from ..env_utils import ensure_venv, get_venv_python_path


def _internal_convert_logic(input_path: str, output_path: str) -> None:
    """
    Internal logic to parse VCF.
    This MUST be run in an environment where 'vobject' is installed.
    """
    import vobject

    print(f"Parsing {input_path}...")

    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    # Pre-process lines to handle Quoted-Printable continuations
    # and standard VCF folding
    processed_lines: List[str] = []
    skip_photo = False
    for line in lines:
        raw_line = line.rstrip('\r\n')
        if not raw_line:
            continue

        # Check if we should start skipping a PHOTO field
        if raw_line.upper().startswith('PHOTO'):
            skip_photo = True
            continue

        # If we are skipping, and the line starts with a space/tab,
        # it's a continuation of the PHOTO
        if skip_photo and (
            raw_line.startswith(' ') or raw_line.startswith('\t')
        ):
            continue
        else:
            skip_photo = False

        if processed_lines and (
            processed_lines[-1].endswith('=') or
            raw_line.startswith(' ') or
            raw_line.startswith('\t')
        ):
            if processed_lines[-1].endswith('='):
                # QP continuation: remove the '=' and append the line
                processed_lines[-1] = processed_lines[-1][:-1] + raw_line
            else:
                # Standard folding: remove the leading space/tab and append
                processed_lines[-1] = (
                    processed_lines[-1] + raw_line.lstrip(' \t')
                )
        else:
            processed_lines.append(raw_line)

    vcf_content = '\n'.join(processed_lines)

    cards = vobject.readComponents(vcf_content)
    result: List[Dict[str, Any]] = []
    for card in cards:
        card_data: Dict[str, Any] = {}
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


def convert_vcf(input_path: str, output_path: str, dry_run: bool = False) -> int:
    """
    Converts contacts.vcf to contacts.json using the venv.
    Returns exit code (0 for success, 1 for failure).
    """
    print("--- WhatsApp VCF to JSON Converter ---")

    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return 1

    if dry_run:
        print(f"[DRY-RUN] Would convert {input_path} to {output_path}")
        return 0

    # Ensure venv exists and has vobject
    ensure_venv()

    venv_python = get_venv_python_path()

    # Get the module name for the internal command
    # We execute this module itself with a special flag
    module_name = "wa_crypt_tools.commands.convert"

    cmd = [
        venv_python,
        "-m", module_name,
        "--internal",
        "--input", str(Path(input_path).absolute()),
        "--output", str(Path(output_path).absolute())
    ]

    try:
        subprocess.check_call(cmd)
        return 0
    except subprocess.CalledProcessError:
        print("Error during VCF conversion.")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--internal", action="store_true", help="Run internal implementation"
    )
    parser.add_argument("--input", "-i", required=True)
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.internal:
        try:
            _internal_convert_logic(args.input, args.output)
            sys.exit(0)
        except Exception as e:
            print(f"Internal Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # Standard CLI usage of this module directly
        sys.exit(convert_vcf(args.input, args.output, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
