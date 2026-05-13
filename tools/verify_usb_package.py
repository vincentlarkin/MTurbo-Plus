#!/usr/bin/env python3
"""Verify a copied USB package against the local stock-parity opt tree."""

from __future__ import annotations

import argparse
import hashlib
import sys
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_OPT = ROOT / "opt"
EXPECTED = [
    Path("TurboSystem_sw/51.80.300.021/image.bin"),
    Path("TurboSystem_sw/51.80.300.021/eFilmLite/tempFL.bin"),
    Path("TurboSHDb/50.80.111.018/image.bin"),
]


def crc32(data: bytes) -> str:
    return f"{zlib.crc32(data) & 0xffffffff:08x}"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_file(local: Path, remote: Path, rel: Path) -> int:
    if not remote.is_file():
        print(f"[FAIL] missing USB file - opt\\{rel}")
        return 1
    local_data = local.read_bytes()
    remote_data = remote.read_bytes()
    if local_data == remote_data:
        print(f"[PASS] opt\\{rel} matches")
        return 0
    print(f"[FAIL] opt\\{rel} differs")
    print(f"  local size={len(local_data)} crc32={crc32(local_data)} sha256={sha256(local_data)}")
    print(f"  usb   size={len(remote_data)} crc32={crc32(remote_data)} sha256={sha256(remote_data)}")
    return 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("usb_root", type=Path, help=r"USB root, for example E:\ ")
    args = parser.parse_args()

    usb_opt = args.usb_root / "opt"
    failures = 0
    if not usb_opt.is_dir():
        print(f"[FAIL] USB opt folder not found - {usb_opt}")
        sys.exit(1)

    expected_set = {str(path).replace("\\", "/") for path in EXPECTED}
    for rel in EXPECTED:
        failures += check_file(LOCAL_OPT / rel, usb_opt / rel, rel)

    extras = []
    for path in usb_opt.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(usb_opt)
        if str(rel).replace("\\", "/") not in expected_set:
            extras.append(rel)
    if extras:
        failures += 1
        print("[FAIL] extra files under USB opt:")
        for rel in extras[:40]:
            print(f"  {rel}")
        if len(extras) > 40:
            print(f"  plus {len(extras) - 40} more")
    else:
        print("[PASS] no extra files under USB opt")

    if failures:
        print(f"USB verification FAILED: {failures}")
        sys.exit(1)
    print("USB verification PASSED")


if __name__ == "__main__":
    main()
