"""Post-patch count of OLD strings in the payload."""
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


def find_all(blob, needle):
    out = []
    start = 0
    while True:
        idx = blob.find(needle, start)
        if idx < 0:
            return out
        out.append(idx)
        start = idx + 1


print(f"{'OLD':<26} {'#old':>4} {'#new':>4}  old_offsets")
print("-" * 80)
for old, new in SYSINFO_REPLACEMENTS:
    old_hits = find_all(payload, old)
    new_hits = find_all(payload, new)
    o = ",".join(f"{h:#x}" for h in old_hits[:4])
    n = ",".join(f"{h:#x}" for h in new_hits[:4])
    print(f"{old.decode():<26} {len(old_hits):>4} {len(new_hits):>4}  old=[{o}]  new=[{n}]")
