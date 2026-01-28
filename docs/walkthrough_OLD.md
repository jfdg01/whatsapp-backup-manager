# Whatsapp Backup

## Preparation

### Whatsapp 64 digit key:

To activate the 64 digit backup:

Three dots > Ajustes > Chats > (Scroll down) Copia de seguridad > (Scroll down) Copia seguridad cifrada de extremo a extremo > Otros medios (o similar) > Clave de 64 digitos

Copiar clave a KeePass

Se activa una copia de seguridad que se sube a Drive, a partir del comienzo de la subida se debería de tener la versión local ya lista para adb

### Contact creation

Due to Android security, you must first trigger the export manually, then you can pull it using ADB.

1. On your phone, open **Contacts** > **Fix & manage** (or Settings) > **Export to file**.
2. Save it to the Download folder as `contacts.vcf`.

## Getting the files from the phone

Run the `pull_whatsapp.sh` file. This will send the WhatsApp dir to the ~/Downloads folder.

## Decryption

Create a venv named `wa-crypt-tools` and download the deps: `pip install wa-crypt-tools`

Use the command `wadecrypt <key> msgstore.db.crypt15 msgstore.db` on the db. 

> Note: If you find the `wa.db.crypt15` you can also try to use it, but it didn't work for me.

# Creating the viewer

## Create the HTML way

Create a venv named `html-exporter` and install the deps: `pip install whatsapp-chat-exporter[crypt15]`

Run the command to generate the HTMLs:

```shell
 ./venv/bin/wtsexporter -m ./data -d ./data/msgstore.db -o ./whatsapp_html_output --size 10000000 --old-theme --enrich-from-vcards ./data/contacts.vcf --default-country-code 34 --no-banner -a
 ```

For testing, you can include a number `--include 655972256 ` to include that number only:

```shell
./venv/bin/wtsexporter -m ./data -d ./data/msgstore.db -o ./whatsapp_html_output --size 10000000 --include 655972256 --old-theme --enrich-from-vcards ./data/contacts.vcf --default-country-code 34 --no-banner -a
```

### GUI Viewer (Recommended)

The interactive viewer works best when run from its own isolated directory to avoid path issues.

1. **Setup in a separate folder**:
   
   ```shell
   cd ..
   git clone https://github.com/absadiki/whatsapp-msgstore-viewer whatsapp-viewer
   cd whatsapp-viewer
   python3 -m venv venv
   ./venv/bin/pip install -e .
   ```

2. **Launch the viewer**:
   ```shell
   ./venv/bin/python3 main.pyp
   ```

3. **In the GUI**:
   - Load your **decrypted** `msgstore.db` from your project folder.
   - Point the **Media Path** to your `Media/` folder.
   - Point to your `contacts.vcf` if needed for name resolution.