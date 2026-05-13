#!/usr/bin/env python3
"""Build one named test package in opt/ from stock inputs."""

from __future__ import annotations

import argparse
import sys
import zlib
from pathlib import Path

from PIL import Image

from patch_contact_visible_string import ORIGINAL as CONTACT_ORIGINAL
from patch_contact_visible_string import PATCHED as CONTACT_PATCHED
from patch_larkrom_rebrand import patch_image as patch_larkrom_rebrand_image
from patch_mturbo_splash import (
    MTURBO_SPLASH_INDEX,
    SPLASH_FRAME_COUNT,
    SPLASH_POINTER_TABLE_OFFSET,
    EGA_PREVIEW_PALETTE,
    build_blue_wireframe,
    build_larkrom_blueboot,
    decode_rle_with_consumed,
    encode_rle_exact,
    render,
    splash_pointers,
)
from patch_mturbo_strings import KNOWN_TIMER_ZLIB_OFFSET, best_recompress, decompress_stream
from rebuild_stock_parity_package import main as rebuild_stock_parity
from recompute_image_checksums import (
    detect_kind as detect_image_kind,
    fixup_shdb,
    fixup_system,
)
from verify_current_package import crc32, diff_ranges, zlib_info


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_IMAGE = ROOT / "opt" / "TurboSystem_sw" / "51.80.300.021" / "image.bin"
STOCK_SYSTEM_IMAGE = ROOT / "3.0clean" / "opt" / "TurboSystem_sw" / "51.80.300.015" / "image.bin"
SHDB_IMAGE = ROOT / "opt" / "TurboSHDb" / "50.80.111.018" / "image.bin"
STOCK_SHDB_IMAGE = ROOT / "3.0clean" / "opt" / "TurboSHDb" / "50.80.111.012" / "image.bin"
TEMPFL = ROOT / "opt" / "TurboSystem_sw" / "51.80.300.021" / "eFilmLite" / "tempFL.bin"
STOCK_TEMPFL = ROOT / "3.0clean" / "opt" / "TurboSystem_sw" / "51.80.300.015" / "eFilmLite" / "tempFL.bin"
MANIFEST = ROOT / "analysis" / "current_test_package.md"
LARKROM_SPLASH_PREVIEW_DIR = ROOT / "analysis" / "splash_larkrom_preview"


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def write_system(data: bytearray) -> None:
    SYSTEM_IMAGE.write_bytes(data)


def is_zlib_header(first: int, second: int) -> bool:
    if first & 0x0F != 8:
        return False
    if first >> 4 > 7:
        return False
    return ((first << 8) + second) % 31 == 0


def zlib_ranges(data: bytes, min_inflated: int = 0x1000) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    index = 0
    while index < len(data) - 2:
        if data[index] != 0x78 or not is_zlib_header(data[index], data[index + 1]):
            index += 1
            continue
        obj = zlib.decompressobj()
        try:
            payload = obj.decompress(data[index:])
        except zlib.error:
            index += 1
            continue
        if not obj.eof or len(payload) < min_inflated:
            index += 1
            continue
        consumed = len(data) - index - len(obj.unused_data)
        ranges.append((index, index + consumed))
        index += max(consumed, 1)
    return ranges


def inside_any(offset: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= offset < end for start, end in ranges)


def longest_zero_run_outside_zlib(data: bytes) -> tuple[int, int]:
    ranges = zlib_ranges(data)
    best = (0, 0)
    index = 0
    while index < len(data):
        if data[index] != 0 or inside_any(index, ranges):
            index += 1
            continue
        start = index
        while index < len(data) and data[index] == 0 and not inside_any(index, ranges):
            index += 1
        if index - start > best[1] - best[0]:
            best = (start, index)
    if best[1] - best[0] < 0x400:
        fail("could not find a long zero run outside zlib streams")
    return best


def patch_system_slack_byte(data: bytearray) -> str:
    start, end = longest_zero_run_outside_zlib(bytes(data))
    offset = start + ((end - start) // 2)
    data[offset] = 1
    write_system(data)
    return f"changed one byte in longest zero run 0x{start:x}-0x{end:x} at system offset 0x{offset:x}: 00 -> 01"


def patch_system_outer_copyright(data: bytearray) -> str:
    old = b"Copyright 1984-1996 Wind River Systems, Inc."
    new = b"Copyright 1984-1996 Wind River Systems, MT!"
    if len(old) != len(new):
        fail("copyright replacement must be length-preserving")
    offset = bytes(data).find(old)
    if offset < 0:
        fail("stock Wind River copyright string not found")
    data[offset : offset + len(old)] = new
    write_system(data)
    return f"changed outer uncompressed copyright at system offset 0x{offset:x}"


def patch_zlib_recompress_noop(data: bytearray) -> str:
    payload, stream_len = decompress_stream(data, KNOWN_TIMER_ZLIB_OFFSET)
    new_stream = same_length_recompress(payload, stream_len)
    if new_stream == bytes(data[KNOWN_TIMER_ZLIB_OFFSET : KNOWN_TIMER_ZLIB_OFFSET + stream_len]):
        fail("best recompression matched stock stream exactly; no useful test diff")
    if len(new_stream) != stream_len:
        fail(f"noop recompress length changed: {len(new_stream)} != {stream_len}")
    data[KNOWN_TIMER_ZLIB_OFFSET : KNOWN_TIMER_ZLIB_OFFSET + stream_len] = new_stream
    write_system(data)
    return f"recompressed identical zlib payload with original stream length 0x{stream_len:x}"


def same_length_recompress(payload: bytes, target_len: int) -> bytes:
    compressor = zlib.compressobj(
        9,
        zlib.DEFLATED,
        zlib.MAX_WBITS,
        zlib.DEF_MEM_LEVEL,
        zlib.Z_DEFAULT_STRATEGY,
    )
    prefix = compressor.compress(payload) + compressor.flush(zlib.Z_SYNC_FLUSH)
    finish = compressor.flush(zlib.Z_FINISH)
    pad_len = target_len - len(prefix) - len(finish)
    empty_stored_block = b"\x00\x00\x00\xff\xff"
    if pad_len < 0 or pad_len % len(empty_stored_block):
        fail(
            "could not make exact-length zlib no-op stream: "
            f"target={target_len} prefix={len(prefix)} finish={len(finish)} pad={pad_len}"
        )
    new_stream = prefix + empty_stored_block * (pad_len // len(empty_stored_block)) + finish
    check_payload, check_len = decompress_stream(new_stream, 0)
    if check_len != target_len:
        fail(f"exact-length zlib no-op consumed 0x{check_len:x}, expected 0x{target_len:x}")
    if check_payload != payload:
        fail("exact-length zlib no-op payload changed")
    return new_stream


def patch_contact_string(data: bytearray) -> str:
    payload, stream_len = decompress_stream(data, KNOWN_TIMER_ZLIB_OFFSET)
    blob = bytearray(payload)
    offset = blob.find(CONTACT_ORIGINAL)
    if offset < 0:
        fail("stock contact string not found in zlib payload")
    blob[offset : offset + len(CONTACT_ORIGINAL)] = CONTACT_PATCHED
    new_stream = best_recompress(bytes(blob))
    if len(new_stream) > stream_len:
        fail(f"contact patch grew stream: {len(new_stream)} > {stream_len}")
    data[KNOWN_TIMER_ZLIB_OFFSET : KNOWN_TIMER_ZLIB_OFFSET + len(new_stream)] = new_stream
    data[KNOWN_TIMER_ZLIB_OFFSET + len(new_stream) : KNOWN_TIMER_ZLIB_OFFSET + stream_len] = (
        b"\x00" * (stream_len - len(new_stream))
    )
    write_system(data)
    return f"patched contact string at inflated zlib offset 0x{offset:x}"


def patch_embedded_header_version(data: bytearray) -> str:
    old = b"51.80.300.015"
    new = b"51.80.300.021"
    offset = bytes(data[:0x40]).find(old)
    if offset < 0:
        fail("stock embedded system version not found in header")
    data[offset : offset + len(old)] = new
    write_system(data)
    return f"changed embedded system header version at offset 0x{offset:x}; known-fail control"


def patch_tempfl_byte(_data: bytearray) -> str:
    data = bytearray(TEMPFL.read_bytes())
    offset = len(data) - 1
    old = data[offset]
    data[offset] = old ^ 0x01
    TEMPFL.write_bytes(data)
    return f"changed tempFL byte at offset 0x{offset:x}: {old:02x} -> {data[offset]:02x}"


def longest_zero_run(data: bytes) -> tuple[int, int]:
    best = (0, 0)
    index = 0
    while index < len(data):
        if data[index] != 0:
            index += 1
            continue
        start = index
        while index < len(data) and data[index] == 0:
            index += 1
        if index - start > best[1] - best[0]:
            best = (start, index)
    if best[1] - best[0] < 0x400:
        fail("could not find a long zero run")
    return best


def patch_shdb_slack_byte(_data: bytearray) -> str:
    data = bytearray(SHDB_IMAGE.read_bytes())
    start, end = longest_zero_run(bytes(data))
    offset = start + ((end - start) // 2)
    data[offset] = 1
    SHDB_IMAGE.write_bytes(data)
    return f"changed one SHDb byte in longest zero run 0x{start:x}-0x{end:x} at offset 0x{offset:x}: 00 -> 01"


def patch_splash_blueboot(data: bytearray) -> str:
    ptrs = splash_pointers(bytes(data))
    start = ptrs[MTURBO_SPLASH_INDEX]
    end = ptrs[MTURBO_SPLASH_INDEX + 1]
    chunk = bytes(data[start:end])
    original_indices, _ = decode_rle_with_consumed(chunk)
    patched_indices = build_blue_wireframe(original_indices)
    repacked = encode_rle_exact(patched_indices, len(chunk))
    if repacked == chunk:
        fail("blueboot splash already matches; nothing to write")
    data[start:end] = repacked
    write_system(data)
    return (
        f"replaced boot splash frame 0 with blueboot wireframe at outer offset "
        f"0x{start:x}..0x{end:x} ({len(chunk)} bytes, length-preserving RLE)"
    )


def patch_splash_and_contact(data: bytearray) -> str:
    splash_msg = patch_splash_blueboot(data)
    data = bytearray(SYSTEM_IMAGE.read_bytes())
    contact_msg = patch_contact_string(data)
    return f"{splash_msg}\n{contact_msg}"


def write_larkrom_splash_previews(frames: list[bytes | bytearray]) -> None:
    LARKROM_SPLASH_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    thumbs: list[Image.Image] = []
    for index, frame in enumerate(frames):
        preview = render(frame, EGA_PREVIEW_PALETTE)
        preview.save(LARKROM_SPLASH_PREVIEW_DIR / f"frame_{index:02d}_ega.png")
        if index == 0:
            preview.save(LARKROM_SPLASH_PREVIEW_DIR / "splash_preview.png")
        thumbs.append(preview.resize((160, 120)))

    if thumbs:
        sheet = Image.new("RGB", (160 * 4, 120 * ((len(thumbs) + 3) // 4)), (0, 0, 0))
        for index, thumb in enumerate(thumbs):
            sheet.paste(thumb, ((index % 4) * 160, (index // 4) * 120))
        sheet.save(LARKROM_SPLASH_PREVIEW_DIR / "contact_sheet_ega.png")


def patch_splash_larkrom_all(data: bytearray) -> str:
    ptrs = splash_pointers(bytes(data))
    base_start = ptrs[0]
    base_end = ptrs[1]
    base_original_indices, _ = decode_rle_with_consumed(bytes(data[base_start:base_end]))
    patched_frames: list[bytearray] = []
    changed_ranges: list[str] = []
    for index, start in enumerate(ptrs):
        end = ptrs[index + 1] if index + 1 < SPLASH_FRAME_COUNT else SPLASH_POINTER_TABLE_OFFSET
        chunk = bytes(data[start:end])
        _original_indices, consumed = decode_rle_with_consumed(chunk)
        patched_indices = build_larkrom_blueboot(base_original_indices, index)
        repacked = encode_rle_exact(patched_indices, consumed) + chunk[consumed:]
        data[start:end] = repacked
        patched_frames.append(patched_indices)
        changed_ranges.append(f"frame {index:02d} 0x{start:x}..0x{end:x} ({len(chunk)} bytes)")

    write_system(data)
    write_larkrom_splash_previews(patched_frames)
    return (
        "replaced all 12 boot splash frames with the LarkROM Blueboot animation:\n"
        + "\n".join(f"- {line}" for line in changed_ranges)
        + f"\npreview written: {LARKROM_SPLASH_PREVIEW_DIR.relative_to(ROOT)}"
    )


def patch_larkrom_bundle(data: bytearray) -> str:
    splash_msg = patch_splash_larkrom_all(data)
    string_msg = patch_larkrom_rebrand_image(SYSTEM_IMAGE)
    return f"{splash_msg}\n{string_msg}"


VARIANTS = {
    "stock": lambda data: "rebuilt stock-parity package; no binary changes",
    "system-slack-byte": patch_system_slack_byte,
    "system-outer-copyright": patch_system_outer_copyright,
    "system-zlib-recompress-noop": patch_zlib_recompress_noop,
    "system-contact-string": patch_contact_string,
    "system-splash-blueboot": patch_splash_blueboot,
    "system-blueboot-bundle": patch_splash_and_contact,
    "system-larkrom-bundle": patch_larkrom_bundle,
    "system-header-version": patch_embedded_header_version,
    "shdb-slack-byte": patch_shdb_slack_byte,
    "tempfl-byte": patch_tempfl_byte,
}


def file_diff_lines(label: str, stock_path: Path, current_path: Path, limit: int = 8) -> list[str]:
    stock = stock_path.read_bytes()
    current = current_path.read_bytes()
    diff_bytes, ranges = diff_ranges(stock, current, limit=12)
    lines = [
        f"{label} crc32 stock={crc32(stock)} current={crc32(current)}",
        f"{label} diff bytes={diff_bytes}",
    ]
    for start, end in ranges[:limit]:
        lines.append(f"  diff 0x{start:08x}-0x{end:08x} len={end - start}")
    return lines


def diff_summary_lines() -> list[str]:
    lines: list[str] = []
    for label, stock_path, current_path in [
        ("system image", STOCK_SYSTEM_IMAGE, SYSTEM_IMAGE),
        ("SHDb image", STOCK_SHDB_IMAGE, SHDB_IMAGE),
        ("tempFL", STOCK_TEMPFL, TEMPFL),
    ]:
        item_lines = file_diff_lines(label, stock_path, current_path)
        if lines:
            lines.append("")
        lines.extend(item_lines)
    return lines


def print_diff_summary() -> None:
    for line in diff_summary_lines():
        print(line)


def write_manifest(variant: str, message: str) -> None:
    lines = [
        "# Current Test Package",
        "",
        f"Variant: `{variant}`",
        "",
        message,
        "",
        "Diff summary:",
        "",
        "```text",
        *diff_summary_lines(),
        "```",
        "",
        "Reset to stock-parity baseline with:",
        "",
        "```powershell",
        "python -B .\\tools\\make_test_package.py stock",
        "```",
        "",
    ]
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text("\n".join(lines), encoding="ascii")
    print(f"manifest written: {MANIFEST.relative_to(ROOT)}")


def reseal_active_images(verbose: bool = True) -> list[str]:
    notes: list[str] = []
    for image_path in (SYSTEM_IMAGE, SHDB_IMAGE):
        if not image_path.is_file():
            continue
        buffer = bytearray(image_path.read_bytes())
        kind = detect_image_kind(bytes(buffer))
        changed = False
        if kind == "system":
            changed, descriptor_reports, header_reports = fixup_system(buffer, dry_run=False)
            if changed:
                image_path.write_bytes(bytes(buffer))
            for report in descriptor_reports + header_reports:
                if not report.matches:
                    notes.append(
                        f"sealed {image_path.name} {report.label}: 0x{report.stored:08x}"
                        f" -> 0x{report.calculated:08x}"
                    )
        else:
            changed, header_reports = fixup_shdb(buffer, dry_run=False)
            if changed:
                image_path.write_bytes(bytes(buffer))
            for report in header_reports:
                if not report.matches:
                    notes.append(
                        f"sealed {image_path.name} {report.label}: 0x{report.stored:08x}"
                        f" -> 0x{report.calculated:08x}"
                    )
    if verbose:
        if notes:
            for note in notes:
                print(note)
        else:
            print("integrity layers already consistent; nothing to seal")
    return notes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("variant", choices=sorted(VARIANTS))
    parser.add_argument(
        "--no-reseal",
        action="store_true",
        help="skip the auto reseal step (for reproducing pre-2026 broken-integrity tests)",
    )
    args = parser.parse_args()

    rebuild_stock_parity()
    data = bytearray(SYSTEM_IMAGE.read_bytes())
    message = VARIANTS[args.variant](data)
    print(f"variant: {args.variant}")
    print(message)
    if args.no_reseal:
        print("integrity reseal skipped (--no-reseal); package is intentionally broken-integrity")
        seal_notes: list[str] = []
    else:
        seal_notes = reseal_active_images()
    if seal_notes:
        message = message + "\n\nReseal:\n" + "\n".join(f"- {note}" for note in seal_notes)
    print_diff_summary()
    write_manifest(args.variant, message)


if __name__ == "__main__":
    main()
