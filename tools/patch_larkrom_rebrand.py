#!/usr/bin/env python3
"""Apply the production LarkROM/Blueboot visible-string rebrand."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
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

FUJI_CONTACT = b"ffss-service@fujifilm.com"
CONTACT_MARKER = b"MT STRING VISIBLE 2019!!!"


@dataclass(frozen=True)
class Replacement:
    label: str
    old: bytes
    new: bytes
    replace_all: bool = False


REPLACEMENTS = [
    Replacement(
        "license heading",
        b"To obtain a license key:",
        b"To obtain LarkROM key:  ",
    ),
    Replacement(
        "contact heading",
        b"1. Contact SonoSite at:",
        b"1. Contact LarkROM at: ",
    ),
    Replacement(
        "system info mini-boot label",
        b"Mini Boot SW Ver",
        b"Blueboot SW Ver ",
        replace_all=True,
    ),
    Replacement(
        "license entry heading",
        b"3. Enter license key:",
        b"3. Enter LarkROM key:",
    ),
    Replacement(
        "worldwide support number",
        b"1.425.951.1330 (Worldwide)",
        b"1.877.675.8118 (Support)  ",
    ),
    Replacement(
        "product label",
        b"SonoSite Titan",
        b"LarkROM Titan ",
    ),
    Replacement(
        "password reset contact",
        b"(To reset your password, contact SonoSite at 1.877.657.8118)",
        b"(To reset your password, contact LarkROM at 1.877.675.8118) ",
    ),
    Replacement(
        "patent list title",
        b"SonoSite, Inc. Patent List",
        b"LarkROM OS Patent List    ",
    ),
]


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_lengths() -> None:
    if len(CONTACT_MARKER) != len(FUJI_CONTACT):
        fail("contact restore replacement is not length-preserving")
    for item in REPLACEMENTS:
        if len(item.old) != len(item.new):
            fail(
                f"{item.label} replacement length mismatch: "
                f"{len(item.old)} != {len(item.new)}"
            )


def patch_once(blob: bytearray, item: Replacement) -> tuple[bool, list[int]]:
    idx = blob.find(item.old)
    if idx >= 0:
        blob[idx : idx + len(item.old)] = item.new
        return True, [idx]
    if item.new in blob:
        return False, []
    fail(f"missing expected {item.label}: {item.old!r}")


def patch_all(blob: bytearray, item: Replacement) -> tuple[bool, list[int]]:
    changed = False
    hits: list[int] = []
    start = 0
    while True:
        idx = blob.find(item.old, start)
        if idx < 0:
            break
        blob[idx : idx + len(item.old)] = item.new
        hits.append(idx)
        start = idx + len(item.new)
        changed = True
    if hits:
        return changed, hits
    if item.new in blob:
        return False, []
    fail(f"missing expected {item.label}: {item.old!r}")


def restore_contact(blob: bytearray) -> tuple[bool, list[int]]:
    hits: list[int] = []
    start = 0
    while True:
        idx = blob.find(CONTACT_MARKER, start)
        if idx < 0:
            break
        blob[idx : idx + len(CONTACT_MARKER)] = FUJI_CONTACT
        hits.append(idx)
        start = idx + len(FUJI_CONTACT)
    if hits:
        return True, hits
    if FUJI_CONTACT in blob:
        return False, []
    fail(f"missing support contact: {FUJI_CONTACT!r} or {CONTACT_MARKER!r}")


def recompress_to_fit(payload: bytes, limit: int, data: bytes, stream_offset: int) -> bytes:
    candidate = best_recompress(payload)
    if len(candidate) <= limit:
        return candidate

    slack = count_trailing_zeros(data, stream_offset + limit)
    allowed_growth = min(slack, SLACK_HARD_CAP_BYTES)
    if len(candidate) <= limit + allowed_growth:
        return candidate

    fail(
        "recompressed LarkROM payload is too large: "
        f"best={len(candidate)} stream_limit={limit} slack={slack}"
    )


def patch_image(image_path: Path, dry_run: bool = False) -> str:
    check_lengths()
    data = bytearray(image_path.read_bytes())
    payload, stream_len = decompress_stream(data, KNOWN_TIMER_ZLIB_OFFSET)
    blob = bytearray(payload)
    notes: list[str] = []
    changed = False

    contact_changed, contact_hits = restore_contact(blob)
    changed |= contact_changed
    if contact_hits:
        notes.append(
            "restored fujifilm support contact at inflated offsets "
            + ", ".join(f"+0x{idx:x}" for idx in contact_hits)
        )
    else:
        notes.append("fujifilm support contact already present")

    for item in REPLACEMENTS:
        item_changed, hits = patch_all(blob, item) if item.replace_all else patch_once(blob, item)
        changed |= item_changed
        if hits:
            notes.append(
                f"patched {item.label} at inflated offsets "
                + ", ".join(f"+0x{idx:x}" for idx in hits)
            )
        else:
            notes.append(f"{item.label} already patched")

    if not changed:
        return "no LarkROM string changes needed\n" + "\n".join(notes)

    new_stream = recompress_to_fit(bytes(blob), stream_len, bytes(data), KNOWN_TIMER_ZLIB_OFFSET)
    notes.append(
        f"recompressed stream1 at 0x{KNOWN_TIMER_ZLIB_OFFSET:x}: "
        f"{stream_len} -> {len(new_stream)} bytes"
    )

    if dry_run:
        return "dry run only; image not written\n" + "\n".join(notes)

    data[KNOWN_TIMER_ZLIB_OFFSET : KNOWN_TIMER_ZLIB_OFFSET + len(new_stream)] = new_stream
    if len(new_stream) < stream_len:
        data[KNOWN_TIMER_ZLIB_OFFSET + len(new_stream) : KNOWN_TIMER_ZLIB_OFFSET + stream_len] = (
            b"\x00" * (stream_len - len(new_stream))
        )
    image_path.write_bytes(data)
    return "\n".join(notes)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    image_path = (args.image or resolve_single(SYSTEM_IMAGE_GLOB, "system image")).resolve()
    print(patch_image(image_path, dry_run=args.dry_run))
    if not args.dry_run:
        print(f"patched image written: {image_path}")


if __name__ == "__main__":
    main()
