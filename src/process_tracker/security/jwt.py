from __future__ import annotations
"""
Мини-JWT (HS256) без внешних зависимостей.
Поддерживает encode(payload, secret, exp_seconds) и decode(token, secret).
"""

import base64
import json
import hmac
import hashlib
import time
from typing import Any, Dict

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def _unb64(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("ascii"))

def encode(payload: Dict[str, Any], secret: str, *, exp_seconds: int = 3600) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    body = dict(payload)
    body["iat"] = now
    body["exp"] = now + int(exp_seconds)
    h = _b64(json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    p = _b64(json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    signing_input = f"{h}.{p}".encode("ascii")
    sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    s = _b64(sig)
    return f"{h}.{p}.{s}"

class JWTError(Exception):
    ...

def decode(token: str, secret: str) -> Dict[str, Any]:
    try:
        h, p, s = token.split(".")
    except ValueError:
        raise JWTError("Invalid token format")
    signing_input = f"{h}.{p}".encode("ascii")
    expected = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig = _unb64(s)
    if not hmac.compare_digest(sig, expected):
        raise JWTError("Invalid signature")
    payload = json.loads(_unb64(p).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise JWTError("Token expired")
    return payload
