#!/usr/bin/env python3
"""Patch visible MTurbo boot/timer marker strings in the firmware package."""

from __future__ import annotations

import argparse
import shutil
import sys
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_IMAGE_GLOB = "opt/TurboSystem_sw/*/image.bin"
SHDB_IMAGE_GLOB = "opt/TurboSHDb/*/image.bin"
KNOWN_TIMER_ZLIB_OFFSET = 0x24BBB5

SYSTEM_VERSION_ORIGINAL = b"51.80.300.015"
SYSTEM_VERSION_PATCHED = b"51.80.999.999"
SHDB_VERSION_ORIGINAL = b"50.80.111.012"
SHDB_VERSION_PATCHED = b"50.80.999.999"

BOOT_ORIGINAL = b"Copyright 1984-1996 Wind River Systems, Inc."
BOOT_PATCHED = b"Copyright 2019 If you see this, it worked   "

TIMER_REPLACEMENTS = [
    (b"left before license key needed", b"left before MT build key test!"),
    (b"49 hours, 59 minutes", b"MT BUILD TIMER 2019!"),
    (b"To obtain a license key:", b"MT firmware marker page:"),
    (b"1. Contact SonoSite at:", b"1. MT marker visible!!!"),
    (b"www.sonosite.com", b"mt-build-2019!!!"),
    (b"ffss-service@fujifilm.com", b"MT screen marker 2019 OK!"),
    (b"2. Supply following:", b"2. MT build info!!!!"),
    (b"a. your name", b"a. MT BUILD!"),
    (b"b. System serial # ", b"b. MT serial mark!!"),
    (b"c. ARM version:", b"c. ARM MARKER!!"),
    (b"d. PCBA serial #:", b"d. PCBA MARKER!!!"),
    (b"3. Enter license key:", b"3. MT KEY MARKER!!!!!"),
    (b"e. Previous licence update", b"e. MT marker update 2019!!"),
    (b"[System]", b"[MT2019]"),
    (b"1.877.675.8118 (USA)", b"MT-BOOT-MARKER-2019!"),
    (b"1.425.951.1330 (Worldwide)", b"MT FIRMWARE MARKER WORLD!!"),
]

# System Information screen labels. These live inside the same inflated zlib
# payload as the timer strings, in the contiguous label table around
# +0x8ca050..0x8ca8a0 in the inflated payload. Each one is a printf label
# rendered next to a runtime value (e.g. "%-*s True", "%-*s %d %s"), so
# replacing the label text only changes what shows on the System Information
# screen (Setup -> System Information). Nothing here is matched by name in
# code or by the license/clinical layer.
#
# Explicitly NOT replaced here (left stock on purpose):
#   - "License Key", "Patient *", exam names ("Cardiac", "OB", "Vascular"...),
#     "DICOM ...", "Service", "Software Version" (the DICOM-tag instance).
SYSINFO_REPLACEMENTS = [
    (b"Get System Configuration", b"Get MT-Plus Cfg Marker !"),
    (b"ARM SW Ver",                b"MTARM 2019"),
    (b"Mini Boot SW Ver",          b"MT MINI-BOOT2019"),
    (b"Boot Loader SW Ver",        b"MT BOOT-LDR 2019!!"),
    (b"VxWorks SW Ver",            b"MT VxMARK 2019"),
    (b"DSP SW Ver (All Modes)",    b"MT DSP MARKER 2019 !!!"),
    (b"Fritz FPGA Ver",            b"MT FRITZ 2019!"),
    (b"Main FPGA Ver",             b"MT FPGA MARK!"),
    (b"Touch Pad SW Ver",          b"MT TOUCHPAD 2019"),
    (b"Touch Pad S/N",             b"MT-TOUCH 2019"),
    (b"Burn-In Mode",              b"MT-BUILD2019"),
    (b"Sleep Delay",               b"MT MARK!!!!"),
    (b"Power-Off Delay",           b"MT 2019 BUILD!!"),
    (b"External Network Ports",    b"MT 2019 PORTS MARKER!!"),
    (b"Front-End Calibrated",      b"MT-PLUS 2019 BUILD!!"),
    (b"TGC DACs Calibrated",       b"MT BUILD MARK 2019!"),
    (b"Wave2B Supported",          b"MT2019 BUILDMARK"),
    (b"Console Shell",             b"MT2019 MARK!!"),
    (b"Panic Screen",              b"MT MARK 2019"),
]


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_lengths() -> None:
    for old, new in (
        (SYSTEM_VERSION_ORIGINAL, SYSTEM_VERSION_PATCHED),
        (SHDB_VERSION_ORIGINAL, SHDB_VERSION_PATCHED),
    ):
        if len(old) != len(new):
            fail(f"version replacement length mismatch: {old!r} -> {new!r}")
    if len(BOOT_ORIGINAL) != len(BOOT_PATCHED):
        fail("boot marker replacement length changed")
    for old, new in TIMER_REPLACEMENTS:
        if len(old) != len(new):
            fail(f"timer replacement length mismatch: {old!r} -> {new!r}")
    for old, new in SYSINFO_REPLACEMENTS:
        if len(old) != len(new):
            fail(f"sysinfo replacement length mismatch ({len(old)} vs {len(new)}): {old!r} -> {new!r}")


def decompress_stream(data: bytes, offset: int) -> tuple[bytes, int]:
    obj = zlib.decompressobj()
    try:
        payload = obj.decompress(data[offset:])
    except zlib.error as exc:
        raise ValueError(str(exc)) from exc
    if not obj.eof:
        raise ValueError("zlib stream did not terminate")
    consumed = len(data) - offset - len(obj.unused_data)
    return payload, consumed


def find_timer_stream(data: bytes) -> tuple[int, int, bytes]:
    anchors = [b"3. Enter license key:", b"3. MT KEY MARKER!!!!!"]
    try:
        payload, consumed = decompress_stream(data, KNOWN_TIMER_ZLIB_OFFSET)
        if any(anchor in payload for anchor in anchors):
            return KNOWN_TIMER_ZLIB_OFFSET, consumed, payload
    except ValueError:
        pass

    for marker in (b"\x78\x9c", b"\x78\xda", b"\x78\x01"):
        start = 0
        while True:
            offset = data.find(marker, start)
            if offset < 0:
                break
            start = offset + 1
            try:
                payload, consumed = decompress_stream(data, offset)
            except ValueError:
                continue
            if any(anchor in payload for anchor in anchors):
                return offset, consumed, payload
    fail("could not find timer-screen zlib payload")


def patch_bytes_once(blob: bytearray, old: bytes, new: bytes, label: str) -> bool:
    idx = blob.find(old)
    if idx >= 0:
        blob[idx : idx + len(old)] = new
        print(f"patched {label} at 0x{idx:x}: {old.decode()} -> {new.decode()}")
        return True
    if blob.find(new) >= 0:
        print(f"already patched {label}: {new.decode()}")
        return False
    fail(f"missing expected {label}: {old!r}")


def patch_bytes_all(blob: bytearray, old: bytes, new: bytes, label: str) -> bool:
    """Replace every occurrence of `old` with `new`.

    Length-preserving. Idempotent: if no `old` remains but `new` is present,
    reports `already patched`. Returns True if any byte was changed.
    """
    assert len(old) == len(new)
    changed = False
    hits: list[int] = []
    start = 0
    while True:
        idx = blob.find(old, start)
        if idx < 0:
            break
        blob[idx : idx + len(old)] = new
        hits.append(idx)
        start = idx + len(old)
        changed = True
    if hits:
        joined = ",".join(f"0x{h:x}" for h in hits)
        print(f"patched {label} at [{joined}]: {old.decode()} -> {new.decode()}")
        return True
    if blob.find(new) >= 0:
        print(f"already patched {label}: {new.decode()}")
        return False
    fail(f"missing expected {label}: {old!r}")


def report_current_marker(blob: bytes, original: bytes, patched: bytes, label: str) -> None:
    if blob.find(original) >= 0:
        print(f"current {label}: {original.decode()}")
        return
    if blob.find(patched) >= 0:
        print(f"current {label}: {patched.decode()}")
        return
    fail(f"missing expected {label}: {original!r} or {patched!r}")


def resolve_single(glob_pattern: str, label: str) -> Path:
    matches = sorted(ROOT.glob(glob_pattern))
    if len(matches) != 1:
        fail(f"expected one {label}, found {len(matches)} using {glob_pattern}")
    return matches[0]


def patch_file_once(path: Path, old: bytes, new: bytes, label: str, dry_run: bool) -> bool:
    data = bytearray(path.read_bytes())
    changed = patch_bytes_once(data, old, new, label)
    if changed and not dry_run:
        path.write_bytes(data)
        print(f"patched image written: {path}")
    return changed


def report_file_marker(path: Path, original: bytes, patched: bytes, label: str) -> None:
    report_current_marker(path.read_bytes(), original, patched, label)


def best_recompress(payload: bytes) -> bytes:
    """Return the smallest zlib(deflate) re-encoding of payload we can find."""
    strategies = [
        zlib.Z_DEFAULT_STRATEGY,
        zlib.Z_FILTERED,
        zlib.Z_RLE,
        zlib.Z_HUFFMAN_ONLY,
    ]
    best: bytes | None = None
    for level in range(9, 0, -1):
        for strategy in strategies:
            compressor = zlib.compressobj(
                level,
                zlib.DEFLATED,
                zlib.MAX_WBITS,
                zlib.DEF_MEM_LEVEL,
                strategy,
            )
            candidate = compressor.compress(payload) + compressor.flush()
            if best is None or len(candidate) < len(best):
                best = candidate
    assert best is not None
    return best


def count_trailing_zeros(data: bytes, start: int, max_scan: int = 0x4000) -> int:
    """Count how many consecutive zero bytes start at offset `start`."""
    end = min(len(data), start + max_scan)
    n = 0
    while start + n < end and data[start + n] == 0:
        n += 1
    return n


# Allow the recompressed zlib stream to grow into the trailing-zero slack
# region that the original firmware build left after this chunk. Hard-capped
# below the measured slack so we never run into the next firmware block.
SLACK_HARD_CAP_BYTES = 0x400  # 1 KiB beyond original stream_len


def recompress_to_fit(payload: bytes, limit: int, data: bytes, stream_offset: int) -> bytes:
    candidate = best_recompress(payload)
    if len(candidate) <= limit:
        return candidate

    slack = count_trailing_zeros(data, stream_offset + limit)
    allowed_growth = min(slack, SLACK_HARD_CAP_BYTES)
    extended_limit = limit + allowed_growth
    if len(candidate) <= extended_limit:
        try:
            obj = zlib.decompressobj()
            roundtrip = obj.decompress(candidate)
            if not obj.eof or roundtrip != payload:
                raise ValueError("roundtrip mismatch")
        except Exception as exc:
            fail(f"recompressed stream failed roundtrip verification: {exc}")
        print(
            f"recompressed timer payload {len(candidate)} bytes (orig {limit}), "
            f"growing into {len(candidate) - limit} of {slack} zero slack bytes "
            f"(cap {SLACK_HARD_CAP_BYTES})"
        )
        return candidate
    fail(
        "recompressed timer payload is too large: "
        f"best={len(candidate)} stream_limit={limit} slack={slack} "
        f"cap={SLACK_HARD_CAP_BYTES} extended_limit={extended_limit}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path)
    parser.add_argument("--shdb-image", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backup", action="store_true")
    version_group = parser.add_mutually_exclusive_group()
    version_group.add_argument("--bump-versions", action="store_true")
    version_group.add_argument("--restore-versions", action="store_true")
    args = parser.parse_args()

    check_lengths()
    image_path = (args.image or resolve_single(SYSTEM_IMAGE_GLOB, "system image")).resolve()
    shdb_image_path = (args.shdb_image or resolve_single(SHDB_IMAGE_GLOB, "SHDb image")).resolve()
    data = bytearray(image_path.read_bytes())

    changed = False
    if args.bump_versions:
        changed |= patch_bytes_once(data, SYSTEM_VERSION_ORIGINAL, SYSTEM_VERSION_PATCHED, "system version")
    elif args.restore_versions:
        changed |= patch_bytes_once(data, SYSTEM_VERSION_PATCHED, SYSTEM_VERSION_ORIGINAL, "system version")
    else:
        report_current_marker(data, SYSTEM_VERSION_ORIGINAL, SYSTEM_VERSION_PATCHED, "system version")
    changed |= patch_bytes_once(data, BOOT_ORIGINAL, BOOT_PATCHED, "boot copyright")

    stream_offset, stream_len, payload = find_timer_stream(data)
    timer_blob = bytearray(payload)
    timer_changed = False
    for old, new in TIMER_REPLACEMENTS:
        timer_changed |= patch_bytes_once(timer_blob, old, new, "timer string")
    for old, new in SYSINFO_REPLACEMENTS:
        timer_changed |= patch_bytes_all(timer_blob, old, new, "sysinfo string")

    if timer_changed:
        new_stream = recompress_to_fit(bytes(timer_blob), stream_len, bytes(data), stream_offset)
        data[stream_offset : stream_offset + len(new_stream)] = new_stream
        if len(new_stream) < stream_len:
            data[stream_offset + len(new_stream) : stream_offset + stream_len] = (
                b"\x00" * (stream_len - len(new_stream))
            )
        print(
            "recompressed timer payload "
            f"at 0x{stream_offset:x}: {stream_len} -> {len(new_stream)} bytes"
        )
        changed = True

    if not changed:
        print("no system image changes needed")
    else:
        if args.dry_run:
            print("dry run only; system image not written")
        else:
            if args.backup:
                backup_path = image_path.with_suffix(image_path.suffix + ".bak")
                if not backup_path.exists():
                    shutil.copy2(image_path, backup_path)
                    print(f"backup written: {backup_path}")
            image_path.write_bytes(data)
            print(f"patched image written: {image_path}")

    if args.bump_versions:
        patch_file_once(
            shdb_image_path,
            SHDB_VERSION_ORIGINAL,
            SHDB_VERSION_PATCHED,
            "SHDb/transducer version",
            dry_run=args.dry_run,
        )
    elif args.restore_versions:
        patch_file_once(
            shdb_image_path,
            SHDB_VERSION_PATCHED,
            SHDB_VERSION_ORIGINAL,
            "SHDb/transducer version",
            dry_run=args.dry_run,
        )
    else:
        report_file_marker(
            shdb_image_path,
            SHDB_VERSION_ORIGINAL,
            SHDB_VERSION_PATCHED,
            "SHDb/transducer version",
        )


if __name__ == "__main__":
    main()
