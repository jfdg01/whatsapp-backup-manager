# WhatsApp Tool User Manual

## Setup
1. **ADB**: Ensure your Android device is connected with USB Debugging enabled.
2. **Key**: Have your 64-digit hexadecimal WhatsApp key ready (or put it in `config.json`).

## Commands

All commands are run using the `wa_crypt_tools` module. Global arguments (like `--key`) should generally precede the subcommand.

### 1. Pull
Backs up `WhatsApp` folder (Databases, Media) and `contacts.vcf` from the device.
```bash
python3 -m wa_crypt_tools pull
# Or with a custom output directory:
python3 -m wa_crypt_tools --output ./custom_output pull
```

### 2. Decrypt
Decrypts `msgstore.db.crypt15` and `wa.db.crypt15`.
```bash
python3 -m wa_crypt_tools --key <YOUR_64_CHAR_HEX_KEY> decrypt
# If input is different from default/config:
python3 -m wa_crypt_tools --key <YOUR_64_CHAR_HEX_KEY> decrypt --input ./output
```

### 3. Push (Restore)
Pushes the local `WhatsApp` folder to the device (`/sdcard/Android/media/com.whatsapp/WhatsApp`).
```bash
python3 -m wa_crypt_tools push
# If input is different from default/config:
python3 -m wa_crypt_tools push --input ./output
```

### 4. Convert Contacts
Converts `contacts.vcf` to a JSON format.
```bash
python3 -m wa_crypt_tools convert --input ./output/contacts.vcf --output ./output/contacts.json
```

### 5. All (Orchestrator)
Runs **Pull** → **Decrypt** → **Convert** → **Push** in one go.
```bash
python3 -m wa_crypt_tools --key <YOUR_64_CHAR_HEX_KEY> all
```

### Global Options
These can be passed before any subcommand:
- `--config <path>`: Path to a JSON config file (default: `config.json`).
- `--output <dir>`: Base directory for output operations.
- `--device <id>`: Specific ADB device ID (if multiple connected).
- `--key <hex>`: 64-digit hex key for decryption.
- `--dry-run`: Simulate actions without executing them (don't pull, push, or decrypt).
