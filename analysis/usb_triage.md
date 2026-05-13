# USB Triage

This is the active flow when a USB update fails on the M-Turbo with the
"system preparation" error. The failure modes split into two layers:

1. **Filesystem / package-shape layer.** Even a byte-identical stock-parity
   `opt/` tree on a USB stick can be rejected here. This is the layer that
   `tools/inspect_usb_package.py` is for.
2. **Binary integrity layer.** Edits inside `image.bin` need the per-stream
   descriptor CRCs and the outer header CRC refreshed before the unit will
   accept them. This is now solved end-to-end by
   `tools/recompute_image_checksums.py`. Earlier failed bench tests
   (`system-zlib-recompress-noop`, `system-slack-byte`) are explained by
   this layer being skipped.

## Decision Tree

```
"system preparation" error
    |
    +-- Did stock-parity copy ALSO fail this run? (yes -> filesystem layer)
    |       |
    |       +-- Filesystem layer probes (in order):
    |             1. python -B .\tools\inspect_usb_package.py <USB drive>
    |                  - confirms FAT/FAT32, no hidden Windows/macOS metadata,
    |                    no extra files, expected layout, byte parity.
    |             2. If inspect is clean, the bench finding is contradictory:
    |                  - reformat the USB clean as FAT32 with the M-Turbo's
    |                    native tool or `format E: /q /fs:fat32` on Windows.
    |                  - re-test with stock-parity opt/.
    |             3. If still failing, suspect version policy:
    |                  - python -B .\tools\make_versioned_package.py 51.80.300.016 50.80.111.013
    |                    (incremental from stock 015/012 -- minimum next valid bump).
    |                  - copy opt/ to USB, retest.
    |                  - python -B .\tools\make_versioned_package.py 51.80.300.016 50.80.111.013 \
    |                        --record pass|fail --note "<observation>"
    |                  - keep walking up: .017, .018, ..., .021, .999.
    |
    +-- Stock-parity copy passed; only edited image fails? (yes -> binary layer)
            |
            +-- python -B .\tools\recompute_image_checksums.py opt\TurboSystem_sw\<ver>\image.bin --check
                  - if any [FIX] lines appear, run --write before re-testing.
            +-- python -B .\tools\recompute_image_checksums.py opt\TurboSHDb\<ver>\image.bin --check
            +-- if both check clean, the unit's integrity gate is something
                else (eg signature). Switch back to RE: load stream1 in Ghidra
                with proper image base and trace the descriptor consumer.
```

## What's Known About The Filesystem Layer

- The bench operator's last finding was that copying the current
  stock-parity `opt/` tree to the USB stick still produced the system
  preparation error. That contradicts the older note that says folder-bump
  packages had been accepted on this same hardware. So one of these has
  changed since the older test:
  - The USB stick or filesystem (re-formatted, different size, different
    label, brought in metadata).
  - The unit's installed firmware version (an upgrade gates by "must be
    newer", and the .021/.018 bumps may no longer be considered newer).
  - The bumped-folder rule itself (the older test may have used a
    `.016/.013` style increment, not `.021/.018`; we never recorded the
    exact bump that worked).

`tools/inspect_usb_package.py` reports filesystem type, label, serial,
case sensitivity, every file under the USB root with attributes, and any
windows/mac/linux metadata directories that should be deleted. Run it on
both the failing stick and a known-good baseline (eg the original M-Turbo
3.0 install media) to compare.

## What's Known About The Binary Layer

Three layers, all standard CRC32:

| Layer | Field offset | Covered range | Stock value |
| --- | --- | --- | --- |
| System outer header CRC | `0x4` | `0x8..0x24bb9c` | `0x6332d5eb` |
| System per-stream descriptor CRC (5x) | `desc + 4` for each desc at `0x24bb9c, 0x676104, 0x677516, 0x677d42, 0x1323127` | `desc + 8` to start of next descriptor (or end of file) | see `analysis/descriptor_checksum_notes.md` |
| SHDb outer header CRC | `0x4` | `0x8..end` | `0x77d4f17f` |

Reseal flow after any byte edit:

```powershell
python -B .\tools\recompute_image_checksums.py opt\TurboSystem_sw\51.80.300.021\image.bin --write
python -B .\tools\recompute_image_checksums.py opt\TurboSHDb\50.80.111.018\image.bin --write
```

`tools/make_test_package.py` now auto-reseals after every variant. Use
`--no-reseal` only when intentionally reproducing the older
broken-integrity tests.

## Open Questions

- Is the unit's installed firmware version above or below `51.80.300.015`?
  We do not have an explicit reading of the running version on the bench.
  An "About" / "System Information" screen should expose it.
- Did the older successful test use `51.80.300.016` (minimum increment) or
  `51.80.300.021` (current bump)? Recording this would tell us whether the
  policy is "any newer" vs "next valid".
- Does the unit accept a stock-parity package that uses the **stock**
  folder names (`51.80.300.015` / `50.80.111.012`)? That probes whether the
  updater requires a strictly higher folder version vs whether it just
  reads `image.bin` and trusts its embedded version.
  - `python -B .\tools\make_versioned_package.py 51.80.300.015 50.80.111.012`
- Is there ANY other expected file/marker on the USB beyond the three
  payload files? `tools/inspect_usb_package.py` lists everything we have
  on a known-good copy; if the unit needs eg a top-level marker or a
  signed manifest we have not seen, that would show up only after a
  positive comparison against a known-working stick.
