"""Generate encrypted built-in config from the current user config.

Usage:
    python tools/generate_builtin.py

Reads ~/.sharppic/config.json, encrypts it, and writes the result into
src/utils/builtin_config.py as an embedded constant.
"""

import json
import sys
from pathlib import Path

# Allow importing from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.crypto import encrypt

CONFIG_FILE = Path.home() / ".sharppic" / "config.json"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "src" / "utils" / "builtin_config.py"

# Keys to embed (only API-related, not user-specific paths)
EMBED_KEYS = ["api_base_url", "api_key", "model_name"]


def main():
    if not CONFIG_FILE.exists():
        print(f"Error: config not found at {CONFIG_FILE}")
        print("Please run the app first and configure settings.")
        sys.exit(1)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        full_config = json.load(f)

    embed = {k: full_config[k] for k in EMBED_KEYS if k in full_config}

    if not embed.get("api_key"):
        print("Warning: api_key is empty in config, are you sure?")

    token = encrypt(embed)

    code = (
        '"""Auto-generated built-in config. Do NOT edit manually.\n'
        '\n'
        'Regenerate with:  python tools/generate_builtin.py\n'
        '"""\n'
        '\n'
        f'BUILTIN_TOKEN = "{token}"\n'
    )

    OUTPUT_FILE.write_text(code, encoding="utf-8")
    print(f"Written to {OUTPUT_FILE}")
    print(f"Embedded keys: {list(embed.keys())}")
    print(f"Token length: {len(token)} chars")


if __name__ == "__main__":
    main()
