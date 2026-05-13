#!/usr/bin/env python3
"""Snapshot the current opt/ tree into releases/<name>/ as an immortalized build.

Each release folder gets a copy of the three payload binaries, an integrity
manifest with CRC32/SHA256 of every file, and a starter RELEASE.md the
operator can fill in with bench observations. The release folder is
self-contained: copying its opt/ subtree to a USB stick reproduces the
exact bench package.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import shutil
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_OPT = ROOT / "opt"
RELEASES = ROOT / "releases"

PAYLOAD = [
    Path("TurboSystem_sw/51.80.300.021/image.bin"),
    Path("TurboSystem_sw/51.80.300.021/eFilmLite/tempFL.bin"),
    Path("TurboSHDb/50.80.111.018/image.bin"),
]


def crc32(data: bytes) -> str:
    return f"{zlib.crc32(data) & 0xFFFFFFFF:08x}"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="release folder name, e.g. Project_Blueboot_0.0.1")
    parser.add_argument("--variant", required=True, help="short label for the variant, e.g. contact-string")
    parser.add_argument("--description", default="", help="one-line description for RELEASE.md")
    parser.add_argument("--bench-result", default="pass", choices=["pass", "fail", "untested"], help="bench outcome")
    parser.add_argument("--bench-note", default="", help="freeform bench observation")
    args = parser.parse_args()

    target = RELEASES / args.name
    if target.exists():
        raise SystemExit(f"error: release folder already exists: {target.relative_to(ROOT)}")

    rows = []
    for rel in PAYLOAD:
        source = ACTIVE_OPT / rel
        if not source.is_file():
            raise SystemExit(f"error: missing payload file in active opt/: {rel}")
        dest = target / "opt" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        data = dest.read_bytes()
        rows.append((str(rel).replace("\\", "/"), len(data), crc32(data), sha256(data)))
        print(f"snapshot: {rel} ({len(data):,} bytes, crc32={rows[-1][2]})")

    timestamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M %Z").strip()
    manifest_lines = ["# Integrity Manifest", "", f"Snapshot taken: {timestamp}", "", "| Path | Size | CRC32 | SHA256 |", "| --- | ---: | --- | --- |"]
    for rel, size, crc, sha in rows:
        manifest_lines.append(f"| `opt/{rel}` | {size} | `{crc}` | `{sha}` |")
    manifest_lines.append("")
    (target / "manifest.md").write_text("\n".join(manifest_lines), encoding="utf-8")

    release_lines = [
        f"# {args.name}",
        "",
        args.description or "(fill in description)",
        "",
        f"- Variant: `{args.variant}`",
        f"- Snapshot taken: {timestamp}",
        f"- Bench result: `{args.bench_result}`",
        f"- Bench note: {args.bench_note or '(fill in)'}",
        "",
        "## Install",
        "",
        "Copy the contents of this release's `opt/` folder to a FAT32 USB",
        "root, eject the stick, plug it into the M-Turbo, and run the upgrade",
        "from the unit's update flow.",
        "",
        "```powershell",
        f"Copy-Item -Recurse -Force releases\\{args.name}\\opt\\* <USB-drive>:\\opt\\",
        "python -B .\\tools\\verify_usb_package.py <USB-drive>:\\",
        f"python -B .\\tools\\recompute_image_checksums.py <USB-drive>:\\opt\\TurboSystem_sw\\51.80.300.021\\image.bin --check",
        f"python -B .\\tools\\recompute_image_checksums.py <USB-drive>:\\opt\\TurboSHDb\\50.80.111.018\\image.bin --check",
        "```",
        "",
        "All four invocations above should report PASS / [OK].",
        "",
        "## Integrity",
        "",
        "See `manifest.md` for per-file CRC32 and SHA256.",
        "",
        "## Reproduce",
        "",
        "From a fresh stock-parity tree, this snapshot can be rebuilt with:",
        "",
        "```powershell",
        f"python -B .\\tools\\make_test_package.py {args.variant}",
        f"python -B .\\tools\\snapshot_release.py {args.name} --variant {args.variant}",
        "```",
        "",
    ]
    (target / "RELEASE.md").write_text("\n".join(release_lines), encoding="utf-8")
    print(f"\nrelease snapshot written: {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
