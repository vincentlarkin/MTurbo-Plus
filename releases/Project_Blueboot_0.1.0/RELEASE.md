# Project_Blueboot_0.1.0

Full LarkROM rebrand: Blueboot animation across all 12 splash frames, LarkROM-branded sysinfo/contact/password-reset/patent labels, restored fujifilm support email, simplified support phone.

- Variant: `system-larkrom-bundle`
- Snapshot taken: 2026-05-12 23:36
- Bench result: `fail`
- Bench note: FAILED on bench. Unit reached system preparation, rebooted, then black screen with fans full speed and keyboard lit. Do not install this package.

## Failure Analysis

Do not use this release for further testing. Static comparison found a likely
boot-stage corruption in the splash region:

- Stock and `Project_Blueboot_0.0.2` frame 11 decode consumes `42368` bytes
  and then preserves `5874` bytes of non-frame tail data before the splash
  pointer table.
- This release forced frame 11 to consume the full `48242` byte chunk,
  overwriting that tail.
- The overwritten tail differs from stock in `5751` bytes. Since the splash
  region lives inside the protected mini-boot/configuration area, this is a
  plausible cause for the black-screen/full-fan boot failure.

## Install

Copy the contents of this release's `opt/` folder to a FAT32 USB
root, eject the stick, plug it into the M-Turbo, and run the upgrade
from the unit's update flow.

```powershell
Copy-Item -Recurse -Force releases\Project_Blueboot_0.1.0\opt\* <USB-drive>:\opt\
python -B .\tools\verify_usb_package.py <USB-drive>:\
python -B .\tools\recompute_image_checksums.py <USB-drive>:\opt\TurboSystem_sw\51.80.300.021\image.bin --check
python -B .\tools\recompute_image_checksums.py <USB-drive>:\opt\TurboSHDb\50.80.111.018\image.bin --check
```

All four invocations above should report PASS / [OK].

## Integrity

See `manifest.md` for per-file CRC32 and SHA256.

Local verification passed before this snapshot:

- System descriptor CRCs and outer header CRC all `[OK]`.
- SHDb outer header CRC `[OK]`; SHDb payload is byte-identical to stock.
- `tempFL.bin` is byte-identical to stock.
- Targeted stream1 checks found the restored fujifilm contact, LarkROM contact/license labels, two `Blueboot SW Ver` labels, simplified support phone, rebranded password-reset contact, rebranded patent-list title, and preserved `M-Turbo` exam preset.
- All 12 splash frames decode to 640x480 after patching.

## Reproduce

From a fresh stock-parity tree, this snapshot can be rebuilt with:

```powershell
python -B .\tools\make_test_package.py system-larkrom-bundle
python -B .\tools\snapshot_release.py Project_Blueboot_0.1.0 --variant system-larkrom-bundle
```
