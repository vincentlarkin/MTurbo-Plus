"""Look in the inflated timer payload near anchors we KNOW the user sees,
and dump short label-like strings nearby. These are the candidates that
realistically appear on the timer/license screen and adjacent setup screens.

Also dumps the plain-ASCII boot block around 0x24b6a8 in the outer image.
"""

from __future__ import annotations

import re
import sys
import zlib
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
IMAGE = next((ROOT / "opt" / "TurboSystem_sw").glob("*/image.bin"))
TIMER_ZLIB = 0x24BBB5
STRING_RE = re.compile(rb"[\x20-\x7e]{4,}")


def cstrings(blob: bytes, start: int, end: int, minlen: int = 4) -> list[tuple[int, bytes]]:
    out: list[tuple[int, bytes]] = []
    for m in STRING_RE.finditer(blob, start, end):
        if len(m.group()) >= minlen:
            out.append((m.start(), m.group()))
    return out


def main() -> None:
    data = IMAGE.read_bytes()

    print("=== outer image: boot text block 0x24b400..0x24b900 ===")
    for off, s in cstrings(data, 0x24B400, 0x24B900, minlen=6):
        print(f"  0x{off:08x} len={len(s):3d}  {s.decode('ascii', errors='backslashreplace')!r}")

    obj = zlib.decompressobj()
    payload = obj.decompress(data[TIMER_ZLIB:])
    print(f"\n=== inflated timer payload: {len(payload):#x} bytes ===")

    anchors = [
        b"49 hours, 59 minutes",
        b"To obtain a license key:",
        b"1. Contact SonoSite at:",
        b"3. Enter license key:",
        b"left before license key needed",
        b"1.877.675.8118 (USA)",
        b"www.sonosite.com",
        b"Sleep Delay",
        b"License Key",
        b"Software Version",
        b"Power-Off Delay",
        b"Internal Storage Capacity",
        b"NOTE: DICOM not licensed",
    ]
    for needle in anchors:
        idx = payload.find(needle)
        if idx < 0:
            print(f"\n--- {needle.decode()!r} NOT FOUND ---")
            continue
        print(f"\n--- {needle.decode()!r} @ +0x{idx:06x} ---")
        window_start = max(0, idx - 0x200)
        window_end = min(len(payload), idx + 0x400)
        for off, s in cstrings(payload, window_start, window_end, minlen=4):
            if len(s) > 80:
                continue
            txt = s.decode("ascii", errors="backslashreplace")
            if any(bad in txt for bad in (".cpp", "::", "_Z", "Zaf", "ZAF")):
                continue
            print(f"   +0x{off:06x} len={len(s):3d}  {txt!r}")


if __name__ == "__main__":
    main()
