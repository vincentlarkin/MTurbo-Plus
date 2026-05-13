#!/usr/bin/env python3
"""Rebuild the active USB payload from stock binaries with bumped folders."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FILES = [
    (
        ROOT / "3.0clean" / "opt" / "TurboSystem_sw" / "51.80.300.015" / "image.bin",
        ROOT / "opt" / "TurboSystem_sw" / "51.80.300.021" / "image.bin",
    ),
    (
        ROOT / "3.0clean" / "opt" / "TurboSystem_sw" / "51.80.300.015" / "eFilmLite" / "tempFL.bin",
        ROOT / "opt" / "TurboSystem_sw" / "51.80.300.021" / "eFilmLite" / "tempFL.bin",
    ),
    (
        ROOT / "3.0clean" / "opt" / "TurboSHDb" / "50.80.111.012" / "image.bin",
        ROOT / "opt" / "TurboSHDb" / "50.80.111.018" / "image.bin",
    ),
]


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for source, target in FILES:
        if not source.is_file():
            fail(f"missing stock source: {source.relative_to(ROOT)}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        print(f"copied {source.relative_to(ROOT)} -> {target.relative_to(ROOT)}")

    print("stock-parity package rebuilt")


if __name__ == "__main__":
    main()
