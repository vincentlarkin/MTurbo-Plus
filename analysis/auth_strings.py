"""Search the outer image, the inflated timer payload, the SHDb image, and
tempFL.bin for any auth-related strings. Print location and surrounding
context so we can tell DEFAULT-VALUE storage from CHECK-CODE references.
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

SYS_IMAGE = next((ROOT / "opt" / "TurboSystem_sw").glob("*/image.bin"))
SHDB_IMAGE = next((ROOT / "opt" / "TurboSHDb").glob("*/image.bin"))
TEMPFL = next((ROOT / "opt" / "TurboSystem_sw").glob("*/eFilmLite/tempFL.bin"))
TIMER_ZLIB = 0x24BBB5

NEEDLES_CI = [
    b"administrator",
    b"admin",
    b"password",
    b"login",
    b"user name",
    b"username",
    b"passwd",
    b"sign in",
    b"sign-in",
    b"credential",
    b"authenticate",
    b"auth ",
    b"unlock",
    b"locked",
    b"failed login",
    b"too many",
    b"forgot password",
    b"new password",
    b"old password",
    b"password expired",
    b"change password",
    b"reset password",
]


def find_all_ci(blob: bytes, needle: bytes) -> list[int]:
    pat = re.compile(re.escape(needle), re.IGNORECASE)
    return [m.start() for m in pat.finditer(blob)]


def ctx(blob: bytes, off: int, before: int = 80, after: int = 80) -> str:
    chunk = blob[max(0, off - before): off + after]
    return chunk.replace(b"\x00", b".").decode("ascii", errors="backslashreplace")


def scan(label: str, blob: bytes, allow_decompress: bool = False) -> None:
    print(f"\n========== {label}  (size 0x{len(blob):x}) ==========")
    for needle in NEEDLES_CI:
        hits = find_all_ci(blob, needle)
        if not hits:
            continue
        print(f"\n  --- {needle.decode()!r}  ({len(hits)} hit{'s' if len(hits)!=1 else ''}) ---")
        for off in hits[:20]:
            print(f"    +0x{off:08x}  ctx={ctx(blob, off)!r}")
        if len(hits) > 20:
            print(f"    ... and {len(hits) - 20} more")


def main() -> None:
    sys_data = SYS_IMAGE.read_bytes()
    shdb_data = SHDB_IMAGE.read_bytes()
    tempfl = TEMPFL.read_bytes()

    scan(f"outer image  ({SYS_IMAGE.relative_to(ROOT)})", sys_data)

    print(f"\n========== inflated timer payload  (offset 0x{TIMER_ZLIB:x}) ==========")
    obj = zlib.decompressobj()
    payload = obj.decompress(sys_data[TIMER_ZLIB:])
    scan("inflated timer payload", payload)

    scan(f"shdb image  ({SHDB_IMAGE.relative_to(ROOT)})", shdb_data)
    scan(f"tempFL.bin  ({TEMPFL.relative_to(ROOT)})", tempfl)


if __name__ == "__main__":
    main()
