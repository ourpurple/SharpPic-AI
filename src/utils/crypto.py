"""Encrypt / decrypt helpers for built-in config.

Uses XOR with a rotating key + base64.  This is **obfuscation**, not
cryptographic security — it prevents casual exposure of the API key in
plain text but cannot stop a determined reverse-engineer.  Acceptable for
distributing a desktop tool to trusted users.
"""

import base64
import json

# Rotating XOR key — split across fragments to make grep harder
_K_PARTS = [b"Sh4rp", b"D0c_", b"Bu1lt", b"!n_K3y"]
_KEY = b"".join(_K_PARTS)


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encrypt(config: dict) -> str:
    """Return a base64 string representing the encrypted config dict."""
    raw = json.dumps(config, ensure_ascii=False).encode("utf-8")
    return base64.b64encode(_xor_bytes(raw, _KEY)).decode("ascii")


def decrypt(token: str) -> dict:
    """Decode a token produced by encrypt() back to a config dict."""
    raw = _xor_bytes(base64.b64decode(token), _KEY)
    return json.loads(raw.decode("utf-8"))
