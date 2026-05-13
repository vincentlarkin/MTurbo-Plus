#!/usr/bin/env python3
"""Build a stock-parity opt/ tree with parametric folder version bumps.

Use this to systematically probe the M-Turbo updater's version policy.
Each invocation creates a fresh opt/ tree containing the three known stock
binaries (byte-identical to 3.0clean) but under user-chosen version folders.

The embedded image-header version strings inside image.bin are NOT touched.
Bench history shows that tiny embedded edits trip the updater during the
Reading / system initialize stage, while pure folder-name bumps have been
accepted as long as the binaries inside stay byte-identical to stock.

This tool also keeps a running log of attempts in
analysis/version_attempts.md, so the bench operator does not have to track
"what did we already try" by hand.

Examples:

    python -B .\\tools\\make_versioned_package.py 51.80.300.016 50.80.111.013
    python -B .\\tools\\make_versioned_package.py --suite incremental
    python -B .\\tools\\make_versioned_package.py --record fail \\
        --note "device reported system preparation error at 30%"
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STOCK_SYSTEM_DIR = ROOT / "3.0clean" / "opt" / "TurboSystem_sw" / "51.80.300.015"
STOCK_SHDB_DIR = ROOT / "3.0clean" / "opt" / "TurboSHDb" / "50.80.111.012"
ACTIVE_OPT = ROOT / "opt"

LOG = ROOT / "analysis" / "version_attempts.md"

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)\.(\d+)$")
SYSTEM_BASE = "51.80.300"
SHDB_BASE = "50.80.111"


@dataclass(frozen=True)
class VersionPair:
    system: str
    shdb: str

    def label(self) -> str:
        return f"{self.system} / {self.shdb}"


def parse_version(value: str, base: str | None = None) -> tuple[int, int, int, int]:
    match = VERSION_RE.match(value)
    if not match:
        raise SystemExit(f"error: not a four-part version: {value!r}")
    parts = tuple(int(part) for part in match.groups())
    if base and not value.startswith(base + "."):
        print(
            f"warn: {value!r} does not share base `{base}` with stock; updater may "
            "reject it for product-line reasons.",
            file=sys.stderr,
        )
    return parts


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def build_opt_tree(target_root: Path, system_version: str, shdb_version: str) -> None:
    target_root = target_root.resolve()
    if target_root.exists():
        shutil.rmtree(target_root)
    system_target_dir = target_root / "TurboSystem_sw" / system_version
    shdb_target_dir = target_root / "TurboSHDb" / shdb_version
    system_target_dir.mkdir(parents=True, exist_ok=True)
    shdb_target_dir.mkdir(parents=True, exist_ok=True)
    (system_target_dir / "eFilmLite").mkdir(parents=True, exist_ok=True)

    pairs: list[tuple[Path, Path]] = [
        (
            STOCK_SYSTEM_DIR / "image.bin",
            system_target_dir / "image.bin",
        ),
        (
            STOCK_SYSTEM_DIR / "eFilmLite" / "tempFL.bin",
            system_target_dir / "eFilmLite" / "tempFL.bin",
        ),
        (
            STOCK_SHDB_DIR / "image.bin",
            shdb_target_dir / "image.bin",
        ),
    ]
    for source, target in pairs:
        if not source.is_file():
            raise SystemExit(f"error: missing stock source: {display_path(source)}")
        shutil.copy2(source, target)
        print(f"copied {display_path(source)} -> {display_path(target)}")


def suite_versions(name: str) -> list[VersionPair]:
    if name == "incremental":
        return [
            VersionPair(f"{SYSTEM_BASE}.016", f"{SHDB_BASE}.013"),
            VersionPair(f"{SYSTEM_BASE}.017", f"{SHDB_BASE}.014"),
            VersionPair(f"{SYSTEM_BASE}.018", f"{SHDB_BASE}.015"),
        ]
    if name == "max":
        return [VersionPair(f"{SYSTEM_BASE}.999", f"{SHDB_BASE}.999")]
    if name == "stock-folder":
        return [VersionPair(f"{SYSTEM_BASE}.015", f"{SHDB_BASE}.012")]
    if name == "current":
        return [VersionPair(f"{SYSTEM_BASE}.021", f"{SHDB_BASE}.018")]
    raise SystemExit(f"error: unknown suite `{name}`")


def append_log(record: dict[str, str]) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    if not LOG.exists():
        LOG.write_text(
            "# Version Attempts\n"
            "\n"
            "Each row is one bench test of a parametric folder-bump package.\n"
            "Use `make_versioned_package.py --record` to add results after USB\n"
            "tests so we don't burn the same flash cycle twice.\n"
            "\n"
            "| When | System | SHDb | Result | Notes |\n"
            "| --- | --- | --- | --- | --- |\n",
            encoding="utf-8",
        )
    row = (
        f"| {timestamp} | `{record['system']}` | `{record['shdb']}` | "
        f"`{record['result']}` | {record['note'] or '-'} |\n"
    )
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(row)


def update_current_test_manifest(version: VersionPair, message: str) -> None:
    manifest = ROOT / "analysis" / "current_test_package.md"
    body = (
        "# Current Test Package\n\n"
        f"Variant: `versioned-{version.system}_{version.shdb}`\n\n"
        f"{message}\n\n"
        "Diff summary:\n\n"
        "```text\n"
        f"system folder: {version.system}\n"
        f"SHDb folder:   {version.shdb}\n"
        "system image: byte-identical to 3.0clean stock\n"
        "SHDb image:   byte-identical to 3.0clean stock\n"
        "tempFL:       byte-identical to 3.0clean stock\n"
        "```\n\n"
        "Reset to the documented stock-parity baseline with:\n\n"
        "```powershell\n"
        "python -B .\\tools\\rebuild_stock_parity_package.py\n"
        "```\n",
    )
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("".join(body), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("system_version", nargs="?", help="e.g. 51.80.300.016")
    parser.add_argument("shdb_version", nargs="?", help="e.g. 50.80.111.013")
    parser.add_argument(
        "--suite",
        choices=["incremental", "max", "stock-folder", "current"],
        help="print a suite of pre-baked version pairs (no files written)",
    )
    parser.add_argument(
        "--record",
        choices=["pass", "fail", "skip"],
        help="append the resulting bench result to analysis/version_attempts.md without rebuilding",
    )
    parser.add_argument("--note", default="", help="free-form note for the version log row")
    parser.add_argument(
        "--target",
        type=Path,
        default=ACTIVE_OPT,
        help="target opt root (default: opt/ in the repo)",
    )
    args = parser.parse_args()

    if args.suite:
        for pair in suite_versions(args.suite):
            print(pair.label())
        return

    if args.record:
        if not (args.system_version and args.shdb_version):
            raise SystemExit("error: --record requires both system_version and shdb_version")
        append_log(
            {
                "system": args.system_version,
                "shdb": args.shdb_version,
                "result": args.record,
                "note": args.note,
            }
        )
        print(f"recorded {args.record} for {args.system_version} / {args.shdb_version}")
        return

    if not (args.system_version and args.shdb_version):
        raise SystemExit("error: provide system_version and shdb_version (or use --suite)")

    parse_version(args.system_version, base=SYSTEM_BASE)
    parse_version(args.shdb_version, base=SHDB_BASE)

    build_opt_tree(args.target, args.system_version, args.shdb_version)
    pair = VersionPair(args.system_version, args.shdb_version)
    msg = (
        f"built parametric package: system folder `{pair.system}`, SHDb folder "
        f"`{pair.shdb}`. Embedded image-header versions are stock; only the "
        "USB-visible folder names changed."
    )
    if args.target.resolve() == ACTIVE_OPT.resolve():
        update_current_test_manifest(pair, msg)
    else:
        print("note: --target points outside the active opt/; current_test_package.md not updated")
    print(msg)
    print()
    print("next steps:")
    print(
        "  1. python -B .\\tools\\verify_usb_package.py <USB drive>  (after copying opt/ to USB)"
    )
    print(
        "  2. python -B .\\tools\\inspect_usb_package.py <USB drive>"
    )
    print(
        f"  3. python -B .\\tools\\make_versioned_package.py {pair.system} {pair.shdb} \\"
    )
    print('         --record pass|fail --note "<bench observation>"')


if __name__ == "__main__":
    main()
