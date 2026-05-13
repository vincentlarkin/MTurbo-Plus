"""Quick analysis pass over opt/TurboSystem_sw/*/image.bin.

Goals:
- Map plain ASCII string regions in the outer image.
- Confirm version markers, boot strings, splash table state.
- Decompress the known timer zlib payload at 0x24bbb5 and dump candidate
  marker strings, prioritised by length and clinical-UI feel.

This file is a one-shot analysis helper. It does not modify any binary.
Output is ASCII-safe so Windows cp1252 consoles do not blow up.
"""

from __future__ import annotations

import io
import re
import sys
import zlib
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
IMAGE = next((ROOT / "opt" / "TurboSystem_sw").glob("*/image.bin"))
TIMER_ZLIB = 0x24BBB5

PRINTABLE_RE = re.compile(rb"[\x20-\x7e]{8,}")


def outer_strings(data: bytes) -> list[tuple[int, bytes]]:
    return [(m.start(), m.group()) for m in PRINTABLE_RE.finditer(data)]


def cluster_regions(hits: list[tuple[int, bytes]], gap: int = 0x200) -> list[tuple[int, int, int]]:
    if not hits:
        return []
    regions: list[list[int]] = []
    cur_start = hits[0][0]
    cur_end = hits[0][0] + len(hits[0][1])
    count = 1
    for off, s in hits[1:]:
        if off - cur_end <= gap:
            cur_end = max(cur_end, off + len(s))
            count += 1
        else:
            regions.append([cur_start, cur_end, count])
            cur_start, cur_end, count = off, off + len(s), 1
    regions.append([cur_start, cur_end, count])
    return [(a, b, c) for a, b, c in regions]


def decompress_timer(data: bytes) -> tuple[bytes, int]:
    obj = zlib.decompressobj()
    payload = obj.decompress(data[TIMER_ZLIB:])
    consumed = len(data) - TIMER_ZLIB - len(obj.unused_data)
    return payload, consumed


def split_cstrings(blob: bytes) -> list[tuple[int, bytes]]:
    out = []
    i = 0
    n = len(blob)
    while i < n:
        j = i
        while j < n and 0x20 <= blob[j] <= 0x7E:
            j += 1
        if j - i >= 6:
            out.append((i, blob[i:j]))
        i = max(j + 1, i + 1)
    return out


def looks_ui(s: bytes) -> bool:
    txt = s.decode("ascii", errors="ignore")
    if "/" in txt and "." in txt and txt.endswith(".cpp"):
        return False
    if txt.startswith(("Zaf", "_Z", "vtable", "typeinfo")):
        return False
    if txt.count(" ") < 1 and len(txt) < 14:
        return False
    if any(c.isalpha() for c in txt) and txt[0].isupper():
        return True
    return False


def main() -> None:
    data = IMAGE.read_bytes()
    print(f"image: {IMAGE.relative_to(ROOT)}  size={len(data):#x} ({len(data)} bytes)")
    print(f"version slot @0x8: {data[8:0x20]!r}")
    print(f"Wind River copyright present: {data.find(b'Copyright 1984-1996 Wind River') >= 0}")
    print(f"'Copyright 2019 If you see this, it worked' present: {data.find(b'Copyright 2019 If you see this') >= 0}")

    outer = outer_strings(data)
    regions = cluster_regions(outer)
    print(f"\nouter plain-ASCII regions (>=8 chars, gap 0x200):")
    for a, b, c in regions:
        print(f"  0x{a:08x}-0x{b:08x}  hits={c:5d}  span={b-a:#x}")

    payload, consumed = decompress_timer(data)
    print(f"\ntimer zlib @0x{TIMER_ZLIB:x}: consumed={consumed:#x}, inflates to {len(payload):#x} ({len(payload)} bytes)")

    timer_strings = split_cstrings(payload)
    print(f"timer payload printable cstrings >=6: {len(timer_strings)}")

    interesting = [
        b"hours",
        b"minutes",
        b"license",
        b"License",
        b"SonoSite",
        b"sonosite",
        b"FujiFilm",
        b"Service",
        b"Setup",
        b"System",
        b"Patient",
        b"Probe",
        b"Exam",
        b"Calc",
        b"Measurement",
        b"Annotation",
        b"Imaging",
        b"Preset",
        b"Cardiac",
        b"Abdomen",
        b"OB",
        b"Vascular",
        b"Software Version",
        b"Build",
        b"version",
        b"USB",
        b"Update",
        b"Upgrade",
        b"Error",
        b"Warning",
        b"contact",
        b"Contact",
        b"Please",
        b"Restart",
    ]
    print("\nselected hits inside timer payload:")
    for needle in interesting:
        count = payload.count(needle)
        if count:
            sample_off = payload.find(needle)
            line_start = max(0, sample_off - 40)
            line_end = min(len(payload), sample_off + 60)
            ctx = payload[line_start:line_end].replace(b"\x00", b".").decode("ascii", errors="backslashreplace")
            print(f"  {needle.decode():<18} count={count:4d}  ctx={ctx!r}")

    print("\nlong candidate UI strings inside timer payload (len 14..60):")
    seen = set()
    candidates = []
    for off, s in timer_strings:
        if not (14 <= len(s) <= 60):
            continue
        if s in seen:
            continue
        seen.add(s)
        if looks_ui(s):
            candidates.append((off, s))
    candidates.sort(key=lambda t: (-len(t[1]), t[1]))
    for off, s in candidates[:120]:
        print(f"  +0x{off:06x} len={len(s):2d}  {s.decode('ascii', errors='backslashreplace')!r}")


if __name__ == "__main__":
    main()
