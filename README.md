# MTurbo-Plus Firmware Package Notes

This repo is a binary M-Turbo USB update package. It is not a source build
tree.

Bench/test device only. Not for clinical use.

## Project Blueboot

We have a fully-editable, bench-installable binary path. Curated working
firmware builds live in `releases/`:

| Version | Variant | Bench result |
| --- | --- | --- |
| `Project_Blueboot_0.0.1` | `system-contact-string` | PASS |
| `Project_Blueboot_0.0.2` | `system-blueboot-bundle` (splash + contact string) | PASS |
| `Project_Blueboot_0.1.0` | `system-larkrom-bundle` (full LarkROM/Blueboot rebrand) | FAIL - do not install |
| `Project_Blueboot_0.1.1` | `system-larkrom-bundle` (tail-preserving LarkROM/Blueboot rebrand) | UNTESTED |

Each release has its own `RELEASE.md` and a self-contained `opt/` tree
that can be copied straight to a USB stick. See `releases/README.md` for
the full release-pipeline writeup.

The current strategy for new builds:

1. Keep `.bin` byte-identical to stock `3.0clean` *unless* the active test
   intentionally changes one thing.
2. Bump only the `opt/` folder names (`51.80.300.015` -> `51.80.300.021`,
   `50.80.111.012` -> `50.80.111.018`) so the updater offers the package.
3. After any byte edit, let `tools/make_test_package.py` auto-reseal the
   per-stream descriptor stored words and the outer header CRC. Both
   layers are now fully understood (`analysis/descriptor_checksum_notes.md`).
4. Snapshot bench-confirmed builds with `tools/snapshot_release.py`.

## Current Package Layout

```text
opt/
  TurboSystem_sw/51.80.300.021/
    image.bin
    eFilmLite/tempFL.bin
  TurboSHDb/50.80.111.018/
    image.bin

3.0clean/
  opt/TurboSystem_sw/51.80.300.015/
    image.bin
    eFilmLite/tempFL.bin
  opt/TurboSHDb/50.80.111.012/
    image.bin
```

`3.0clean` is the stock source of truth. `opt` is the USB payload tree.
When `tools/make_test_package.py` is used, check
`analysis/current_test_package.md` for the exact active `opt` variant before
copying to USB.

## What The Binaries Are

| Path | Size | CRC32 | What it is |
| --- | ---: | --- | --- |
| `opt/TurboSystem_sw/51.80.300.021/image.bin` | 20,368,530 | `3a25b18d` | Main ARM system firmware image. The embedded header string remains stock: `51.80.300.015`. |
| `opt/TurboSystem_sw/51.80.300.021/eFilmLite/tempFL.bin` | 37 | `3da4bd54` | Plain marker file: `Temp file to allow upgrade to proceed`. Unchanged from stock. |
| `opt/TurboSHDb/50.80.111.018/image.bin` | 230,849,960 | `e6874a61` | Scanhead/transducer database package. The embedded header string remains stock: `50.80.111.012`. |

The bumped folder names are intentional:

- System folder: `51.80.300.015` -> `51.80.300.021`
- Scanhead DB folder: `50.80.111.012` -> `50.80.111.018`

Bench finding to preserve: this directory version bump is necessary when
updating from the latest 3.0 package, and it works perfectly when the binaries
inside those bumped directories are otherwise stock.

The embedded image headers are not bumped. Prior testing showed that tiny
embedded header edits can trip the updater during the `Reading` / system
initialize stage.

## Known System Image Internals

These are for validation and triage, not for the active package:

- System image header version slot: offset `0x8`, value `51.80.300.015`.
- System outer header CRC: offset `0x4`, value `0x6332d5eb`.
  This is standard CRC32 over `image.bin[0x8:0x24bb9c]`.
- SHDb outer header CRC: offset `0x4`, value `0x77d4f17f`.
  This is standard CRC32 over `image.bin[0x8:end]`.
- Sync-word boot/configuration regions:
  - `0x00000030-0x00159660`
  - `0x00159660-0x0021d5d8`
  - `0x0021d5d8-0x0024bbb5`
  These start with `55 99 aa 66`, the byte order seen for the Xilinx
  `0xaa995566` sync word. Treat these as protected boot/configuration regions.
- Boot splash pointer table: offset `0x214edc`, 12 frame pointers.
  Frame 11 is special: its image decode consumes `42368` bytes but the chunk
  is `48242` bytes, leaving a `5874` byte non-frame tail before the pointer
  table. Preserve that tail byte-for-byte.
- Main zlib application payload:
  - offset `0x24bbb5`
  - compressed length `0x42a54a`
  - inflated length `0xd25b98`
  - zlib Adler-32 trailer `0x0fd8b686`
- Main zlib descriptor:
  - descriptor offset `0x24bb9c`
  - magic `0xaabb0340`
  - stored word `0x224fc950`
  - start field `0x24bbb4`
  - end field `0x676104`

There are five zlib descriptors. Each one's `stored_word` is now solved:
it is standard CRC32 over the descriptor bytes from `desc + 8` (right after
`stored_word`) up to the start of the next descriptor (or end-of-file for
the last). See `analysis/descriptor_checksum_notes.md` for the verified
formula. `tools/recompute_image_checksums.py` rewrites all descriptor
stored words plus the outer header CRC after any payload edit.

Changing one visible string inside the main zlib payload rewrites the
compressed bytes after recompression. With the descriptor CRC layer now
solved, that is no longer noisy: reseal with
`tools/recompute_image_checksums.py` and the package is consistent again.

## Working Rule

For the active USB package:

1. Bump only the folder names under `opt/`.
2. Keep embedded image-header versions stock.
3. Keep `image.bin` and `tempFL.bin` byte-identical to `3.0clean` unless the
   current test intentionally changes one thing.
4. Verify CRC/SHA parity or the exact intended diff before every USB test.
5. Treat any byte change inside either `image.bin` as likely covered by the
   updater's integrity path unless proven otherwise.
6. Do not use the pre-zlib sync-word regions for harmless-byte tests. They are
   boot/configuration material, even where long zero runs appear.
7. If a test changes bytes before `0x24bb9c`, recompute the system outer header
   CRC before considering it a valid probe.

## Rebuild And Verify

Rebuild the current parity package from `3.0clean`:

```powershell
python .\tools\rebuild_stock_parity_package.py
```

Verify exact binary parity and print hashes:

```powershell
python .\tools\verify_current_package.py --details
```

Add `--deep` when chasing checksum fields. It also searches for obvious
32-bit length/CRC/Adler constants outside the main zlib stream:

```powershell
python .\tools\verify_current_package.py --details --deep
```

Then copy the `opt/` folder to the USB root for the normal M-Turbo update
flow.

## Tools

Active tools:

- `tools/firmware_map.py` - writes `analysis/firmware_map.json` and
  `analysis/firmware_map.md` with hashes, sync-word regions, zlib streams,
  splash chunks, candidate constants, and SHDb resource-name hints.
- `tools/make_test_package.py` - rebuilds from stock, applies one named test
  variant into `opt/`, auto-reseals integrity layers (use `--no-reseal` to
  reproduce the older broken-integrity tests), prints the exact diff, and
  writes `analysis/current_test_package.md`. Variants include `stock`,
  `system-contact-string`, `system-splash-blueboot`,
  `system-blueboot-bundle` (splash + contact string),
  `system-larkrom-bundle` (all 12 splash frames + LarkROM stream1 strings),
  and the legacy probes `system-slack-byte`, `system-zlib-recompress-noop`,
  etc.
- `tools/patch_larkrom_rebrand.py` - production string patcher for the
  LarkROM/Blueboot stream1 labels. Restores the real fujifilm support email,
  rebrands the visible contact/sysinfo labels, simplifies the support phone
  line, updates the password-reset contact and patent-list title, and avoids
  path/object/mode strings.
- `tools/snapshot_release.py` - copies the current active opt/ tree into
  `releases/<name>/`, writes a per-file `manifest.md` (size + CRC32 + SHA256)
  and a starter `RELEASE.md` with install instructions and bench notes.
  Use this to immortalize a bench-confirmed build.
- `tools/make_versioned_package.py` - parametric folder-version bumps for
  systematic version probing. Lets you build, eg, `51.80.300.016` /
  `50.80.111.013` without hand-editing folders. Records bench results in
  `analysis/version_attempts.md` so we don't burn the same flash cycle
  twice.
- `tools/recompute_image_checksums.py` - reseals a system or SHDb image
  after any byte edit. Refreshes the per-stream descriptor CRC32 stored
  words (system image only) and the outer header CRC32. This is the tool
  that makes the binary editable.
- `tools/brute_descriptor_checksum.py` - cross-stream CRC/checksum brute
  force. The pass that found the per-descriptor CRC formula now stored in
  `analysis/descriptor_checksum_notes.md`.
- `tools/rebuild_stock_parity_package.py` - copies stock binaries into the
  bumped `opt/` folders.
- `tools/trace_upgrade_checks.py` - decompresses the known system streams,
  searches upgrade/check strings, and traces reader/check neighborhoods.
- `tools/verify_current_package.py` - verifies path shape, embedded stock
  headers, outer header CRCs, zlib descriptors, CRC32/SHA256, byte-for-byte
  parity against `3.0clean`, and optional deep checksum-constant search.
  After any test variant edit, prefer `recompute_image_checksums.py --check`
  for an integrity-only check that does not require stock byte parity.
- `tools/verify_usb_package.py` - compares a copied USB `opt/` tree against
  the local verified `opt/` tree and reports stale/extra files.
- `tools/inspect_usb_package.py` - deep filesystem-level diagnostic for a
  USB drive. Reports filesystem type, label, serial, every file with
  attributes (hidden, system, reparse points, etc.), windows/macos/linux
  metadata, case-sensitivity issues, encoding issues, byte parity. Run
  this any time stock-parity USB testing fails before suspecting binaries.
- `tools/extract_analysis_inputs.py` - writes repeatable extracted chunks for
  Ghidra and CLI reverse-engineering work.
- `tools/ghidra_scripts/ExportIntegrityFocus.java` - Ghidra headless script
  that scans upgrade/integrity strings and exports focused decompiler output.

Research tools kept for controlled experiments:

- `tools/patch_contact_visible_string.py`
- `tools/patch_mturbo_strings.py`
- `tools/patch_mturbo_splash.py`
- `tools/patch_mturbo_splash_minimal_v.py`
- `tools/patch_sysinfo_visible_label.py`
- `tools/patch_settings_system_info.py`
- `tools/mturbo_bin_gui.py`

Running a patch tool intentionally breaks stock parity. Run
`verify_current_package.py` afterward so the diff is explicit before any USB
test.

External tools worth evaluating:

- `binwalk` or `unblob` for carving embedded streams, filesystems, archives,
  and unknown chunks out of the images.
- `Kaitai Struct`, `Construct`, or ImHex pattern files for documenting binary
  structures once and reusing that map instead of rediscovering offsets.
- Ghidra for ARM/VxWorks disassembly and decompiler work when byte maps are not
  enough. Current local install path:
  `<GHIDRA_INSTALL_DIR>`.
- `radare2` plus `r2pipe` for scriptable command-line disassembly and binary
  diffing.
- `crccheck` or `crc` for testing common CRC/checksum variants while looking
  for integrity fields.
- `capstone` for lightweight scripted ARM disassembly from Python.
- `lief` if an extracted chunk turns out to be a normal ELF/PE/Mach-O style
  executable. It is not expected to parse the raw outer `image.bin` directly.

Preferred mapping workflow:

1. Keep `opt` stock-parity and known-good.
2. Generate a repeatable map of outer offsets, zlib streams, splash chunks,
   resource volumes, candidate length fields, and candidate checksum fields.
3. Make one minimal, named test change at a time.
4. Record the exact byte ranges changed and whether the unit accepts the USB.
5. Promote only accepted findings into the active package path.

Useful commands:

```powershell
python -B .\tools\firmware_map.py
python -B .\tools\trace_upgrade_checks.py
python -B .\tools\make_test_package.py stock
python -B .\tools\make_test_package.py system-contact-string
python -B .\tools\make_test_package.py system-splash-blueboot
python -B .\tools\make_test_package.py system-blueboot-bundle
python -B .\tools\make_test_package.py system-larkrom-bundle
python -B .\tools\make_test_package.py system-zlib-recompress-noop
python -B .\tools\make_test_package.py tempfl-byte
python -B .\tools\make_test_package.py shdb-slack-byte
python -B .\tools\make_versioned_package.py 51.80.300.016 50.80.111.013
python -B .\tools\recompute_image_checksums.py opt\TurboSystem_sw\51.80.300.021\image.bin --check
python -B .\tools\recompute_image_checksums.py opt\TurboSHDb\50.80.111.018\image.bin --check
python -B .\tools\snapshot_release.py Project_Blueboot_0.0.x --variant system-blueboot-bundle
python -B .\tools\verify_current_package.py --details --deep
python -B .\tools\verify_usb_package.py F:\
python -B .\tools\inspect_usb_package.py F:\
python -B .\tools\extract_analysis_inputs.py
python -B .\tools\brute_descriptor_checksum.py --write
```

Suggested first system-only integrity probe: `system-zlib-recompress-noop`. It
leaves the inflated application payload unchanged and changes only the main
zlib container bytes. Do not use `system-slack-byte` as a harmless control; the
previous failed offset landed inside the first sync-word boot/configuration
region.

Generated Ghidra focus reports:

- `analysis/ghidra_miniboot_integrity_focus.md`
- `analysis/ghidra_stream1_integrity_focus.md`
- `analysis/descriptor_checksum_notes.md`

The Ghidra project is stored outside the repo at
`<GHIDRA_PROJECT_DIR>/MTurboPlus`.

## Failure Triage

The full step-by-step is in `analysis/usb_triage.md`. Short version:

1. **If stock-parity copy fails on USB**, the binary integrity is not the
   problem. Run `tools/inspect_usb_package.py <USB drive>` to look at the
   filesystem, hidden Windows/macOS metadata, and case sensitivity.
   Reformat USB clean as FAT32 if needed. Then probe the version policy
   with `tools/make_versioned_package.py` -- start at the minimum
   incremental bump (`51.80.300.016` / `50.80.111.013`) and walk up.
2. **If an edited image fails on USB**, run
   `tools/recompute_image_checksums.py <image> --check`. Any `[FIX]` line
   means a CRC layer is stale; rerun with `--write`. The descriptor and
   outer header CRC32s are now both fully understood
   (`analysis/descriptor_checksum_notes.md`).
3. **If local opt/ verifies stock-parity but USB still fails**, inspect
   the USB drive itself; the removable drive can carry stale extras even
   when the local opt/ tree is pristine.

The previously reported failures of `system-slack-byte` and
`system-zlib-recompress-noop` are both explained by the descriptor CRC
layer that is now solved. `make_test_package.py` auto-reseals after every
variant; the next pass of those test variants on the bench is a clean
signal again.
