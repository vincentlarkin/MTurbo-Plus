#!/usr/bin/env python3
"""Patch one visible contact/support string as a string-only marker."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from patch_mturbo_strings import (
    KNOWN_TIMER_ZLIB_OFFSET,
    best_recompress,
    count_trailing_zeros,
    decompress_stream,
    resolve_single,
)


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_IMAGE_GLOB = "opt/TurboSystem_sw/*/image.bin"
SLACK_HARD_CAP_BYTES = 0x400

# Same length: 25 bytes. This appears once in the license/contact screen copy.
ORIGINAL = b"ffss-service@fujifilm.com"
PATCHED = b"MT STRING VISIBLE 2019!!!"


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def recompress_to_fit(payload: bytes, limit: int, data: bytes, stream_offset: int) -> bytes:
    candidate = best_recompress(payload)
    if len(candidate) <= limit:
        return candidate

    slack = count_trailing_zeros(data, stream_offset + limit)
    allowed_growth = min(slack, SLACK_HARD_CAP_BYTES)
    if len(candidate) <= limit + allowed_growth:
        print(
            f"zlib grows by {len(candidate) - limit} bytes into trailing zero slack "
            f"({slack} bytes measured, cap {SLACK_HARD_CAP_BYTES})"
        )
        return candidate

    fail(
        "recompressed payload is too large: "
        f"best={len(candidate)} stream_limit={limit} slack={slack}"
    )


def patch_image(image_path: Path, dry_run: bool) -> None:
    if len(ORIGINAL) != len(PATCHED):
        fail("replacement must be length-preserving")

    data = bytearray(image_path.read_bytes())
    payload, stream_len = decompress_stream(data, KNOWN_TIMER_ZLIB_OFFSET)
    blob = bytearray(payload)
    idx = blob.find(ORIGINAL)

    if idx < 0:
        if PATCHED in blob:
            print(f"already patched: {PATCHED.decode()}")
            return
        fail(f"missing expected contact string: {ORIGINAL!r}")

    blob[idx : idx + len(ORIGINAL)] = PATCHED
    new_stream = recompress_to_fit(bytes(blob), stream_len, bytes(data), KNOWN_TIMER_ZLIB_OFFSET)
    print(f"patched contact string at inflated +0x{idx:x}")
    print(f"{ORIGINAL.decode()} -> {PATCHED.decode()}")
    print(f"zlib stream 0x{KNOWN_TIMER_ZLIB_OFFSET:x}: {stream_len} -> {len(new_stream)} bytes")

    if dry_run:
        print("dry run only; image not written")
        return

    data[KNOWN_TIMER_ZLIB_OFFSET : KNOWN_TIMER_ZLIB_OFFSET + len(new_stream)] = new_stream
    if len(new_stream) < stream_len:
        data[KNOWN_TIMER_ZLIB_OFFSET + len(new_stream) : KNOWN_TIMER_ZLIB_OFFSET + stream_len] = (
            b"\x00" * (stream_len - len(new_stream))
        )
    image_path.write_bytes(data)
    print(f"patched image written: {image_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    image_path = (args.image or resolve_single(SYSTEM_IMAGE_GLOB, "system image")).resolve()
    patch_image(image_path, args.dry_run)


if __name__ == "__main__":
    main()
