# CLAUDE.md - wa-crypt-tools

## Commands
- **Lint**: `./wa-crypt-tools/bin/python -m flake8 wa_crypt_tools`
- **Typecheck**: `./wa-crypt-tools/bin/python -m mypy wa_crypt_tools`
- **Test**: `./wa-crypt-tools/bin/python -m unittest discover tests`
- **Run**: `./wa-crypt-tools/bin/python -m wa_crypt_tools`

## Environment
- Uses `wa-crypt-tools` venv at project root.
- Dependencies handled via `pip install`.
- Testing uses `unittest` and `unittest.mock`.
