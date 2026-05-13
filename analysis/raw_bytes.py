"""Show raw bytes around the offsets the patcher reported."""
import sys
import zlib
from pathlib import Path
import binascii

ROOT = Path(__file__).resolve().parents[1]
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

data = (ROOT / "opt" / "TurboSystem_sw" / "51.80.300.015" / "image.bin").read_bytes()
obj = zlib.decompressobj()
payload = obj.decompress(data[0x24BBB5:])

points = [
    ("Mini Boot 0x8c3982", 0x8c3982),
    ("ARM SW 0x8c39c5",    0x8c39c5),
    ("Sleep Delay 0x8ca46c", 0x8ca46c),
    ("Burn-In Mode 0x8ca44c", 0x8ca44c),
    ("Panic Screen 0x8ca570", 0x8ca570),
]

for label, off in points:
    print(f"\n=== {label} ===")
    raw = payload[off - 32: off + 64]
    print("raw:", binascii.hexlify(raw, ' ', 16).decode())
    print("ascii:", "".join(chr(b) if 0x20 <= b <= 0x7e else "." for b in raw))
