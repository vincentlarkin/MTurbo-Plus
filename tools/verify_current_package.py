#!/usr/bin/env python3
"""Verify the current stock-parity folder-bump package."""

from __future__ import annotations

import argparse
import hashlib
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIMER_ZLIB = 0x24BBB5
SYSTEM_HEADER_CRC_END_FIELD = 0x20

sys.path.insert(0, str(ROOT))
from tools.patch_mturbo_splash import SPLASH_FRAME_COUNT, SPLASH_POINTER_TABLE_OFFSET, decode_rle_with_consumed  # noqa: E402


def check(label: str, ok: bool, detail: str = "") -> int:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label}{(' - ' + detail) if detail else ''}")
    return 0 if ok else 1


def crc32(data: bytes) -> str:
    return f"{zlib.crc32(data) & 0xffffffff:08x}"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little")


def header_crc(data: bytes, end: int) -> int:
    return zlib.crc32(data[8:end]) & 0xffffffff


def system_header_crc_end(data: bytes) -> int:
    return u32(data, SYSTEM_HEADER_CRC_END_FIELD)


def diff_ranges(left: bytes, right: bytes, limit: int = 8) -> tuple[int, list[tuple[int, int]]]:
    ranges: list[tuple[int, int]] = []
    diff_bytes = 0
    size = min(len(left), len(right))
    index = 0
    while index < size:
        if left[index] == right[index]:
            index += 1
            continue
        start = index
        while index < size and left[index] != right[index]:
            index += 1
        diff_bytes += index - start
        if len(ranges) < limit:
            ranges.append((start, index))
    if len(left) != len(right):
        start = size
        end = max(len(left), len(right))
        diff_bytes += end - start
        if len(ranges) < limit:
            ranges.append((start, end))
    return diff_bytes, ranges


def zlib_info(data: bytes) -> tuple[bytes, int, bytes]:
    obj = zlib.decompressobj()
    payload = obj.decompress(data[TIMER_ZLIB:])
    if not obj.eof:
        raise ValueError("zlib stream did not terminate")
    consumed = len(data) - TIMER_ZLIB - len(obj.unused_data)
    stream = data[TIMER_ZLIB : TIMER_ZLIB + consumed]
    return payload, consumed, stream


def print_file_details(label: str, current: bytes, stock: bytes) -> None:
    print(f"{label}:")
    print(f"  current size={len(current)} crc32={crc32(current)} sha256={sha256(current)}")
    print(f"  stock   size={len(stock)} crc32={crc32(stock)} sha256={sha256(stock)}")
    if current == stock:
        print("  parity: byte-identical")
        return
    diff_bytes, ranges = diff_ranges(stock, current)
    print(f"  parity: differs by {diff_bytes} byte(s)")
    for start, end in ranges:
        print(f"    diff 0x{start:08x}-0x{end:08x} len={end - start}")


def find_u32_hits(data: bytes, value: int, excluded: tuple[int, int]) -> list[tuple[str, list[int], int]]:
    results: list[tuple[str, list[int], int]] = []
    for endian in ("little", "big"):
        pattern = value.to_bytes(4, endian)
        hits: list[int] = []
        count = 0
        start = 0
        while True:
            offset = data.find(pattern, start)
            if offset < 0:
                break
            start = offset + 1
            if excluded[0] <= offset < excluded[1]:
                continue
            count += 1
            if len(hits) < 8:
                hits.append(offset)
        if count:
            results.append((endian, hits, count))
    return results


def print_deep_constant_search(stock_image: bytes, stock_payload: bytes, stock_stream: bytes, stock_consumed: int) -> None:
    excluded = (TIMER_ZLIB, TIMER_ZLIB + stock_consumed)
    values = {
        "zlib compressed length": stock_consumed,
        "zlib inflated length": len(stock_payload),
        "zlib stream crc32": zlib.crc32(stock_stream) & 0xffffffff,
        "zlib payload crc32": zlib.crc32(stock_payload) & 0xffffffff,
        "zlib payload adler32": zlib.adler32(stock_payload) & 0xffffffff,
        "system file length": len(stock_image),
        "system file crc32": zlib.crc32(stock_image) & 0xffffffff,
    }

    print()
    print("deep constant search:")
    any_hits = False
    for label, value in values.items():
        hits = find_u32_hits(stock_image, value, excluded)
        if not hits:
            print(f"  {label}=0x{value:08x}: no outside hits")
            continue
        any_hits = True
        rendered = []
        for endian, offsets, count in hits:
            shown = ", ".join(f"0x{offset:x}" for offset in offsets)
            rendered.append(f"{endian} [{shown}] count={count}")
        print(f"  {label}=0x{value:08x}: {'; '.join(rendered)}")
    if not any_hits:
        print("  no simple 32-bit length/checksum fields found outside the zlib stream")


def descriptor_rows(data: bytes) -> list[dict[str, int | str]]:
    specs = [
        ("stream1", 0x24BB9C, 0x0C, 0x10),
        ("stream2", 0x676104, 0x18, 0x1C),
        ("stream3", 0x677516, 0x08, 0x0C),
        ("stream4", 0x677D42, 0x08, 0x0C),
        ("stream5", 0x1323127, 0x08, 0x0C),
    ]
    rows = []
    for label, offset, start_field, end_field in specs:
        start = u32(data, offset + start_field)
        end = u32(data, offset + end_field)
        stream_offset = start + 1
        rows.append(
            {
                "label": label,
                "descriptor": offset,
                "magic": u32(data, offset),
                "stored_word": u32(data, offset + 4),
                "start_field": start,
                "end_field": end,
                "stream_offset": stream_offset,
                "compression_flag": data[stream_offset - 1] if 0 <= stream_offset - 1 < len(data) else -1,
                "zlib_header": u32(data, stream_offset) & 0xffff if 0 <= stream_offset < len(data) - 1 else -1,
            }
        )
    return rows


def print_header_details(system_data: bytes, shdb_data: bytes) -> None:
    system_end = system_header_crc_end(system_data)
    print()
    print("outer header CRCs:")
    print(
        f"  system stored=0x{u32(system_data, 4):08x} calc=0x{header_crc(system_data, system_end):08x} "
        f"range=0x8:0x{system_end:x}"
    )
    print(
        f"  SHDb   stored=0x{u32(shdb_data, 4):08x} calc=0x{header_crc(shdb_data, len(shdb_data)):08x} "
        f"range=0x8:0x{len(shdb_data):x}"
    )
    print()
    print("system zlib descriptor table:")
    for row in descriptor_rows(system_data):
        print(
            f"  {row['label']}: desc=0x{row['descriptor']:x} magic=0x{row['magic']:08x} "
            f"stored_word=0x{row['stored_word']:08x} start_field=0x{row['start_field']:x} "
            f"end_field=0x{row['end_field']:x} stream=0x{row['stream_offset']:x} "
            f"flag=0x{row['compression_flag']:02x} zlib_header=0x{row['zlib_header']:04x}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--details", action="store_true", help="print CRC32/SHA256 and zlib details")
    parser.add_argument("--deep", action="store_true", help="search for obvious 32-bit checksum/length fields")
    args = parser.parse_args()

    failures = 0
    system = ROOT / "opt" / "TurboSystem_sw" / "51.80.300.021" / "image.bin"
    shdb = ROOT / "opt" / "TurboSHDb" / "50.80.111.018" / "image.bin"
    tempfl = ROOT / "opt" / "TurboSystem_sw" / "51.80.300.021" / "eFilmLite" / "tempFL.bin"
    clean_system = ROOT / "3.0clean" / "opt" / "TurboSystem_sw" / "51.80.300.015" / "image.bin"
    clean_shdb = ROOT / "3.0clean" / "opt" / "TurboSHDb" / "50.80.111.012" / "image.bin"
    clean_tempfl = ROOT / "3.0clean" / "opt" / "TurboSystem_sw" / "51.80.300.015" / "eFilmLite" / "tempFL.bin"

    failures += check("system path exists", system.is_file(), str(system.relative_to(ROOT)))
    failures += check("SHDb path exists", shdb.is_file(), str(shdb.relative_to(ROOT)))
    failures += check("tempFL path exists", tempfl.is_file(), str(tempfl.relative_to(ROOT)))
    if failures:
        sys.exit(1)

    system_data = system.read_bytes()
    shdb_data = shdb.read_bytes()
    tempfl_data = tempfl.read_bytes()
    clean_system_data = clean_system.read_bytes()
    clean_shdb_data = clean_shdb.read_bytes()
    clean_tempfl_data = clean_tempfl.read_bytes()
    failures += check("system file size matches stock", len(system_data) == len(clean_system_data), str(len(system_data)))
    failures += check("SHDb file size matches stock", len(shdb_data) == len(clean_shdb_data), str(len(shdb_data)))
    failures += check("tempFL file size matches stock", len(tempfl_data) == len(clean_tempfl_data), str(len(tempfl_data)))
    failures += check("system embedded header is stock", b"51.80.300.015" in system_data[:0x40])
    failures += check("SHDb embedded header is stock", b"50.80.111.012" in shdb_data[:0x40])
    system_crc_end = system_header_crc_end(system_data)
    failures += check(
        "system outer header CRC matches",
        u32(system_data, 4) == header_crc(system_data, system_crc_end),
        f"stored=0x{u32(system_data, 4):08x} calc=0x{header_crc(system_data, system_crc_end):08x} range=0x8:0x{system_crc_end:x}",
    )
    failures += check(
        "SHDb outer header CRC matches",
        u32(shdb_data, 4) == header_crc(shdb_data, len(shdb_data)),
        f"stored=0x{u32(shdb_data, 4):08x} calc=0x{header_crc(shdb_data, len(shdb_data)):08x} range=0x8:0x{len(shdb_data):x}",
    )
    for row in descriptor_rows(system_data):
        failures += check(
            f"{row['label']} descriptor points at zlib",
            row["compression_flag"] == 0x08 and row["zlib_header"] == 0x9C78,
            f"desc=0x{row['descriptor']:x} stream=0x{row['stream_offset']:x} stored_word=0x{row['stored_word']:08x}",
        )
    failures += check(
        "system image matches stock bytes",
        system_data == clean_system_data,
        f"current_crc32={crc32(system_data)} stock_crc32={crc32(clean_system_data)}",
    )
    failures += check(
        "SHDb image matches stock bytes",
        shdb_data == clean_shdb_data,
        f"current_crc32={crc32(shdb_data)} stock_crc32={crc32(clean_shdb_data)}",
    )
    failures += check(
        "tempFL matches stock bytes",
        tempfl_data == clean_tempfl_data,
        f"current_crc32={crc32(tempfl_data)} stock_crc32={crc32(clean_tempfl_data)}",
    )

    ptrs = [
        int.from_bytes(system_data[SPLASH_POINTER_TABLE_OFFSET + i * 4 : SPLASH_POINTER_TABLE_OFFSET + i * 4 + 4], "little")
        for i in range(SPLASH_FRAME_COUNT)
    ]
    start, end = ptrs[0], ptrs[1]
    chunk = system_data[start:end]
    _indices, consumed = decode_rle_with_consumed(chunk)
    failures += check(
        "frame 0 splash is stock",
        chunk == clean_system_data[start:end] and consumed == end - start,
        f"chunk=0x{start:x}-0x{end:x} consumed={consumed}",
    )

    payload, consumed, stream = zlib_info(system_data)
    clean_payload, clean_consumed, clean_stream = zlib_info(clean_system_data)
    failures += check("main zlib payload decompresses", True, f"consumed={consumed}")
    failures += check(
        "main zlib stream matches stock",
        stream == clean_stream and consumed == clean_consumed,
        f"current_len=0x{consumed:x} stock_len=0x{clean_consumed:x}",
    )
    failures += check(
        "main zlib payload matches stock",
        payload == clean_payload,
        f"current_crc32={crc32(payload)} stock_crc32={crc32(clean_payload)}",
    )
    failures += check(
        "contact string remains stock",
        payload.count(b"ffss-service@fujifilm.com") == 1 and b"MT STRING VISIBLE 2019!!!" not in payload,
        f"stock={payload.count(b'ffss-service@fujifilm.com')} "
        f"patched={payload.count(b'MT STRING VISIBLE 2019!!!')}",
    )
    failures += check(
        "sysinfo labels remain stock",
        payload.count(b"Mini Boot SW Ver") == 2 and b"MT VISIBLE 2019!" not in payload,
        f"stock={payload.count(b'Mini Boot SW Ver')} patched={payload.count(b'MT VISIBLE 2019!')}",
    )

    if args.details or args.deep:
        print()
        print_file_details("system image", system_data, clean_system_data)
        print_file_details("SHDb image", shdb_data, clean_shdb_data)
        print_file_details("tempFL", tempfl_data, clean_tempfl_data)
        print()
        print("system zlib:")
        print(f"  offset=0x{TIMER_ZLIB:x}")
        print(f"  current compressed_len=0x{consumed:x} inflated_len=0x{len(payload):x}")
        print(f"  stock   compressed_len=0x{clean_consumed:x} inflated_len=0x{len(clean_payload):x}")
        print(f"  current stream_crc32={crc32(stream)} payload_crc32={crc32(payload)} adler32={zlib.adler32(payload) & 0xffffffff:08x}")
        print(f"  stock   stream_crc32={crc32(clean_stream)} payload_crc32={crc32(clean_payload)} adler32={zlib.adler32(clean_payload) & 0xffffffff:08x}")
        print_header_details(system_data, shdb_data)

    if args.deep:
        print_deep_constant_search(clean_system_data, clean_payload, clean_stream, clean_consumed)

    if failures:
        print(f"verification FAILED: {failures}")
        sys.exit(1)
    print("verification PASSED")


if __name__ == "__main__":
    main()
