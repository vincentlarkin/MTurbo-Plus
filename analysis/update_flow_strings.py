"""Search the inflated timer payload for strings related to the update-
detection flow: file/path names, version-compare/downgrade messages,
package descriptors, and anything that names a sibling file to image.bin.

Goal: figure out what file/marker (besides image.bin) the M-Turbo
updater is actually scanning for on the USB stick.
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

sys_image = next((ROOT / "opt" / "TurboSystem_sw").glob("*/image.bin"))
data = sys_image.read_bytes()
obj = zlib.decompressobj()
payload = obj.decompress(data[0x24BBB5:])

NEEDLES = [
    # path / file names
    b"opt/",
    b"opt\\",
    b"image.bin",
    b"tempFL",
    b"eFilmLite",
    b"TurboSystem",
    b"TurboSHDb",
    b".manifest",
    b".pkg",
    b".sig",
    b".upg",
    b".update",
    b".xml",
    b".cfg",
    b"manifest",
    b"package",
    b"signature",
    b"checksum",
    b"digest",
    # update flow / version compare
    b"downgrade",
    b"older",
    b"newer",
    b"same version",
    b"already installed",
    b"highest seen",
    b"last installed",
    b"high water",
    b"cached version",
    b"version too low",
    b"version too high",
    b"version mismatch",
    b"valid package",
    b"invalid package",
    b"corrupt package",
    b"system preparation",
    b"prepare upgrade",
    b"upgrade not ready",
    b"upgrade pending",
    # USB
    b"usb",
    b"USB",
    b"stick",
    b"removable",
    # version handling code-paths
    b"installed version",
    b"current version",
    b"target version",
    b"compare version",
    b"is_newer",
    b"isNewer",
    b"GetVersion",
    b"getVersion",
    b"package version",
    b"product version",
]


def find_all_ci(blob: bytes, needle: bytes) -> list[int]:
    pat = re.compile(re.escape(needle), re.IGNORECASE)
    return [m.start() for m in pat.finditer(blob)]


def find_all_cs(blob: bytes, needle: bytes) -> list[int]:
    return [m.start() for m in re.finditer(re.escape(needle), blob)]


def ctx(blob: bytes, off: int, before: int = 80, after: int = 120) -> str:
    chunk = blob[max(0, off - before): off + after]
    return chunk.replace(b"\x00", b".").decode("ascii", errors="backslashreplace")


CASE_SENSITIVE = {b"USB", b"usb"}

for needle in NEEDLES:
    hits = find_all_cs(payload, needle) if needle in CASE_SENSITIVE else find_all_ci(payload, needle)
    if not hits:
        continue
    print(f"\n========== {needle.decode(errors='backslashreplace')!r}  ({len(hits)} hit{'s' if len(hits)!=1 else ''}) ==========")
    for off in hits[:8]:
        print(f"  +0x{off:08x}  {ctx(payload, off)!r}")
    if len(hits) > 8:
        print(f"  ... and {len(hits) - 8} more")
