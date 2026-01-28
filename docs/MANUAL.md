# WhatsApp Tool User Manual

## Setup
1. **ADB**: Ensure your Android device is connected with USB Debugging enabled.
2. **Key**: Have your 64-digit hexadecimal WhatsApp key ready (or put it in `config.json`).

## Commands

### 1. Pull
Backs up `WhatsApp` folder (Databases, Media) and `contacts.vcf` from the device.
```bash
python3 wa_tool.py pull --output ./output
```

### 2. Decrypt
Decrypts `msgstore.db.crypt15` and `wa.db.crypt15`.
```bash
python3 wa_tool.py decrypt <YOUR_64_CHAR_HEX_KEY> --input ./output
```

### 3. Push (Restore)
Pushes the local `WhatsApp` folder to the device (`/sdcard/Android/media/com.whatsapp/WhatsApp`).
```bash
python3 wa_tool.py push --input ./output
```

### 4. Convert Contacts
Converts `contacts.vcf` to a JSON format.
```bash
python3 wa_tool.py convert-vcf --input ./output/contacts.vcf --output ./output/contacts.json
```

### 5. All (Orchestrator)
Runs **Pull** → **Decrypt** → **Convert** in one go.
```bash
python3 wa_tool.py all <YOUR_64_CHAR_HEX_KEY> --output ./output
```
