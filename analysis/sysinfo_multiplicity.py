"""For each sysinfo label that appears multiple times, list all occurrences."""

from __future__ import annotations

import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.patch_mturbo_strings import SYSINFO_REPLACEMENTS

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

data = (ROOT / "opt" / "TurboSystem_sw" / "51.80.300.015" / "image.bin").read_bytes()
obj = zlib.decompressobj()
payload = obj.decompress(data[0x24BBB5:])


def find_all(blob: bytes, needle: bytes) -> list[int]:
    out = []
    start = 0
    while True:
        idx = blob.find(needle, start)
        if idx < 0:
            return out
        out.append(idx)
        start = idx + 1


def ctx(off: int, span: int = 40) -> str:
    chunk = payload[max(0, off - span): off + span]
    return chunk.replace(b"\x00", b".").decode("ascii", errors="backslashreplace")


for old, new in SYSINFO_REPLACEMENTS:
    old_hits = find_all(payload, old)
    new_hits = find_all(payload, new)
    if len(old_hits) <= 1 and len(new_hits) <= 1:
        continue
    print(f"\n--- {old.decode()!r} -> {new.decode()!r} ---")
    for h in old_hits:
        print(f"  OLD @ +0x{h:06x}  ctx={ctx(h)!r}")
    for h in new_hits:
        print(f"  NEW @ +0x{h:06x}  ctx={ctx(h)!r}")
