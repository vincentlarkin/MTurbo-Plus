"""Look at the context surrounding the patched and unpatched offsets to find
out which copy is the actual on-screen label table."""

from __future__ import annotations
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


def ctx(off: int, before: int = 96, after: int = 96) -> str:
    chunk = payload[max(0, off - before): off + after]
    return chunk.replace(b"\x00", b".").decode("ascii", errors="backslashreplace")


points = {
    "ARM SW Ver early": 0x8c39c5,
    "ARM SW Ver late":  0x8ca0cc,
    "Mini Boot early":  0x8c3982,
    "Mini Boot late":   0x8ca094,
    "Burn-In Mode early": 0x8ca44c,
    "Burn-In Mode late":  0x8cae20,
    "Sleep Delay early":  0x8ca46c,
    "Sleep Delay later1": 0x8d1c84,
    "Sleep Delay later2": 0x8d1c98,
    "Panic Screen early": 0x8ca570,
    "Panic Screen late":  0x8ce988,
}

for label, off in points.items():
    print(f"\n=== {label} @ +0x{off:06x} ===")
    print(repr(ctx(off)))
