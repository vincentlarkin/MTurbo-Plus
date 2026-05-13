#!/usr/bin/env python3
"""Apply a visible conservative marker to the stock M-Turbo splash.

This deliberately does not re-encode the splash. It changes only selected RLE
value bytes in frame 0 from palette index 1 to palette index 15, leaving every
count byte, chunk length, pointer, and later offset untouched.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from patch_mturbo_splash import (
    EGA_PREVIEW_PALETTE,
    MTURBO_SPLASH_INDEX,
    SPLASH_POINTER_TABLE_OFFSET,
    SYSTEM_IMAGE_GLOB,
    decode_rle_with_consumed,
    render,
    resolve_single,
    splash_pointers,
)


ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "analysis" / "minimal_v_marker"

# Relative offsets inside splash frame 0. These are RLE value bytes, not count
# bytes. They were chosen from stock frame 0 blue-background runs. The first
# group is the original tiny V-ish marker; the second group makes it visible on
# hardware while still changing only existing value bytes.
V_VALUE_OFFSETS = [
    0x180A,
    0x20A6,
    0x2222,
    0x242C,
    0x26B8,
    0x2BEA,
    0x2EF6,
    0x3342,
    0x37F4,
    0x412C,
    0x453C,
    0x454E,
    0x2890,
    0x2A5E,
    0x2C7C,
    0x2E6A,
    0x3116,
    0x3428,
    0x3736,
    0x3A6A,
    0x3D9A,
    0x409E,
    0x432C,
    0x4618,
    0x497A,
    0x4D30,
    0x50FC,
    0x5426,
    0x56BC,
    0x591C,
    0x5C70,
    0x601E,
    0x637C,
    0x658C,
]

SOURCE_INDEX = 1
MARKER_INDEX = 15


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def patch_image(image_path: Path, dry_run: bool, outdir: Path) -> None:
    data = bytearray(image_path.read_bytes())
    ptrs = splash_pointers(data)
    start = ptrs[MTURBO_SPLASH_INDEX]
    end = ptrs[MTURBO_SPLASH_INDEX + 1]
    chunk_len = end - start

    changed = 0
    already = 0
    for rel in V_VALUE_OFFSETS:
        if rel < 0 or rel >= chunk_len or rel % 2:
            fail(f"invalid RLE value offset 0x{rel:x}")
        abs_off = start + rel
        value = data[abs_off] & 0x0F
        if value == MARKER_INDEX:
            already += 1
            continue
        if value != SOURCE_INDEX:
            fail(f"unexpected palette index at 0x{abs_off:x}: got {value}, expected {SOURCE_INDEX}")
        data[abs_off] = (data[abs_off] & 0xF0) | MARKER_INDEX
        changed += 1

    chunk = bytes(data[start:end])
    indices, consumed = decode_rle_with_consumed(chunk)
    if consumed != chunk_len:
        fail(f"patched splash consumed {consumed}, expected {chunk_len}")

    outdir.mkdir(parents=True, exist_ok=True)
    preview = outdir / "minimal_v_marker.png"
    render(indices, EGA_PREVIEW_PALETTE).save(preview)
    print(f"M-Turbo splash chunk: 0x{start:x}-0x{end:x} ({chunk_len} bytes)")
    print(f"decoded frame consumes {consumed} of {chunk_len} bytes")
    print(f"marker value bytes changed={changed}, already={already}, total={len(V_VALUE_OFFSETS)}")
    print(f"most-common indices: {Counter(indices).most_common(5)}")
    print(f"preview written: {preview.resolve()}")

    if not changed:
        print("minimal V marker already patched")
        return
    if dry_run:
        print("dry run only; image not written")
        return
    image_path.write_bytes(data)
    print(f"patched image written: {image_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, default=None)
    parser.add_argument("--outdir", type=Path, default=OUTDIR)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    image_path = (args.image or resolve_single(SYSTEM_IMAGE_GLOB, "system image")).resolve()
    patch_image(image_path, args.dry_run, args.outdir)


if __name__ == "__main__":
    main()
