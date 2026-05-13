#!/usr/bin/env python3
"""Deep diagnostic for a copied USB update package.

The default `verify_usb_package.py` only confirms byte parity for the three
expected files. The bench finding is that a byte-identical stock-parity opt/
tree on USB still produces the same `system preparation error`. So the
remaining suspects are filesystem-level: filesystem type, volume label,
hidden/system metadata, file attributes, case sensitivity, encoding, and
extra/garbage files the updater may also be reading.

This tool walks the USB root and reports everything that could explain a
filesystem-level rejection. It never writes to the USB and never deletes
anything; the operator decides what to fix based on the report.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import os
import string
import sys
import zlib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL_OPT = ROOT / "opt"
EXPECTED_RELATIVE = [
    Path("opt/TurboSystem_sw/51.80.300.021/image.bin"),
    Path("opt/TurboSystem_sw/51.80.300.021/eFilmLite/tempFL.bin"),
    Path("opt/TurboSHDb/50.80.111.018/image.bin"),
]

ATTR_FLAGS = [
    (0x01, "READONLY"),
    (0x02, "HIDDEN"),
    (0x04, "SYSTEM"),
    (0x10, "DIRECTORY"),
    (0x20, "ARCHIVE"),
    (0x40, "DEVICE"),
    (0x80, "NORMAL"),
    (0x100, "TEMPORARY"),
    (0x200, "SPARSE_FILE"),
    (0x400, "REPARSE_POINT"),
    (0x800, "COMPRESSED"),
    (0x1000, "OFFLINE"),
    (0x2000, "NOT_CONTENT_INDEXED"),
    (0x4000, "ENCRYPTED"),
]


@dataclass
class VolumeInfo:
    drive: str
    label: str = ""
    serial: str = ""
    fs_type: str = ""
    total_bytes: int = 0
    free_bytes: int = 0
    case_sensitive_paths: bool | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class FileEntry:
    path: Path
    size: int
    attributes: int
    crc32: str
    sha256: str
    is_hidden: bool
    is_system: bool
    is_reparse: bool


def fmt_bytes(value: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:,.1f} {unit}"
        size /= 1024
    return f"{value} B"


def parse_attributes(attrs: int) -> str:
    if attrs == 0:
        return "0"
    matched = [name for flag, name in ATTR_FLAGS if attrs & flag]
    return f"0x{attrs:x} [{', '.join(matched) if matched else 'NONE'}]"


def get_volume_info_windows(drive_root: str) -> VolumeInfo:
    info = VolumeInfo(drive=drive_root)
    if not sys.platform.startswith("win"):
        info.notes.append("non-Windows platform: filesystem details limited")
        try:
            stat = os.statvfs(drive_root)
            info.total_bytes = stat.f_blocks * stat.f_frsize
            info.free_bytes = stat.f_bavail * stat.f_frsize
        except (OSError, AttributeError):
            pass
        return info

    try:
        kernel32 = ctypes.windll.kernel32
    except (AttributeError, OSError) as exc:
        info.notes.append(f"could not load kernel32: {exc}")
        return info

    label_buf = ctypes.create_unicode_buffer(261)
    fs_buf = ctypes.create_unicode_buffer(261)
    serial = ctypes.c_uint(0)
    max_component = ctypes.c_uint(0)
    fs_flags = ctypes.c_uint(0)

    drive_param = drive_root if drive_root.endswith("\\") else drive_root + "\\"
    ok = kernel32.GetVolumeInformationW(
        drive_param,
        label_buf,
        len(label_buf),
        ctypes.byref(serial),
        ctypes.byref(max_component),
        ctypes.byref(fs_flags),
        fs_buf,
        len(fs_buf),
    )
    if ok:
        info.label = label_buf.value
        info.fs_type = fs_buf.value
        info.serial = f"{serial.value:08X}"
        info.case_sensitive_paths = bool(fs_flags.value & 0x00000001)
    else:
        info.notes.append("GetVolumeInformationW failed")

    free_total = ctypes.c_ulonglong(0)
    total = ctypes.c_ulonglong(0)
    free_avail = ctypes.c_ulonglong(0)
    if kernel32.GetDiskFreeSpaceExW(
        drive_param,
        ctypes.byref(free_avail),
        ctypes.byref(total),
        ctypes.byref(free_total),
    ):
        info.total_bytes = total.value
        info.free_bytes = free_avail.value
    return info


def crc32(data: bytes) -> str:
    return f"{zlib.crc32(data) & 0xffffffff:08x}"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_attributes(path: Path) -> int:
    if not sys.platform.startswith("win"):
        return 0
    try:
        return ctypes.windll.kernel32.GetFileAttributesW(str(path))
    except OSError:
        return 0


def collect_entries(root: Path) -> list[FileEntry]:
    entries: list[FileEntry] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            entries.append(
                FileEntry(
                    path=path,
                    size=-1,
                    attributes=file_attributes(path),
                    crc32=f"read-error: {exc}",
                    sha256="",
                    is_hidden=False,
                    is_system=False,
                    is_reparse=False,
                )
            )
            continue
        attrs = file_attributes(path)
        entries.append(
            FileEntry(
                path=path,
                size=len(data),
                attributes=attrs,
                crc32=crc32(data),
                sha256=sha256(data),
                is_hidden=bool(attrs & 0x02),
                is_system=bool(attrs & 0x04),
                is_reparse=bool(attrs & 0x400),
            )
        )
    return entries


def relative_posix(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def categorize_extras(usb_root: Path, entries: list[FileEntry]) -> dict[str, list[FileEntry]]:
    expected_set = {str(rel).replace("\\", "/") for rel in EXPECTED_RELATIVE}
    buckets: dict[str, list[FileEntry]] = {
        "expected_payload": [],
        "windows_metadata": [],
        "macos_metadata": [],
        "spotlight_thumbnails": [],
        "recycle_bin": [],
        "trashes": [],
        "hidden_or_system": [],
        "other_extras": [],
    }
    for entry in entries:
        rel = relative_posix(entry.path, usb_root)
        rel_lower = rel.lower()
        if rel in expected_set:
            buckets["expected_payload"].append(entry)
            continue
        if "system volume information" in rel_lower:
            buckets["windows_metadata"].append(entry)
            continue
        if rel_lower.startswith("$recycle.bin"):
            buckets["recycle_bin"].append(entry)
            continue
        if rel_lower.startswith(".trashes") or rel_lower.startswith(".trash-"):
            buckets["trashes"].append(entry)
            continue
        if rel_lower.startswith(".spotlight-v100") or rel_lower.startswith(".fseventsd"):
            buckets["spotlight_thumbnails"].append(entry)
            continue
        if rel_lower.startswith("._") or rel_lower.endswith(".ds_store"):
            buckets["macos_metadata"].append(entry)
            continue
        if entry.is_hidden or entry.is_system:
            buckets["hidden_or_system"].append(entry)
            continue
        buckets["other_extras"].append(entry)
    return buckets


def case_check(usb_root: Path, expected: list[Path]) -> list[str]:
    issues: list[str] = []
    actual_paths = {relative_posix(path, usb_root): path for path in usb_root.rglob("*")}
    for rel in expected:
        rel_str = str(rel).replace("\\", "/")
        if rel_str in actual_paths:
            continue
        lower_match = next(
            (actual for actual in actual_paths if actual.lower() == rel_str.lower()),
            None,
        )
        if lower_match is None:
            issues.append(f"expected path missing: {rel_str}")
            continue
        if lower_match != rel_str:
            issues.append(
                f"case mismatch: expected `{rel_str}`, USB has `{lower_match}`"
            )
    return issues


def encoding_check(usb_root: Path) -> list[str]:
    issues: list[str] = []
    for path in usb_root.rglob("*"):
        try:
            name = path.name
            name.encode("ascii")
        except UnicodeEncodeError:
            issues.append(f"non-ASCII character in path: {path}")
        if any(ch in name for ch in string.whitespace if ch not in (" ",)):
            issues.append(f"whitespace control character in path: {path}")
    return issues


def parity_compare(usb_root: Path) -> tuple[list[str], list[str]]:
    matches: list[str] = []
    mismatches: list[str] = []
    for rel in EXPECTED_RELATIVE:
        local = LOCAL_OPT / rel.relative_to("opt")
        remote = usb_root / rel
        rel_str = str(rel).replace("\\", "/")
        if not local.is_file():
            mismatches.append(f"local missing: {rel_str}")
            continue
        if not remote.is_file():
            mismatches.append(f"USB missing: {rel_str}")
            continue
        local_data = local.read_bytes()
        remote_data = remote.read_bytes()
        if local_data == remote_data:
            matches.append(rel_str)
            continue
        local_crc = crc32(local_data)
        remote_crc = crc32(remote_data)
        local_sha = sha256(local_data)
        remote_sha = sha256(remote_data)
        mismatches.append(
            f"{rel_str}: local size={len(local_data)} crc32={local_crc} sha256={local_sha}"
        )
        mismatches.append(
            f"{rel_str}: usb   size={len(remote_data)} crc32={remote_crc} sha256={remote_sha}"
        )
    return matches, mismatches


def render_volume_block(volume: VolumeInfo) -> list[str]:
    lines = [
        "## Volume",
        "",
        f"- drive: `{volume.drive}`",
        f"- label: `{volume.label or '(unlabeled)'}`",
        f"- serial: `{volume.serial or 'unknown'}`",
        f"- filesystem: `{volume.fs_type or 'unknown'}`",
        f"- total size: {fmt_bytes(volume.total_bytes)}",
        f"- free space: {fmt_bytes(volume.free_bytes)}",
        f"- case-sensitive paths: `{volume.case_sensitive_paths}`",
    ]
    if volume.notes:
        lines.append("- notes:")
        for note in volume.notes:
            lines.append(f"  - {note}")
    fs = (volume.fs_type or "").upper()
    if fs and fs not in {"FAT", "FAT16", "FAT32"}:
        lines.append("")
        lines.append(
            f"- WARN: filesystem `{fs}` may not be readable by the M-Turbo updater. "
            "Bench history shows USB sticks formatted as FAT/FAT32. Try reformatting "
            "as FAT32 if updates keep failing."
        )
    return lines


def render_extras(buckets: dict[str, list[FileEntry]], usb_root: Path) -> list[str]:
    lines = ["## Files", ""]
    expected = buckets["expected_payload"]
    lines.append(f"- expected payload files present: {len(expected)} / {len(EXPECTED_RELATIVE)}")
    for entry in expected:
        rel = relative_posix(entry.path, usb_root)
        attrs = parse_attributes(entry.attributes)
        lines.append(
            f"  - `{rel}` size={entry.size} crc32=`{entry.crc32}` attr={attrs}"
        )

    def bucket_section(key: str, label: str, warn: str | None) -> None:
        items = buckets[key]
        if not items:
            return
        lines.append("")
        lines.append(f"### {label}: {len(items)}")
        if warn:
            lines.append("")
            lines.append(f"- {warn}")
        lines.append("")
        for entry in items[:40]:
            rel = relative_posix(entry.path, usb_root)
            attrs = parse_attributes(entry.attributes)
            size = entry.size if entry.size >= 0 else "?"
            lines.append(f"  - `{rel}` size={size} attr={attrs}")
        if len(items) > 40:
            lines.append(f"  - plus {len(items) - 40} more")

    bucket_section(
        "windows_metadata",
        "Windows metadata",
        "OK to delete: usually `System Volume Information/`. Some USB cases use `format /q E: /fs:fat32` to clear it.",
    )
    bucket_section(
        "macos_metadata",
        "macOS metadata (./_*, .DS_Store)",
        "DELETE before testing. macOS hidden resource forks confuse some FAT readers.",
    )
    bucket_section(
        "spotlight_thumbnails",
        "macOS Spotlight indexes",
        "DELETE before testing.",
    )
    bucket_section("recycle_bin", "Recycle bin", "DELETE before testing.")
    bucket_section("trashes", "Linux/macOS trashes", "DELETE before testing.")
    bucket_section(
        "hidden_or_system",
        "Other hidden/system files",
        "Investigate. Stock package has none.",
    )
    bucket_section(
        "other_extras",
        "Other extras outside expected payload",
        "WARN: these are NOT part of the stock package. Stock USB layout has only the three payload files under opt/.",
    )
    return lines


def render_root_layout(usb_root: Path) -> list[str]:
    lines = ["## USB Root Layout", ""]
    direct = sorted(item for item in usb_root.iterdir())
    if not direct:
        lines.append("- USB root is empty")
        return lines
    for item in direct:
        kind = "DIR " if item.is_dir() else "FILE"
        rel = relative_posix(item, usb_root)
        attrs = parse_attributes(file_attributes(item))
        lines.append(f"- {kind} `{rel}` attr={attrs}")
    if not any(item.is_dir() and item.name.lower() == "opt" for item in direct):
        lines.append("")
        lines.append(
            "- WARN: no `opt/` directory at USB root. Bench history shows the M-Turbo "
            "updater expects `opt/TurboSystem_sw/<ver>/image.bin` and "
            "`opt/TurboSHDb/<ver>/image.bin` directly under the USB root."
        )
    return lines


def render_parity(usb_root: Path) -> list[str]:
    matches, mismatches = parity_compare(usb_root)
    lines = ["## Byte-Level Parity Vs Local Opt", ""]
    if matches:
        lines.append(f"- byte-identical: {len(matches)}")
        for rel in matches:
            lines.append(f"  - `{rel}`")
    else:
        lines.append("- byte-identical: 0")
    if mismatches:
        lines.append(f"- mismatch / missing: {len(mismatches)}")
        for line in mismatches:
            lines.append(f"  - {line}")
    return lines


def render_path_checks(usb_root: Path) -> list[str]:
    lines = ["## Path Checks", ""]
    case_issues = case_check(usb_root, EXPECTED_RELATIVE)
    if case_issues:
        lines.append("- case/path issues:")
        for issue in case_issues:
            lines.append(f"  - {issue}")
    else:
        lines.append("- case/path: matches expected layout")

    encoding_issues = encoding_check(usb_root)
    if encoding_issues:
        lines.append("- encoding issues:")
        for issue in encoding_issues[:20]:
            lines.append(f"  - {issue}")
        if len(encoding_issues) > 20:
            lines.append(f"  - plus {len(encoding_issues) - 20} more")
    else:
        lines.append("- encoding: all path names ASCII")
    return lines


def build_report(usb_root: Path) -> str:
    drive = str(usb_root)
    if sys.platform.startswith("win") and len(drive) >= 2 and drive[1] == ":":
        drive_letter = drive[:2] + "\\"
    else:
        drive_letter = drive
    volume = get_volume_info_windows(drive_letter)
    entries = collect_entries(usb_root)
    buckets = categorize_extras(usb_root, entries)

    lines = [
        "# USB Package Inspection",
        "",
        f"USB root: `{usb_root}`",
        f"Local opt: `{LOCAL_OPT}`",
        "",
    ]
    lines.extend(render_volume_block(volume))
    lines.append("")
    lines.extend(render_root_layout(usb_root))
    lines.append("")
    lines.extend(render_parity(usb_root))
    lines.append("")
    lines.extend(render_extras(buckets, usb_root))
    lines.append("")
    lines.extend(render_path_checks(usb_root))
    lines.append("")

    expected_set = {str(rel).replace("\\", "/") for rel in EXPECTED_RELATIVE}
    actual_set = {relative_posix(entry.path, usb_root) for entry in entries}
    missing = sorted(expected_set - actual_set)
    extras = sorted(actual_set - expected_set)
    issues: list[str] = []
    if missing:
        issues.append(f"{len(missing)} expected file(s) missing")
    if extras:
        issues.append(f"{len(extras)} extra file(s) on USB")
    if (volume.fs_type or "").upper() not in {"FAT", "FAT16", "FAT32", ""}:
        issues.append(f"non-FAT filesystem `{volume.fs_type}`")

    lines.append("## Summary")
    lines.append("")
    if issues:
        lines.append("- issues:")
        for issue in issues:
            lines.append(f"  - {issue}")
    else:
        lines.append("- no filesystem-level issues detected against the stock layout")
        lines.append(
            "- if the unit still rejects this USB, the next suspect is the version "
            "policy on the bumped folder names. Try `make_versioned_package.py` with "
            "an incremental version (e.g. `51.80.300.016` / `50.80.111.013`)."
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("usb_root", type=Path, help=r"USB root, for example E:\\")
    parser.add_argument(
        "--write",
        type=Path,
        default=ROOT / "analysis" / "usb_inspection.md",
        help="output markdown report path (default: analysis/usb_inspection.md)",
    )
    parser.add_argument("--stdout", action="store_true", help="print report to stdout instead of writing")
    args = parser.parse_args()

    usb_root: Path = args.usb_root
    if not usb_root.exists():
        print(f"error: USB root does not exist: {usb_root}", file=sys.stderr)
        sys.exit(2)
    if not usb_root.is_dir():
        print(f"error: USB root is not a directory: {usb_root}", file=sys.stderr)
        sys.exit(2)

    report = build_report(usb_root)
    if args.stdout:
        print(report)
        return
    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(report, encoding="utf-8")
    print(f"wrote {args.write.relative_to(ROOT)}")
    print(report)


if __name__ == "__main__":
    main()
