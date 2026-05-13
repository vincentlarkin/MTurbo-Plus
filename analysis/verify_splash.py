"""Verify the current state of the splash bitmap inside image.bin.

Decodes splash frame 0 from the RLE chunk and reports whether it matches
the patched (blue field + centered wireframe + MTURBO+ BLUE BOOT text) or
the stock layout. Also writes a fresh PNG preview from the *current* bytes.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.patch_mturbo_splash import (  # noqa: E402
    SPLASH_POINTER_TABLE_OFFSET,
    SPLASH_FRAME_COUNT,
    MTURBO_SPLASH_INDEX,
    PIXELS,
    EGA_PREVIEW_PALETTE,
    BACKGROUND_INDEX,
    WIRE_INDEX,
    DIM_WIRE_INDEX,
    decode_rle_with_consumed,
    looks_patched,
    render,
)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass


def main() -> None:
    image = next((ROOT / "opt" / "TurboSystem_sw").glob("*/image.bin"))
    out_dir = ROOT / "analysis" / "splash_candidates"
    out_dir.mkdir(parents=True, exist_ok=True)

    data = image.read_bytes()
    ptrs = [
        int.from_bytes(
            data[SPLASH_POINTER_TABLE_OFFSET + i * 4 : SPLASH_POINTER_TABLE_OFFSET + i * 4 + 4],
            "little",
        )
        for i in range(SPLASH_FRAME_COUNT)
    ]
    print(f"image: {image.relative_to(ROOT)}  size=0x{len(data):x}")
    print(f"splash pointer table @ 0x{SPLASH_POINTER_TABLE_OFFSET:x}")
    for i, p in enumerate(ptrs):
        end = ptrs[i + 1] if i + 1 < len(ptrs) else None
        size = (end - p) if end else None
        print(f"  frame[{i:2d}] = 0x{p:08x}{'' if end is None else f'  size {size} bytes'}")

    start = ptrs[MTURBO_SPLASH_INDEX]
    end = ptrs[MTURBO_SPLASH_INDEX + 1]
    chunk = bytes(data[start:end])
    indices, consumed = decode_rle_with_consumed(chunk)
    if len(indices) != PIXELS:
        print(f"  ERROR: decoded {len(indices)} pixels (expected {PIXELS})")
        sys.exit(1)

    counts = Counter(indices)
    top = counts.most_common(5)
    print(f"\nM-Turbo splash chunk: 0x{start:x}-0x{end:x}  ({len(chunk)} bytes)")
    print(f"decoded {consumed} of {len(chunk)} chunk bytes")
    print(f"most-common palette indices: {top}")
    print(
        f"counts: bg(={BACKGROUND_INDEX})={counts[BACKGROUND_INDEX]}, "
        f"wire(={WIRE_INDEX})={counts[WIRE_INDEX]}, "
        f"dim(={DIM_WIRE_INDEX})={counts[DIM_WIRE_INDEX]}, "
        f"stock-idx1={counts[1]}"
    )

    is_patched = looks_patched(indices)
    print(f"\nlooks_patched()  -> {is_patched}")
    if is_patched:
        print("  STATUS: splash is the MTurbo-Plus blue-wireframe variant. Custom photo present.")
    else:
        print("  STATUS: splash looks STOCK (not patched). Run patch_mturbo_splash.py.")

    preview = out_dir / "current_splash_state.png"
    render(indices, EGA_PREVIEW_PALETTE).save(preview)
    print(f"\nwrote preview: {preview.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
