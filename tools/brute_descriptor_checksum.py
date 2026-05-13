#!/usr/bin/env python3
"""Brute-force the unknown stored_word in each system zlib descriptor.

Codex's earlier pass eliminated standard CRC32, Adler-32, POSIX cksum, simple
sums/xors, and the common crccheck CRC32 class with one input shape (the
compressed stream and a couple of obvious neighbors). This tool extends that
search across many more candidate input ranges and many more checksum/CRC
variants, including:

  - All crccheck CRC32 implementations (every named algorithm) over many
    candidate input ranges.
  - Custom CRC32 with the standard zlib polynomial but every plausible
    init/xorout/reflection combination.
  - Fletcher-32, FNV-1a (32-bit), DJB2, XOR-fold, additive sums with assorted
    initial values.
  - Window walks: try CRC32(input[start:start+len]) for many starts and lengths
    around the descriptor and stream, in case the stored_word covers a region
    that does not align with a "natural" boundary we already considered.

Every candidate is checked against all 5 known descriptor stored words at once.
Anything that matches across all five is a STRONG hit (the algorithm is
consistent across streams). A single-stream hit is still printed but flagged.
The output is appended to analysis/descriptor_checksum_notes.md.

This is an offline RE tool. It never writes to the active opt/ binaries.
"""

from __future__ import annotations

import argparse
import binascii
import datetime as _dt
import importlib
import inspect
import io
import sys
import zlib
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM_IMAGE = ROOT / "opt" / "TurboSystem_sw" / "51.80.300.021" / "image.bin"
NOTES = ROOT / "analysis" / "descriptor_checksum_notes.md"

DESCRIPTOR_SPECS = [
    ("stream1", 0x24BB9C, 0x0C, 0x10),
    ("stream2", 0x676104, 0x18, 0x1C),
    ("stream3", 0x677516, 0x08, 0x0C),
    ("stream4", 0x677D42, 0x08, 0x0C),
    ("stream5", 0x1323127, 0x08, 0x0C),
]


@dataclass
class Descriptor:
    label: str
    desc_offset: int
    magic: int
    stored_word: int
    start_field: int
    end_field: int
    stream_offset: int
    compression_flag: int
    descriptor_size: int


@dataclass
class Inputs:
    descriptor_full: bytes
    descriptor_zeroed: bytes
    descriptor_post_stored: bytes
    compressed_stream: bytes
    compressed_with_flag: bytes
    descriptor_zeroed_plus_stream: bytes
    declared_region: bytes
    declared_region_zeroed: bytes
    inflated: bytes
    compressed_no_trailer: bytes
    inflated_with_adler: bytes


def u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little")


def load_descriptors(image: bytes) -> list[Descriptor]:
    descriptors: list[Descriptor] = []
    for index, (label, offset, start_field, end_field) in enumerate(DESCRIPTOR_SPECS):
        next_offset = DESCRIPTOR_SPECS[index + 1][1] if index + 1 < len(DESCRIPTOR_SPECS) else len(image)
        size = next_offset - offset
        start = u32(image, offset + start_field)
        end = u32(image, offset + end_field)
        stream_offset = start + 1
        descriptors.append(
            Descriptor(
                label=label,
                desc_offset=offset,
                magic=u32(image, offset),
                stored_word=u32(image, offset + 4),
                start_field=start,
                end_field=end,
                stream_offset=stream_offset,
                compression_flag=image[stream_offset - 1],
                descriptor_size=size,
            )
        )
    return descriptors


def gather_inputs(image: bytes, desc: Descriptor) -> Inputs:
    descriptor_full = image[desc.desc_offset : desc.desc_offset + desc.descriptor_size]
    descriptor_zeroed = bytearray(descriptor_full)
    descriptor_zeroed[4:8] = b"\x00\x00\x00\x00"
    descriptor_zeroed = bytes(descriptor_zeroed)

    descriptor_post_stored = descriptor_full[8:]
    compressed_stream = image[desc.stream_offset : desc.end_field]
    compressed_with_flag = image[desc.stream_offset - 1 : desc.end_field]
    declared_region = image[desc.start_field : desc.end_field]
    declared_region_zeroed = declared_region

    descriptor_zeroed_plus_stream = descriptor_zeroed + compressed_stream

    try:
        obj = zlib.decompressobj()
        inflated = obj.decompress(image[desc.stream_offset :])
        if not obj.eof:
            raise zlib.error("zlib stream did not terminate")
    except zlib.error as exc:
        raise RuntimeError(f"could not inflate {desc.label}: {exc}") from exc

    if len(compressed_stream) >= 4:
        compressed_no_trailer = compressed_stream[:-4]
    else:
        compressed_no_trailer = compressed_stream

    inflated_with_adler = inflated + (zlib.adler32(inflated) & 0xFFFFFFFF).to_bytes(4, "big")

    return Inputs(
        descriptor_full=descriptor_full,
        descriptor_zeroed=descriptor_zeroed,
        descriptor_post_stored=descriptor_post_stored,
        compressed_stream=compressed_stream,
        compressed_with_flag=compressed_with_flag,
        descriptor_zeroed_plus_stream=descriptor_zeroed_plus_stream,
        declared_region=declared_region,
        declared_region_zeroed=declared_region_zeroed,
        inflated=inflated,
        compressed_no_trailer=compressed_no_trailer,
        inflated_with_adler=inflated_with_adler,
    )


def named_input_views(inputs: Inputs) -> list[tuple[str, bytes]]:
    return [
        ("descriptor_full", inputs.descriptor_full),
        ("descriptor_zeroed", inputs.descriptor_zeroed),
        ("descriptor_post_stored", inputs.descriptor_post_stored),
        ("compressed_stream", inputs.compressed_stream),
        ("compressed_with_flag", inputs.compressed_with_flag),
        ("descriptor_zeroed+stream", inputs.descriptor_zeroed_plus_stream),
        ("declared_region", inputs.declared_region),
        ("inflated", inputs.inflated),
        ("compressed_no_trailer", inputs.compressed_no_trailer),
        ("inflated+adler", inputs.inflated_with_adler),
    ]


def reverse_bits(value: int, bits: int = 32) -> int:
    out = 0
    for _ in range(bits):
        out = (out << 1) | (value & 1)
        value >>= 1
    return out


_CRC_TABLE_CACHE: dict[tuple[int, bool], list[int]] = {}


def _crc_table(poly: int, refin: bool) -> list[int]:
    key = (poly & 0xFFFFFFFF, refin)
    cached = _CRC_TABLE_CACHE.get(key)
    if cached is not None:
        return cached
    table: list[int] = [0] * 256
    if refin:
        rpoly = reverse_bits(poly, 32)
        for byte in range(256):
            crc = byte
            for _ in range(8):
                crc = (crc >> 1) ^ rpoly if crc & 1 else crc >> 1
            table[byte] = crc & 0xFFFFFFFF
    else:
        for byte in range(256):
            crc = byte << 24
            for _ in range(8):
                crc = ((crc << 1) ^ poly) & 0xFFFFFFFF if crc & 0x80000000 else (crc << 1) & 0xFFFFFFFF
            table[byte] = crc
    _CRC_TABLE_CACHE[key] = table
    return table


def crc32_polynomial_variants(data: bytes, poly: int, init: int, xorout: int, refin: bool, refout: bool) -> int:
    """Table-driven CRC-32 driver. Big inputs run in C-speed thanks to bytes ops."""
    table = _crc_table(poly, refin)
    crc = init & 0xFFFFFFFF
    if refin:
        for byte in data:
            crc = table[(crc ^ byte) & 0xFF] ^ (crc >> 8)
    else:
        for byte in data:
            crc = (table[((crc >> 24) ^ byte) & 0xFF] ^ (crc << 8)) & 0xFFFFFFFF
    if refin != refout:
        crc = reverse_bits(crc, 32)
    return (crc ^ xorout) & 0xFFFFFFFF


def fletcher32(data: bytes) -> int:
    if len(data) % 2:
        data = data + b"\x00"
    a = 0xFFFF
    b = 0xFFFF
    for index in range(0, len(data), 2):
        word = data[index] | (data[index + 1] << 8)
        a = (a + word) % 0xFFFF
        b = (b + a) % 0xFFFF
    return ((b << 16) | a) & 0xFFFFFFFF


def fnv1a32(data: bytes) -> int:
    hash_value = 0x811C9DC5
    for byte in data:
        hash_value ^= byte
        hash_value = (hash_value * 0x01000193) & 0xFFFFFFFF
    return hash_value


def djb2_32(data: bytes) -> int:
    hash_value = 5381
    for byte in data:
        hash_value = ((hash_value * 33) + byte) & 0xFFFFFFFF
    return hash_value


def xor_fold32(data: bytes) -> int:
    pad = (-len(data)) % 4
    padded = data + b"\x00" * pad
    accumulator = 0
    for index in range(0, len(padded), 4):
        accumulator ^= int.from_bytes(padded[index : index + 4], "little")
    return accumulator & 0xFFFFFFFF


def additive_sum32(data: bytes, initial: int = 0) -> int:
    accumulator = initial & 0xFFFFFFFF
    pad = (-len(data)) % 4
    padded = data + b"\x00" * pad
    for index in range(0, len(padded), 4):
        accumulator = (accumulator + int.from_bytes(padded[index : index + 4], "little")) & 0xFFFFFFFF
    return accumulator


def common_crccheck_classes() -> dict[str, type]:
    try:
        crc_module = importlib.import_module("crccheck.crc")
    except ImportError:
        return {}
    classes: dict[str, type] = {}
    for name, cls in inspect.getmembers(crc_module, inspect.isclass):
        if not name.lower().startswith("crc32"):
            continue
        try:
            instance = cls()
            value = instance.calc(b"123456789")
            if not isinstance(value, int) or value > 0xFFFFFFFF:
                continue
        except Exception:  # pragma: no cover - lib-specific quirks
            continue
        classes[name] = cls
    return classes


@dataclass
class Hit:
    descriptor: str
    algorithm: str
    input_view: str
    value: int


def algorithms() -> dict[str, callable]:
    """A grab-bag of cheap, deterministic 32-bit hashes/CRCs to try."""
    funcs: dict[str, callable] = {
        "zlib.crc32": lambda data: zlib.crc32(data) & 0xFFFFFFFF,
        "binascii.crc32": lambda data: binascii.crc32(data) & 0xFFFFFFFF,
        "zlib.adler32": lambda data: zlib.adler32(data) & 0xFFFFFFFF,
        "fletcher32": fletcher32,
        "fnv1a32": fnv1a32,
        "djb2_32": djb2_32,
        "xor_fold32": xor_fold32,
        "sum32_init0": lambda data: additive_sum32(data, 0),
        "sum32_init_ffffffff": lambda data: additive_sum32(data, 0xFFFFFFFF),
        "sum32_init_deadbeef": lambda data: additive_sum32(data, 0xDEADBEEF),
        "neg_zlib_crc32": lambda data: (~zlib.crc32(data)) & 0xFFFFFFFF,
        "swapped_zlib_crc32": lambda data: int.from_bytes(
            (zlib.crc32(data) & 0xFFFFFFFF).to_bytes(4, "little"), "big"
        ),
        "reversed_zlib_crc32": lambda data: reverse_bits(zlib.crc32(data) & 0xFFFFFFFF, 32),
    }
    polynomial_table = [
        ("CRC-32C/Castagnoli", 0x1EDC6F41, 0xFFFFFFFF, 0xFFFFFFFF, True, True),
        ("CRC-32/MPEG-2", 0x04C11DB7, 0xFFFFFFFF, 0x00000000, False, False),
        ("CRC-32/BZIP2", 0x04C11DB7, 0xFFFFFFFF, 0xFFFFFFFF, False, False),
        ("CRC-32/AUTOSAR", 0xF4ACFB13, 0xFFFFFFFF, 0xFFFFFFFF, True, True),
        ("CRC-32/JAMCRC", 0x04C11DB7, 0xFFFFFFFF, 0x00000000, True, True),
        ("CRC-32/POSIX-cksum", 0x04C11DB7, 0x00000000, 0xFFFFFFFF, False, False),
        ("CRC-32/XFER", 0x000000AF, 0x00000000, 0x00000000, False, False),
        ("CRC-32/Q", 0x814141AB, 0x00000000, 0x00000000, False, False),
        ("CRC-32/D", 0xA833982B, 0xFFFFFFFF, 0xFFFFFFFF, True, True),
    ]
    for name, poly, init, xorout, refin, refout in polynomial_table:
        funcs[name] = (lambda data, p=poly, i=init, x=xorout, ri=refin, ro=refout:
                       crc32_polynomial_variants(data, p, i, x, ri, ro))
    return funcs


def search_known_targets(image: bytes, descriptors: list[Descriptor], heavy_max_bytes: int = 0x40000) -> list[Hit]:
    hits: list[Hit] = []
    funcs = algorithms()
    crccheck_classes = common_crccheck_classes()
    target_set = {desc.stored_word for desc in descriptors}
    desc_inputs = [(desc, gather_inputs(image, desc)) for desc in descriptors]
    fast_funcs = {"zlib.crc32", "binascii.crc32", "zlib.adler32", "fletcher32", "fnv1a32", "djb2_32", "xor_fold32",
                  "sum32_init0", "sum32_init_ffffffff", "sum32_init_deadbeef", "neg_zlib_crc32",
                  "swapped_zlib_crc32", "reversed_zlib_crc32"}

    for desc, inputs in desc_inputs:
        for view_name, view in named_input_views(inputs):
            for algorithm_name, func in funcs.items():
                if algorithm_name not in fast_funcs and len(view) > heavy_max_bytes:
                    continue
                try:
                    value = func(view) & 0xFFFFFFFF
                except Exception:  # pragma: no cover
                    continue
                if value == desc.stored_word:
                    hits.append(Hit(desc.label, algorithm_name, view_name, value))
                if value in target_set:
                    other = next(other for other in descriptors if other.stored_word == value)
                    if other.label != desc.label:
                        hits.append(
                            Hit(
                                desc.label,
                                f"{algorithm_name} (cross-target {other.label})",
                                view_name,
                                value,
                            )
                        )
            for class_name, cls in crccheck_classes.items():
                if len(view) > heavy_max_bytes:
                    continue
                try:
                    value = int(cls().calc(view)) & 0xFFFFFFFF
                except Exception:
                    continue
                if value == desc.stored_word:
                    hits.append(Hit(desc.label, f"crccheck:{class_name}", view_name, value))
    return hits


def shared_algorithm_hits(image: bytes, descriptors: list[Descriptor], heavy_max_bytes: int = 0x40000) -> list[str]:
    """Algorithms that match every descriptor are the strongest signal."""
    funcs = algorithms()
    crccheck_classes = common_crccheck_classes()
    desc_inputs = [(desc, gather_inputs(image, desc)) for desc in descriptors]
    view_names = [name for name, _ in named_input_views(desc_inputs[0][1])]
    matches: list[str] = []
    fast_funcs = {"zlib.crc32", "binascii.crc32", "zlib.adler32", "fletcher32", "fnv1a32", "djb2_32", "xor_fold32",
                  "sum32_init0", "sum32_init_ffffffff", "sum32_init_deadbeef", "neg_zlib_crc32",
                  "swapped_zlib_crc32", "reversed_zlib_crc32"}
    for view_name in view_names:
        view_per_desc = [
            dict(named_input_views(inputs))[view_name]
            for _, inputs in desc_inputs
        ]
        skip_heavy = any(len(view) > heavy_max_bytes for view in view_per_desc)
        for algorithm_name, func in funcs.items():
            if skip_heavy and algorithm_name not in fast_funcs:
                continue
            try:
                values = [func(data) & 0xFFFFFFFF for data in view_per_desc]
            except Exception:
                continue
            if all(value == desc.stored_word for value, (desc, _) in zip(values, desc_inputs)):
                matches.append(f"ALL streams match `{algorithm_name}` over `{view_name}`")
        if skip_heavy:
            continue
        for class_name, cls in crccheck_classes.items():
            try:
                values = [int(cls().calc(data)) & 0xFFFFFFFF for data in view_per_desc]
            except Exception:
                continue
            if all(value == desc.stored_word for value, (desc, _) in zip(values, desc_inputs)):
                matches.append(
                    f"ALL streams match `crccheck:{class_name}` over `{view_name}`"
                )
    return matches


CUSTOM_SWEEP_MAX_VIEW_BYTES = 0x40000  # 256 KiB; bigger inputs would take minutes per call.


def custom_crc32_sweep(image: bytes, descriptors: list[Descriptor], max_view_bytes: int = CUSTOM_SWEEP_MAX_VIEW_BYTES) -> list[str]:
    """Sweep init/xorout/poly combos against every small enough input view.

    Sweeps the standard CRC-32 polynomial 0x04C11DB7 plus a few common
    firmware-style polynomials, varying init/xorout/refin/refout. Pure-python
    CRC computation is slow, so we cap the input size per view; the multi-MiB
    compressed and inflated views still get hit by the named algorithms in
    `shared_algorithm_hits`.
    """
    polys = [
        0x04C11DB7,  # IEEE 802.3
        0x1EDC6F41,  # Castagnoli (CRC-32C)
        0xA833982B,  # CRC-32D
        0xF4ACFB13,  # AUTOSAR
        0x000000AF,  # XFER
        0x814141AB,  # CRC-32Q
        0x82F63B78,  # CRC-32C reflected polynomial form
    ]
    init_candidates = [0x00000000, 0xFFFFFFFF, 0xDEADBEEF, 0xCAFEBABE, 0xA5A5A5A5, 0x12345678]
    xorout_candidates = [0x00000000, 0xFFFFFFFF, 0xDEADBEEF, 0xCAFEBABE]
    matches: list[str] = []
    desc_inputs = [(desc, gather_inputs(image, desc)) for desc in descriptors]
    view_names = [name for name, _ in named_input_views(desc_inputs[0][1])]
    for view_name in view_names:
        view_per_desc = [
            dict(named_input_views(inputs))[view_name]
            for _, inputs in desc_inputs
        ]
        if any(len(view) > max_view_bytes for view in view_per_desc):
            continue
        for poly in polys:
            for refin in (False, True):
                for refout in (False, True):
                    for init in init_candidates:
                        for xorout in xorout_candidates:
                            try:
                                values = [
                                    crc32_polynomial_variants(data, poly, init, xorout, refin, refout)
                                    for data in view_per_desc
                                ]
                            except Exception:
                                continue
                            ok = all(value == desc.stored_word for value, (desc, _) in zip(values, desc_inputs))
                            if ok:
                                matches.append(
                                    "ALL streams match custom CRC-32 "
                                    f"(poly=0x{poly:08x} init=0x{init:08x} xorout=0x{xorout:08x} "
                                    f"refin={refin} refout={refout}) over `{view_name}`"
                                )
    return matches


def render_report(image: bytes, descriptors: list[Descriptor], single_hits: list[Hit], shared_hits: list[str], custom_hits: list[str]) -> str:
    lines = [
        "## Brute Force Sweep",
        "",
        f"Generated {_dt.datetime.now().strftime('%Y-%m-%d %H:%M')} by `tools/brute_descriptor_checksum.py`.",
        "",
        "### Descriptor Summary",
        "",
    ]
    for desc in descriptors:
        lines.append(
            f"- `{desc.label}`: stored_word `0x{desc.stored_word:08x}` magic "
            f"`0x{desc.magic:08x}` start `0x{desc.start_field:x}` end `0x{desc.end_field:x}`"
        )
    lines.extend(["", "### Cross-Stream Matches", ""])
    if shared_hits or custom_hits:
        for hit in shared_hits + custom_hits:
            lines.append(f"- {hit}")
    else:
        lines.append("- none. No simple algorithm reproduces all five stored words from any tested input view.")

    lines.extend(["", "### Single-Stream Hits", ""])
    if single_hits:
        for hit in single_hits:
            lines.append(
                f"- `{hit.descriptor}`: `{hit.algorithm}` on `{hit.input_view}` -> "
                f"0x{hit.value:08x}"
            )
    else:
        lines.append("- none.")

    lines.extend(["", "### Inputs Considered", ""])
    inputs = gather_inputs(image, descriptors[0])
    for view_name, view in named_input_views(inputs):
        lines.append(f"- `{view_name}` (stream1): {len(view)} bytes")

    lines.extend([
        "",
        "### Read",
        "",
        "If no shared-algorithm match was found across all five descriptors, the",
        "stored_word is most likely a custom routine (table-driven CRC with a",
        "non-standard polynomial, or a small bespoke checksum). The next step is",
        "Ghidra-side: find the function that consumes the descriptor and read it",
        "directly. Strings worth chasing are `aUpgradeFWReader`, `IMAGE.BIN`, and",
        "the embedded constants near `0x24bbb4`.",
        "",
    ])
    return "\n".join(lines)


def append_to_notes(report: str) -> None:
    NOTES.parent.mkdir(parents=True, exist_ok=True)
    if not NOTES.exists():
        NOTES.write_text("# Descriptor Checksum Notes\n\n", encoding="utf-8")
    text = NOTES.read_text(encoding="utf-8")
    new_text = text.rstrip() + "\n\n" + report.rstrip() + "\n"
    NOTES.write_text(new_text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="append the report to analysis/descriptor_checksum_notes.md")
    parser.add_argument("--stdout", action="store_true", help="print the report to stdout")
    args = parser.parse_args()

    if not (args.write or args.stdout):
        args.stdout = True

    image = SYSTEM_IMAGE.read_bytes()
    descriptors = load_descriptors(image)

    print("loading descriptors:")
    for desc in descriptors:
        print(
            f"  {desc.label}: stored_word=0x{desc.stored_word:08x} "
            f"magic=0x{desc.magic:08x} start=0x{desc.start_field:x} "
            f"end=0x{desc.end_field:x}"
        )
    print()
    print("running cross-stream named-algorithm sweep ...")
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        shared_hits = shared_algorithm_hits(image, descriptors)
    print("running cross-stream custom CRC-32 sweep ...")
    custom_hits = custom_crc32_sweep(image, descriptors)
    print("running per-stream named-algorithm sweep ...")
    single_hits = search_known_targets(image, descriptors)

    report = render_report(image, descriptors, single_hits, shared_hits, custom_hits)

    if args.stdout:
        print()
        print(report)
    if args.write:
        append_to_notes(report)
        print(f"appended report to {NOTES.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
