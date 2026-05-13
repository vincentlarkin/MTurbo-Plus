"""Focused look at the most informative auth-related anchors in the inflated
timer payload. Goal: figure out STORAGE MODEL (default-string vs hashed
credential vs config-file lookup) without dumping a wall of proprietary
firmware text.
"""

from __future__ import annotations

import re
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

data = (ROOT / "opt" / "TurboSystem_sw" / "51.80.300.015" / "image.bin").read_bytes()
obj = zlib.decompressobj()
payload = obj.decompress(data[0x24BBB5:])

PRINTABLE_RE = re.compile(rb"[\x20-\x7e]{4,}")


def find_all_ci(blob: bytes, needle: bytes) -> list[int]:
    pat = re.compile(re.escape(needle), re.IGNORECASE)
    return [m.start() for m in pat.finditer(blob)]


def nearby_strings(blob: bytes, off: int, before: int = 256, after: int = 256, minlen: int = 4) -> list[tuple[int, bytes]]:
    region_start = max(0, off - before)
    region_end = min(len(blob), off + after)
    return [
        (m.start(), m.group())
        for m in PRINTABLE_RE.finditer(blob, region_start, region_end)
        if len(m.group()) >= minlen
    ]


anchors = [
    b"administrator",
    b"change password",
    b"old password",
    b"new password",
    b"forgot password",
    b"failed login",
    b"login failed",
    b"too many",
    b"locked out",
    b"sign in",
    b"credential",
    b"default password",
    b"default admin",
    b"default user",
    b"factory default",
    b"reset.*password",
    b"password.*expired",
]


for needle in anchors:
    if b".*" in needle:
        pat = re.compile(needle, re.IGNORECASE)
        hits = [m.start() for m in pat.finditer(payload)]
    else:
        hits = find_all_ci(payload, needle)
    if not hits:
        continue
    print(f"\n========== {needle.decode()!r}  ({len(hits)} hit{'s' if len(hits)!=1 else ''}) ==========")
    for off in hits[:6]:
        print(f"\n  +0x{off:08x}")
        for s_off, s in nearby_strings(payload, off, before=160, after=160, minlen=5):
            txt = s.decode("ascii", errors="backslashreplace")
            if any(skip in txt for skip in ("Zaf", "_Z", "::", ".cpp", ".h", "vtable")):
                continue
            print(f"      +0x{s_off:08x} len={len(s):3d}  {txt!r}")
