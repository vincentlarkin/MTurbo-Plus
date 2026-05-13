#!/usr/bin/env python3
"""Verify that all marker patches are present in the current image.bin.

Prints PASS/FAIL per marker and exits non-zero if anything is missing.
Does not modify any file. Safe to run any time.
"""

from __future__ import annotations

import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIMER_ZLIB = 0x24BBB5

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

sys.path.insert(0, str(ROOT))
from tools.patch_mturbo_strings import (  # noqa: E402
    BOOT_PATCHED,
    SYSTEM_VERSION_ORIGINAL,
    SYSTEM_VERSION_PATCHED,
    SHDB_VERSION_ORIGINAL,
    SHDB_VERSION_PATCHED,
    TIMER_REPLACEMENTS,
    SYSINFO_REPLACEMENTS,
)
from tools.patch_mturbo_splash import (  # noqa: E402
    SPLASH_POINTER_TABLE_OFFSET,
    SPLASH_FRAME_COUNT,
    MTURBO_SPLASH_INDEX,
    decode_rle_with_consumed,
    looks_patched,
)


def resolve_single(glob_pattern: str) -> Path:
    matches = sorted(ROOT.glob(glob_pattern))
    if len(matches) != 1:
        print(f"error: expected one file via {glob_pattern}, got {len(matches)}", file=sys.stderr)
        sys.exit(2)
    return matches[0]


def main() -> None:
    sys_image = resolve_single("opt/TurboSystem_sw/*/image.bin")
    shdb_image = resolve_single("opt/TurboSHDb/*/image.bin")

    sys_data = sys_image.read_bytes()
    shdb_data = shdb_image.read_bytes()

    print(f"system image: {sys_image.relative_to(ROOT)}  size=0x{len(sys_data):x}")
    print(f"shdb image:   {shdb_image.relative_to(ROOT)}  size=0x{len(shdb_data):x}")
    print()

    fails = 0

    def check(label: str, ok: bool, detail: str = "") -> None:
        nonlocal fails
        verdict = "PASS" if ok else "FAIL"
        if not ok:
            fails += 1
        print(f"  [{verdict}] {label}{('  ' + detail) if detail else ''}")

    print("outer image markers:")
    orig_at = sys_data.find(SYSTEM_VERSION_ORIGINAL)
    bump_at = sys_data.find(SYSTEM_VERSION_PATCHED)
    if orig_at >= 0 and bump_at < 0:
        check(f"system version present (stock {SYSTEM_VERSION_ORIGINAL.decode()})", True,
              f"orig@{orig_at:#x}")
    elif bump_at >= 0 and orig_at < 0:
        check(f"system version present (bumped {SYSTEM_VERSION_PATCHED.decode()})", True,
              f"bumped@{bump_at:#x}")
    else:
        check("system version present (exactly one of stock/bumped)", False,
              f"orig@{orig_at:#x} bumped@{bump_at:#x}")
    check(
        "boot copyright is patched",
        sys_data.find(BOOT_PATCHED) >= 0,
        f"@{sys_data.find(BOOT_PATCHED):#x}" if sys_data.find(BOOT_PATCHED) >= 0 else "missing",
    )
    check(
        "Wind River boot copyright is gone",
        sys_data.find(b"Copyright 1984-1996 Wind River") < 0,
    )

    print("\nsplash bitmap:")
    try:
        ptrs = [
            int.from_bytes(
                sys_data[SPLASH_POINTER_TABLE_OFFSET + i * 4 : SPLASH_POINTER_TABLE_OFFSET + i * 4 + 4],
                "little",
            )
            for i in range(SPLASH_FRAME_COUNT)
        ]
        start = ptrs[MTURBO_SPLASH_INDEX]
        end = ptrs[MTURBO_SPLASH_INDEX + 1]
        chunk = bytes(sys_data[start:end])
        indices, _ = decode_rle_with_consumed(chunk)
        is_patched = looks_patched(indices)
        check(
            "boot splash is the MTurbo-Plus blue-wireframe variant",
            is_patched,
            f"chunk 0x{start:x}-0x{end:x} ({len(chunk)} bytes)",
        )
    except Exception as exc:
        check("boot splash decodes and is patched", False, f"error: {exc}")

    print("\ntimer zlib stream:")
    try:
        obj = zlib.decompressobj()
        payload = obj.decompress(sys_data[TIMER_ZLIB:])
        consumed = len(sys_data) - TIMER_ZLIB - len(obj.unused_data)
        check("zlib stream decompresses cleanly", obj.eof, f"consumed {consumed} bytes, inflated {len(payload)} bytes")
    except Exception as exc:
        check("zlib stream decompresses cleanly", False, f"error: {exc}")
        sys.exit(1)

    print("\ntimer-screen markers:")
    for old, new in TIMER_REPLACEMENTS:
        check(
            f'{old.decode()[:40]} -> {new.decode()[:40]}',
            payload.find(new) >= 0 and payload.find(old) < 0,
            f"@{payload.find(new):#x}" if payload.find(new) >= 0 else "missing",
        )

    print("\nsystem-information markers:")
    for old, new in SYSINFO_REPLACEMENTS:
        # `old` may have legitimately also lived as a substring of a longer
        # label (e.g. "ARM SW Ver" inside "C2 ARM SW Ver"); we only require
        # that the NEW marker is present somewhere. We also report the
        # remaining count of OLD so anyone reading the output can tell at a
        # glance whether more copies still need patching.
        old_count = payload.count(old)
        new_idx = payload.find(new)
        ok = new_idx >= 0
        check(
            f'{old.decode()} -> {new.decode()}',
            ok,
            f"@{new_idx:#x} (old_remaining={old_count})" if ok else "missing",
        )

    print("\nshdb image:")
    shdb_orig_at = shdb_data.find(SHDB_VERSION_ORIGINAL)
    shdb_bump_at = shdb_data.find(SHDB_VERSION_PATCHED)
    if shdb_orig_at >= 0 and shdb_bump_at < 0:
        check(f"SHDb/transducer version present (stock {SHDB_VERSION_ORIGINAL.decode()})", True,
              f"orig@{shdb_orig_at:#x}")
    elif shdb_bump_at >= 0 and shdb_orig_at < 0:
        check(f"SHDb/transducer version present (bumped {SHDB_VERSION_PATCHED.decode()})", True,
              f"bumped@{shdb_bump_at:#x}")
    else:
        check("SHDb/transducer version present (exactly one of stock/bumped)", False,
              f"orig@{shdb_orig_at:#x} bumped@{shdb_bump_at:#x}")

    print()
    if fails:
        print(f"verification FAILED: {fails} marker(s) missing")
        sys.exit(1)
    print("verification PASSED: all markers present")


if __name__ == "__main__":
    main()
