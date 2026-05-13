#!/usr/bin/env python3
"""Patch the Setup label from System Information to System Info."""

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

REPLACEMENTS = [
    (
        b"SystemSetupPanel_SystemInformation",
        b"SystemSetupPanel_SystemInfo       ",
    ),
    (
        b"SystemInformation_Group",
        b"SystemInfo       _Group",
    ),
]


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_lengths() -> None:
    for old, new in REPLACEMENTS:
        if len(old) != len(new):
            fail(f"length mismatch: {old!r} -> {new!r}")


def recompress_to_fit(payload: bytes, limit: int, data: bytes, stream_offset: int) -> bytes:
    candidate = best_recompress(payload)
    if len(candidate) <= limit:
        return candidate

    slack = count_trailing_zeros(data, stream_offset + limit)
    allowed_growth = min(slack, SLACK_HARD_CAP_BYTES)
    if len(candidate) <= limit + allowed_growth:
        return candidate
    fail(
        "recompressed payload is too large: "
        f"best={len(candidate)} stream_limit={limit} slack={slack}"
    )


def patch_image(image_path: Path, dry_run: bool) -> None:
    data = bytearray(image_path.read_bytes())
    payload, stream_len = decompress_stream(data, KNOWN_TIMER_ZLIB_OFFSET)
    blob = bytearray(payload)
    changed = False

    for old, new in REPLACEMENTS:
        idx = blob.find(old)
        if idx >= 0:
            blob[idx : idx + len(old)] = new
            changed = True
            print(f"patched setup label at inflated +0x{idx:x}: {old.decode()} -> {new.decode()}")
            continue
        if blob.find(new) >= 0:
            print(f"already patched setup label: {new.decode()}")
            continue
        fail(f"missing expected setup label: {old!r}")

    if not changed:
        print("no setup label changes needed")
        return

    new_stream = recompress_to_fit(bytes(blob), stream_len, bytes(data), KNOWN_TIMER_ZLIB_OFFSET)
    if dry_run:
        print(
            "dry run only; image not written "
            f"(zlib 0x{KNOWN_TIMER_ZLIB_OFFSET:x}: {stream_len} -> {len(new_stream)} bytes)"
        )
        return

    data[KNOWN_TIMER_ZLIB_OFFSET : KNOWN_TIMER_ZLIB_OFFSET + len(new_stream)] = new_stream
    if len(new_stream) < stream_len:
        data[KNOWN_TIMER_ZLIB_OFFSET + len(new_stream) : KNOWN_TIMER_ZLIB_OFFSET + stream_len] = (
            b"\x00" * (stream_len - len(new_stream))
        )
    image_path.write_bytes(data)
    print(
        f"patched image written: {image_path} "
        f"(zlib 0x{KNOWN_TIMER_ZLIB_OFFSET:x}: {stream_len} -> {len(new_stream)} bytes)"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    check_lengths()
    image_path = (args.image or resolve_single(SYSTEM_IMAGE_GLOB, "system image")).resolve()
    patch_image(image_path, args.dry_run)


if __name__ == "__main__":
    main()
