#!/usr/bin/env python3
"""Recompute integrity checksums in a modified M-Turbo system or SHDb image.

This is the missing piece that makes the binary editable. After any byte
change inside opt/TurboSystem_sw/.../image.bin or opt/TurboSHDb/.../image.bin,
run this to refresh:

  - Per-descriptor stored_word in the system image (CRC32 of the bytes
    right after each descriptor's stored_word field, ending at the start of
    the next descriptor or at end-of-file for the last one).
  - The outer header CRC32 at offset 0x4 (system: covers 0x8..0x24bb9c;
    SHDb: covers 0x8..end-of-file).

The tool detects which kind of image it is from the byte length and the
embedded version string, so the same script works on both.

Examples:

    # Inspect-only: print stored vs calculated for every layer.
    python -B .\\tools\\recompute_image_checksums.py opt\\TurboSystem_sw\\51.80.300.021\\image.bin --check

    # Rewrite the file in place, after backing it up to image.bin.bak.
    python -B .\\tools\\recompute_image_checksums.py opt\\TurboSystem_sw\\51.80.300.021\\image.bin --write

    # Same but write to a new path instead of overwriting.
    python -B .\\tools\\recompute_image_checksums.py path\\to\\edited.bin --write --output path\\to\\sealed.bin
"""

from __future__ import annotations

import argparse
import shutil
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SYSTEM_DESCRIPTOR_OFFSETS = [0x24BB9C, 0x676104, 0x677516, 0x677D42, 0x1323127]
SYSTEM_HEADER_CRC_END_FIELD = 0x20
SYSTEM_OUTER_CRC_OFFSET = 0x4
SHDB_OUTER_CRC_OFFSET = 0x4

KIND_SYSTEM = "system"
KIND_SHDB = "shdb"


@dataclass
class DescriptorLayout:
    label: str
    desc_offset: int
    next_desc_offset: int

    @property
    def stored_word_offset(self) -> int:
        return self.desc_offset + 4

    @property
    def crc_range(self) -> tuple[int, int]:
        return self.desc_offset + 8, self.next_desc_offset


@dataclass
class FixupReport:
    label: str
    stored: int
    calculated: int
    range_start: int
    range_end: int
    matches: bool


def u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little")


def write_u32(buffer: bytearray, offset: int, value: int) -> None:
    buffer[offset : offset + 4] = (value & 0xFFFFFFFF).to_bytes(4, "little")


def detect_kind(data: bytes) -> str:
    head = data[:0x40]
    if b"51.80.300" in head:
        return KIND_SYSTEM
    if b"50.80.111" in head:
        return KIND_SHDB
    if len(data) > 200_000_000:
        return KIND_SHDB
    return KIND_SYSTEM


def descriptor_layouts(data: bytes) -> list[DescriptorLayout]:
    layouts: list[DescriptorLayout] = []
    offsets = SYSTEM_DESCRIPTOR_OFFSETS + [len(data)]
    for index in range(len(SYSTEM_DESCRIPTOR_OFFSETS)):
        layouts.append(
            DescriptorLayout(
                label=f"stream{index + 1}",
                desc_offset=offsets[index],
                next_desc_offset=offsets[index + 1],
            )
        )
    return layouts


def system_header_crc_end(data: bytes) -> int:
    return u32(data, SYSTEM_HEADER_CRC_END_FIELD)


def fixup_system(data: bytearray, dry_run: bool) -> tuple[bool, list[FixupReport], list[FixupReport]]:
    descriptor_reports: list[FixupReport] = []
    header_reports: list[FixupReport] = []
    changed = False

    for layout in descriptor_layouts(data):
        start, end = layout.crc_range
        calc = zlib.crc32(bytes(data[start:end])) & 0xFFFFFFFF
        stored = u32(data, layout.stored_word_offset)
        report = FixupReport(layout.label, stored, calc, start, end, stored == calc)
        descriptor_reports.append(report)
        if stored != calc:
            changed = True
            if not dry_run:
                write_u32(data, layout.stored_word_offset, calc)

    header_end = system_header_crc_end(data)
    header_calc = zlib.crc32(bytes(data[8:header_end])) & 0xFFFFFFFF
    header_stored = u32(data, SYSTEM_OUTER_CRC_OFFSET)
    header_reports.append(FixupReport("outer header", header_stored, header_calc, 8, header_end, header_stored == header_calc))
    if header_stored != header_calc:
        changed = True
        if not dry_run:
            write_u32(data, SYSTEM_OUTER_CRC_OFFSET, header_calc)
    return changed, descriptor_reports, header_reports


def fixup_shdb(data: bytearray, dry_run: bool) -> tuple[bool, list[FixupReport]]:
    header_calc = zlib.crc32(bytes(data[8:])) & 0xFFFFFFFF
    header_stored = u32(data, SHDB_OUTER_CRC_OFFSET)
    report = FixupReport("outer header", header_stored, header_calc, 8, len(data), header_stored == header_calc)
    if header_stored != header_calc and not dry_run:
        write_u32(data, SHDB_OUTER_CRC_OFFSET, header_calc)
    return header_stored != header_calc, [report]


def render_reports(kind: str, reports: list[FixupReport]) -> None:
    for report in reports:
        status = "OK" if report.matches else "FIX"
        print(
            f"  [{status}] {report.label:<14} stored=0x{report.stored:08x} "
            f"calculated=0x{report.calculated:08x} "
            f"range=0x{report.range_start:x}..0x{report.range_end:x}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path, help="path to the system or SHDb image.bin")
    parser.add_argument("--write", action="store_true", help="rewrite the file in place (or to --output)")
    parser.add_argument("--check", action="store_true", help="report stored vs calculated, do not write")
    parser.add_argument("--output", type=Path, help="if writing, save to this path instead of overwriting in place")
    parser.add_argument("--no-backup", action="store_true", help="skip the .bak backup when writing in place")
    parser.add_argument("--kind", choices=[KIND_SYSTEM, KIND_SHDB], help="override auto-detected image kind")
    args = parser.parse_args()

    if args.write and args.check:
        print("error: pass --write or --check, not both", file=sys.stderr)
        sys.exit(2)
    if not args.write and not args.check:
        args.check = True

    if not args.image.is_file():
        print(f"error: image not found: {args.image}", file=sys.stderr)
        sys.exit(2)

    raw = args.image.read_bytes()
    kind = args.kind or detect_kind(raw)
    print(f"image:  {args.image}")
    print(f"kind:   {kind}")
    print(f"size:   {len(raw):,} bytes")

    buffer = bytearray(raw)
    if kind == KIND_SYSTEM:
        changed, descriptor_reports, header_reports = fixup_system(buffer, dry_run=not args.write)
        print()
        print("system descriptors:")
        render_reports(kind, descriptor_reports)
        print()
        print("system outer header CRC:")
        render_reports(kind, header_reports)
    else:
        changed, header_reports = fixup_shdb(buffer, dry_run=not args.write)
        print()
        print("SHDb outer header CRC:")
        render_reports(kind, header_reports)

    if not changed:
        print()
        print("no changes needed; all integrity layers already consistent.")
        return

    if args.check:
        print()
        print("would patch the layers marked [FIX] above. rerun with --write to apply.")
        return

    target = args.output or args.image
    if not args.output and not args.no_backup:
        backup = args.image.with_suffix(args.image.suffix + ".bak")
        try:
            backup.unlink()
        except FileNotFoundError:
            pass
        shutil.copy2(args.image, backup)
        print(f"backup: {backup}")
    target.write_bytes(bytes(buffer))
    print(f"wrote:  {target}")


if __name__ == "__main__":
    main()
