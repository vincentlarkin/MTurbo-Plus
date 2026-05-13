#!/usr/bin/env python3
"""Generate a repeatable map of the active M-Turbo package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path

from patch_mturbo_splash import (
    PIXELS,
    SPLASH_FRAME_COUNT,
    SPLASH_POINTER_TABLE_OFFSET,
    decode_rle_with_consumed,
)
from verify_current_package import TIMER_ZLIB, crc32, find_u32_hits, zlib_info
from verify_current_package import descriptor_rows, header_crc, system_header_crc_end, u32


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_IMAGE = ROOT / "opt" / "TurboSystem_sw" / "51.80.300.021" / "image.bin"
SHDB_IMAGE = ROOT / "opt" / "TurboSHDb" / "50.80.111.018" / "image.bin"
TEMPFL = ROOT / "opt" / "TurboSystem_sw" / "51.80.300.021" / "eFilmLite" / "tempFL.bin"
ASCII_RE = re.compile(rb"[\x20-\x7e]{8,}")


@dataclass
class FileInfo:
    path: str
    size: int
    crc32: str
    sha256: str
    header_ascii: str


@dataclass
class ZlibStreamInfo:
    offset: int
    compressed_len: int
    inflated_len: int
    stream_crc32: str
    payload_crc32: str
    payload_adler32: str
    anchors: list[str]


@dataclass
class SyncRegionInfo:
    index: int
    offset: int
    next_offset: int
    size: int
    note: str


@dataclass
class HeaderCRCInfo:
    stored: str
    calculated: str
    covered_start: int
    covered_end: int
    matches: bool


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ascii_preview(data: bytes, size: int = 64) -> str:
    chunk = data[:size]
    return "".join(chr(value) if 32 <= value < 127 else "." for value in chunk)


def file_info(path: Path) -> FileInfo:
    data = path.read_bytes()
    return FileInfo(
        path=str(path.relative_to(ROOT)),
        size=len(data),
        crc32=crc32(data),
        sha256=sha256(data),
        header_ascii=ascii_preview(data),
    )


def header_crc_info(data: bytes, covered_end: int) -> HeaderCRCInfo:
    stored = u32(data, 4)
    calculated = header_crc(data, covered_end)
    return HeaderCRCInfo(
        stored=f"{stored:08x}",
        calculated=f"{calculated:08x}",
        covered_start=8,
        covered_end=covered_end,
        matches=stored == calculated,
    )


def is_zlib_header(first: int, second: int) -> bool:
    if first & 0x0F != 8:
        return False
    if first >> 4 > 7:
        return False
    return ((first << 8) + second) % 31 == 0


def stream_anchors(payload: bytes) -> list[str]:
    probes = [
        b"IMAGE.BIN",
        b"\\opt\\TurboSystem_sw",
        b"\\opt\\TurboSHDb",
        b"aUpgradeFWReader",
        b"aUpgradeSHReader",
        b"ffss-service@fujifilm.com",
        b"System Information",
        b"Mini Boot SW Ver",
        b"Admin Login-",
    ]
    return [probe.decode("ascii") for probe in probes if probe in payload]


def scan_zlib_streams(data: bytes, min_inflated: int) -> list[ZlibStreamInfo]:
    streams: list[ZlibStreamInfo] = []
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
        stream = data[index : index + consumed]
        streams.append(
            ZlibStreamInfo(
                offset=index,
                compressed_len=consumed,
                inflated_len=len(payload),
                stream_crc32=crc32(stream),
                payload_crc32=crc32(payload),
                payload_adler32=f"{zlib.adler32(payload) & 0xffffffff:08x}",
                anchors=stream_anchors(payload),
            )
        )
        index += max(consumed, 1)
    return streams


def sync_regions(system_data: bytes, streams: list[ZlibStreamInfo]) -> list[SyncRegionInfo]:
    sync_word = bytes.fromhex("5599aa66")
    offsets = [match.start() for match in re.finditer(re.escape(sync_word), system_data)]
    first_stream = min((stream.offset for stream in streams), default=len(system_data))
    boundaries = sorted(offsets + [first_stream])
    regions = []
    for index, offset in enumerate(offsets):
        next_candidates = [candidate for candidate in boundaries if candidate > offset]
        next_offset = min(next_candidates) if next_candidates else len(system_data)
        regions.append(
            SyncRegionInfo(
                index=index,
                offset=offset,
                next_offset=next_offset,
                size=next_offset - offset,
                note="Xilinx-style sync word / boot configuration region; do not patch casually",
            )
        )
    return regions


def splash_map(system_data: bytes) -> list[dict[str, object]]:
    ptrs = [
        int.from_bytes(system_data[SPLASH_POINTER_TABLE_OFFSET + i * 4 : SPLASH_POINTER_TABLE_OFFSET + i * 4 + 4], "little")
        for i in range(SPLASH_FRAME_COUNT)
    ]
    frames = []
    for index, start in enumerate(ptrs):
        end = ptrs[index + 1] if index + 1 < len(ptrs) else SPLASH_POINTER_TABLE_OFFSET
        chunk = system_data[start:end]
        decoded = True
        consumed = 0
        try:
            pixels, consumed = decode_rle_with_consumed(chunk)
            decoded = len(pixels) == PIXELS
        except SystemExit:
            decoded = False
        frames.append(
            {
                "index": index,
                "start": start,
                "end": end,
                "size": end - start,
                "decoded": decoded,
                "rle_consumed": consumed,
                "trailing_nonzero": sum(1 for value in chunk[consumed:] if value) if decoded else None,
                "crc32": crc32(chunk),
            }
        )
    return frames


def ascii_clusters(data: bytes, limit: int = 20, gap: int = 0x200) -> list[dict[str, int]]:
    hits = [(match.start(), match.end()) for match in ASCII_RE.finditer(data)]
    if not hits:
        return []
    clusters: list[dict[str, int]] = []
    start, end = hits[0]
    count = 1
    for hit_start, hit_end in hits[1:]:
        if hit_start - end <= gap:
            end = max(end, hit_end)
            count += 1
            continue
        clusters.append({"start": start, "end": end, "size": end - start, "strings": count})
        start, end, count = hit_start, hit_end, 1
    clusters.append({"start": start, "end": end, "size": end - start, "strings": count})
    return sorted(clusters, key=lambda item: item["strings"], reverse=True)[:limit]


def constant_map(system_data: bytes, payload: bytes, stream: bytes, consumed: int) -> list[dict[str, object]]:
    excluded = (TIMER_ZLIB, TIMER_ZLIB + consumed)
    constants = {
        "zlib compressed length": consumed,
        "zlib inflated length": len(payload),
        "zlib stream crc32": zlib.crc32(stream) & 0xffffffff,
        "zlib payload crc32": zlib.crc32(payload) & 0xffffffff,
        "zlib payload adler32": zlib.adler32(payload) & 0xffffffff,
        "system file length": len(system_data),
        "system file crc32": zlib.crc32(system_data) & 0xffffffff,
    }
    rows = []
    for label, value in constants.items():
        rows.append(
            {
                "label": label,
                "value": f"0x{value:08x}",
                "outside_hits": [
                    {"endian": endian, "offsets": offsets, "count": count}
                    for endian, offsets, count in find_u32_hits(system_data, value, excluded)
                ],
            }
        )
    return rows


def shdb_resource_hints(data: bytes, limit: int = 80) -> list[dict[str, object]]:
    names = []
    seen = set()
    for match in re.finditer(rb"SHDb[A-Za-z0-9_]{2,32}\.bin", data, flags=re.IGNORECASE):
        name = match.group().decode("ascii", errors="replace")
        if (match.start(), name) in seen:
            continue
        seen.add((match.start(), name))
        names.append({"offset": match.start(), "name": name})
        if len(names) >= limit:
            break
    return names


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Firmware Map",
        "",
        "Generated by `tools/firmware_map.py`.",
        "",
        "## Files",
        "",
        "| File | Size | CRC32 | SHA256 |",
        "| --- | ---: | --- | --- |",
    ]
    for item in report["files"]:
        lines.append(f"| `{item['path']}` | {item['size']} | `{item['crc32']}` | `{item['sha256']}` |")

    lines.extend(["", "## System Zlib Streams", ""])
    for stream in report["system_zlib_streams"]:
        anchors = ", ".join(f"`{anchor}`" for anchor in stream["anchors"]) or "none"
        lines.append(
            f"- `0x{stream['offset']:x}` compressed `0x{stream['compressed_len']:x}`, "
            f"inflated `0x{stream['inflated_len']:x}`, stream CRC32 `{stream['stream_crc32']}`, "
            f"payload CRC32 `{stream['payload_crc32']}`, Adler32 `{stream['payload_adler32']}`, anchors: {anchors}"
        )

    lines.extend(["", "## Outer Header CRCs", ""])
    system_crc = report["system_outer_header_crc"]
    shdb_crc = report["shdb_outer_header_crc"]
    lines.append(
        f"- system: stored `{system_crc['stored']}`, calculated `{system_crc['calculated']}`, "
        f"range `0x{system_crc['covered_start']:x}:0x{system_crc['covered_end']:x}`, matches `{system_crc['matches']}`"
    )
    lines.append(
        f"- SHDb: stored `{shdb_crc['stored']}`, calculated `{shdb_crc['calculated']}`, "
        f"range `0x{shdb_crc['covered_start']:x}:0x{shdb_crc['covered_end']:x}`, matches `{shdb_crc['matches']}`"
    )

    lines.extend(["", "## System Zlib Descriptors", ""])
    for row in report["system_zlib_descriptors"]:
        lines.append(
            f"- {row['label']}: desc `0x{row['descriptor']:x}`, magic `0x{row['magic']:08x}`, "
            f"stored word `0x{row['stored_word']:08x}`, start field `0x{row['start_field']:x}`, "
            f"end field `0x{row['end_field']:x}`, stream `0x{row['stream_offset']:x}`"
        )

    lines.extend(["", "## System Sync Word Regions", ""])
    for region in report["system_sync_regions"]:
        lines.append(
            f"- region {region['index']}: `0x{region['offset']:x}-0x{region['next_offset']:x}`, "
            f"size `0x{region['size']:x}`; {region['note']}"
        )
    if not report["system_sync_regions"]:
        lines.append("- none found")

    lines.extend(["", "## Splash Frames", ""])
    for frame in report["splash_frames"]:
        lines.append(
            f"- frame {frame['index']:02d}: `0x{frame['start']:x}-0x{frame['end']:x}`, "
            f"size `{frame['size']}`, consumed `{frame['rle_consumed']}`, crc32 `{frame['crc32']}`"
        )

    lines.extend(["", "## Candidate Constants", ""])
    for row in report["candidate_constants"]:
        if not row["outside_hits"]:
            lines.append(f"- {row['label']} `{row['value']}`: no outside hits")
            continue
        chunks = []
        for hit in row["outside_hits"]:
            offsets = ", ".join(f"`0x{offset:x}`" for offset in hit["offsets"])
            chunks.append(f"{hit['endian']} {offsets} count {hit['count']}")
        lines.append(f"- {row['label']} `{row['value']}`: {'; '.join(chunks)}")

    lines.extend(["", "## SHDb Resource Name Hints", ""])
    for item in report["shdb_resource_hints"]:
        lines.append(f"- `0x{item['offset']:x}` `{item['name']}`")
    if not report["shdb_resource_hints"]:
        lines.append("- none found")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=ROOT / "analysis" / "firmware_map.json")
    parser.add_argument("--markdown", type=Path, default=ROOT / "analysis" / "firmware_map.md")
    parser.add_argument("--min-zlib-inflated", type=int, default=0x1000)
    args = parser.parse_args()

    system_data = SYSTEM_IMAGE.read_bytes()
    shdb_data = SHDB_IMAGE.read_bytes()
    tempfl_data = TEMPFL.read_bytes()
    payload, consumed, stream = zlib_info(system_data)
    system_streams = scan_zlib_streams(system_data, args.min_zlib_inflated)

    report = {
        "files": [
            asdict(file_info(SYSTEM_IMAGE)),
            asdict(file_info(SHDB_IMAGE)),
            asdict(file_info(TEMPFL)),
        ],
        "system_header_version": system_data[8:21].decode("ascii", errors="replace"),
        "shdb_header_version": shdb_data[8:21].decode("ascii", errors="replace"),
        "system_outer_header_crc": asdict(header_crc_info(system_data, system_header_crc_end(system_data))),
        "shdb_outer_header_crc": asdict(header_crc_info(shdb_data, len(shdb_data))),
        "system_zlib_descriptors": descriptor_rows(system_data),
        "tempfl_text": tempfl_data.decode("ascii", errors="replace"),
        "system_zlib_streams": [asdict(item) for item in system_streams],
        "system_sync_regions": [asdict(item) for item in sync_regions(system_data, system_streams)],
        "splash_pointer_table": SPLASH_POINTER_TABLE_OFFSET,
        "splash_frames": splash_map(system_data),
        "candidate_constants": constant_map(system_data, payload, stream, consumed),
        "system_ascii_clusters": ascii_clusters(system_data),
        "shdb_resource_hints": shdb_resource_hints(shdb_data),
    }

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    args.markdown.write_text(render_markdown(report), encoding="ascii")
    print(f"wrote {args.json.relative_to(ROOT)}")
    print(f"wrote {args.markdown.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
