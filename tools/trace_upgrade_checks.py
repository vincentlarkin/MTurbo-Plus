#!/usr/bin/env python3
"""Trace likely upgrade integrity checks in the system image.

This is intentionally read-only. It decompresses the known zlib streams from the
active system image, searches for upgrade/check strings, finds direct little
endian references to those strings, and disassembles nearby ARM code where the
main system payload appears to use raw payload offsets as addresses.
"""

from __future__ import annotations

import argparse
import re
import textwrap
import zlib
from dataclasses import dataclass
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN, Cs


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_IMAGE = ROOT / "opt" / "TurboSystem_sw" / "51.80.300.021" / "image.bin"
OUT = ROOT / "analysis" / "upgrade_check_trace.md"

STREAM_OFFSETS = [0x24BBB5, 0x676129, 0x67753B, 0x677D67, 0x132314C]

NEEDLES = [
    b"aUpgradeMgrImpl.cpp",
    b"AUpgradeMgr.cpp",
    b"aUpgradeReader.cpp",
    b"aUpgradeFWReader",
    b"aUpgradeSHReader",
    b"aUpgradeFWInstaller.cpp",
    b"aUpgradeSHInstaller.cpp",
    b"IMAGE.BIN",
    b"\\opt\\TurboSystem_sw",
    b"\\opt\\TurboSHDb",
    b"NULL != packHeader",
    b"versionStr",
    b"m_upgradeImageInfo.imagePath",
    b"upgradeFile.Open",
    b"TurboSHDbPackHeader",
    b"MountUpgradeFileSystem",
    b"Failed to create upgrade filesystem cbio device",
    b"Verifying CRC",
    b"ERROR (CRC)",
    b"Checksum mismatch",
    b"copyImageToDDR2",
    b"SHA256",
    b"MD5",
    b"RSAENH",
    b"signature",
]


@dataclass(frozen=True)
class Stream:
    index: int
    offset: int
    compressed_len: int
    payload: bytes


def decompress_streams(data: bytes) -> list[Stream]:
    streams = []
    for index, offset in enumerate(STREAM_OFFSETS, 1):
        obj = zlib.decompressobj()
        payload = obj.decompress(data[offset:])
        if not obj.eof:
            raise RuntimeError(f"stream at 0x{offset:x} did not reach zlib EOF")
        consumed = len(data) - offset - len(obj.unused_data)
        streams.append(Stream(index=index, offset=offset, compressed_len=consumed, payload=payload))
    return streams


def find_all(blob: bytes, needle: bytes) -> list[int]:
    return [match.start() for match in re.finditer(re.escape(needle), blob, re.IGNORECASE)]


def ascii_context(blob: bytes, offset: int, before: int = 64, after: int = 112) -> str:
    chunk = blob[max(0, offset - before) : offset + after]
    text = chunk.replace(b"\x00", b".").decode("ascii", errors="backslashreplace")
    return text.replace("\r", "\\r").replace("\n", "\\n")


def find_u32_refs(blob: bytes, value: int) -> list[int]:
    needle = value.to_bytes(4, "little")
    return [match.start() for match in re.finditer(re.escape(needle), blob)]


def words(blob: bytes, offset: int, count: int = 12) -> list[int]:
    out = []
    for pos in range(offset, min(len(blob) - 3, offset + count * 4), 4):
        out.append(int.from_bytes(blob[pos : pos + 4], "little"))
    return out


def local_words(blob: bytes, offset: int, before_words: int = 6, after_words: int = 10) -> str:
    start = max(0, offset - before_words * 4)
    end = min(len(blob), offset + after_words * 4)
    lines = []
    for pos in range(start, end, 4):
        chunk = blob[pos : pos + 4]
        if len(chunk) < 4:
            break
        marker = "=>" if pos == offset else "  "
        lines.append(f"{marker} 0x{pos:08x}: 0x{int.from_bytes(chunk, 'little'):08x}")
    return "\n".join(lines)


def disassemble_arm(blob: bytes, start: int, size: int = 0x120) -> str:
    aligned = start & ~3
    window_start = max(0, aligned - 0x40)
    window = blob[window_start : min(len(blob), aligned + size)]
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
    md.detail = False
    rows = []
    for ins in md.disasm(window, window_start):
        prefix = "=>" if aligned <= ins.address < aligned + 4 else "  "
        rows.append(f"{prefix} 0x{ins.address:08x}: {ins.mnemonic:<8} {ins.op_str}")
        if len(rows) >= 60:
            break
    return "\n".join(rows)


def render_stream_summary(stream: Stream) -> list[str]:
    head = stream.payload[:32].hex()
    ascii_head = "".join(chr(b) if 32 <= b < 127 else "." for b in stream.payload[:64])
    return [
        f"### Stream {stream.index} at `0x{stream.offset:x}`",
        "",
        f"- compressed size: `0x{stream.compressed_len:x}`",
        f"- inflated size: `0x{len(stream.payload):x}`",
        f"- payload head: `{head}`",
        f"- ASCII head: `{ascii_head}`",
        "",
    ]


def render_needles(stream: Stream) -> list[str]:
    lines = ["#### Relevant Strings", ""]
    any_hits = False
    for needle in NEEDLES:
        hits = find_all(stream.payload, needle)
        if not hits:
            continue
        any_hits = True
        shown = ", ".join(f"`0x{hit:x}`" for hit in hits[:12])
        suffix = "" if len(hits) <= 12 else f" plus {len(hits) - 12} more"
        lines.append(f"- `{needle.decode('ascii', errors='replace')}`: {shown}{suffix}")
        for hit in hits[:3]:
            lines.append(f"  - `0x{hit:x}` `{ascii_context(stream.payload, hit)}`")
    if not any_hits:
        lines.append("- none")
    lines.append("")
    return lines


def render_refs(stream: Stream) -> list[str]:
    lines = ["#### Direct Offset References", ""]
    interesting = []
    for needle in NEEDLES:
        for hit in find_all(stream.payload, needle)[:12]:
            refs = find_u32_refs(stream.payload, hit)
            if refs:
                interesting.append((needle, hit, refs))
    if not interesting:
        lines.extend(["- none found", ""])
        return lines

    for needle, hit, refs in interesting[:40]:
        refs_text = ", ".join(f"`0x{ref:x}`" for ref in refs[:12])
        suffix = "" if len(refs) <= 12 else f" plus {len(refs) - 12} more"
        lines.append(f"- `{needle.decode('ascii', errors='replace')}` at `0x{hit:x}` referenced at {refs_text}{suffix}")
        for ref in refs[:2]:
            lines.append("")
            lines.append("```text")
            lines.append(local_words(stream.payload, ref))
            lines.append("```")
    lines.append("")
    return lines


def render_vtable_candidates(stream: Stream) -> list[str]:
    if stream.index != 1:
        return []
    lines = ["#### Upgrade Vtable/Function Pointer Neighborhoods", ""]
    anchors = [
        b"aUpgradeFWReader",
        b"aUpgradeSHReader",
        b"aUpgradeReader.cpp",
        b"aUpgradeFWInstaller.cpp",
        b"aUpgradeMgrImpl.cpp",
    ]
    seen_targets = set()
    for anchor in anchors:
        for hit in find_all(stream.payload, anchor)[:3]:
            start = max(0, hit - 0x80)
            end = min(len(stream.payload), hit + 0x160)
            ptrs = []
            for pos in range(start, end - 3, 4):
                value = int.from_bytes(stream.payload[pos : pos + 4], "little")
                if 0x1000 <= value < len(stream.payload) and value % 4 == 0:
                    ptrs.append((pos, value))
            if not ptrs:
                continue
            lines.append(f"- anchor `{anchor.decode()}` at `0x{hit:x}`")
            for pos, value in ptrs[:16]:
                lines.append(f"  - pointer-like word `0x{value:x}` at `0x{pos:x}`")
                if value not in seen_targets:
                    seen_targets.add(value)
                    lines.append("")
                    lines.append("```armasm")
                    lines.append(disassemble_arm(stream.payload, value))
                    lines.append("```")
    if len(lines) == 2:
        lines.append("- none")
    lines.append("")
    return lines


def render_check_string_xrefs(stream: Stream) -> list[str]:
    if stream.index != 1:
        return []
    lines = ["#### ARM Disassembly Near Check-Related String References", ""]
    targets = [b"NULL != packHeader", b"versionStr", b"upgradeFile.Open", b"Checksum mismatch"]
    emitted = 0
    for needle in targets:
        for hit in find_all(stream.payload, needle):
            refs = find_u32_refs(stream.payload, hit)
            for ref in refs[:4]:
                lines.append(f"- `{needle.decode()}` at `0x{hit:x}`, referenced/literal at `0x{ref:x}`")
                lines.append("")
                lines.append("```armasm")
                lines.append(disassemble_arm(stream.payload, ref))
                lines.append("```")
                emitted += 1
                if emitted >= 12:
                    lines.append("")
                    return lines
    if emitted == 0:
        lines.append("- none")
    lines.append("")
    return lines


def build_report() -> str:
    data = SYSTEM_IMAGE.read_bytes()
    streams = decompress_streams(data)
    lines = [
        "# Upgrade Check Trace",
        "",
        "Generated by `tools/trace_upgrade_checks.py` from the active system image.",
        "",
        "## Interpretation",
        "",
        "- Stream 1 is the main ARM/VxWorks-style payload and contains the system FW/SHDb USB readers.",
        "- Stream 2 is small loader-like data and contains `Checksum mismatch` / `copyImageToDDR2`.",
        "- Stream 4 contains an explicit SHDb-side `Verifying CRC...` path.",
        "- The failed one-byte test touched the pre-zlib sync-word boot/configuration region, so it does not prove the main zlib application payload is raw-byte protected.",
        "",
    ]
    for stream in streams:
        lines.extend(render_stream_summary(stream))
        if stream.index in {1, 2, 4}:
            lines.extend(render_needles(stream))
            lines.extend(render_refs(stream))
            lines.extend(render_vtable_candidates(stream))
            lines.extend(render_check_string_xrefs(stream))
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdout", action="store_true", help="print report instead of writing analysis file")
    args = parser.parse_args()
    report = build_report()
    if args.stdout:
        print(report)
        return
    OUT.write_text(report, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
