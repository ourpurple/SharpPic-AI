import json
from pathlib import Path

_CONFIG_DIR = Path.home() / ".sharppic"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

_DEFAULTS = {
    "api_provider": "openai",  # "openai" or "gmicloud"
    "api_base_url": "https://api.openai.com/v1",
    "api_key": "",
    "model_name": "gpt-4o",
    "save_directory": str(Path.home() / "Pictures" / "SharpPic"),
    # gmicloud-specific
    "gmi_api_key": "",
    "gmi_image_size": "4K",
    "gmi_aspect_ratio": "",
}

_config: dict = {}


def _load_builtin() -> dict:
    """Try to decrypt the embedded built-in config. Returns {} on failure."""
    try:
        from src.utils.builtin_config import BUILTIN_TOKEN
        from src.utils.crypto import decrypt
        return decrypt(BUILTIN_TOKEN)
    except Exception:
        return {}


def load() -> dict:
    global _config
    if _CONFIG_FILE.exists():
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            _config = json.load(f)
    else:
        _config = {}

    # Layer defaults: hard-coded < built-in encrypted < user file
    builtin = _load_builtin()
    for key, value in _DEFAULTS.items():
        _config.setdefault(key, builtin.get(key, value))
    # Also fill any built-in keys not in _DEFAULTS
    for key, value in builtin.items():
        _config.setdefault(key, value)

    return _config


def save() -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(_config, f, indent=2, ensure_ascii=False)


def get(key: str, default=None):
    if not _config:
        load()
    return _config.get(key, default if default is not None else _DEFAULTS.get(key))


def set(key: str, value) -> None:
    if not _config:
        load()
    _config[key] = value


def get_all() -> dict:
    if not _config:
        load()
    return dict(_config)
