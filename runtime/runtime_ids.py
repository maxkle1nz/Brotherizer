#!/usr/bin/env python3
"""Runtime ID helpers."""

from __future__ import annotations

import os
import time

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _encode_base32(value: int, width: int) -> str:
    chars: list[str] = []
    while value > 0:
        value, rem = divmod(value, 32)
        chars.append(ALPHABET[rem])
    encoded = "".join(reversed(chars or ["0"]))
    return encoded.rjust(width, "0")


def make_ulid_like() -> str:
    millis = int(time.time() * 1000)
    random_part = int.from_bytes(os.urandom(10), "big")
    return f"{_encode_base32(millis, 10)}{_encode_base32(random_part, 16)}"


def make_runtime_id(prefix: str) -> str:
    return f"{prefix}_{make_ulid_like()}"

