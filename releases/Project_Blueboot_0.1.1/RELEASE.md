# Project_Blueboot_0.1.1

Tail-preserving LarkROM rebrand candidate: all 12 Blueboot splash frames with frame tail bytes preserved, LarkROM-branded stream1 labels, restored fujifilm support email, simplified support phone.

- Variant: `system-larkrom-bundle`
- Snapshot taken: 2026-05-12 23:58
- Bench result: `untested`
- Bench note: Bench pending. Built after 0.1.0 failure analysis; preserves stock frame-11 tail bytes exactly.

## Install

Copy the contents of this release's `opt/` folder to a FAT32 USB
root, eject the stick, plug it into the M-Turbo, and run the upgrade
from the unit's update flow.

```powershell
Copy-Item -Recurse -Force releases\Project_Blueboot_0.1.1\opt\* <USB-drive>:\opt\
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
- Frame 11 decodes with stock consumed length `42368`; the `5874` byte tail
  before the pointer table is byte-identical to stock.
- All other splash frames decode with stock consumed lengths.

## Reproduce

From a fresh stock-parity tree, this snapshot can be rebuilt with:

```powershell
python -B .\tools\make_test_package.py system-larkrom-bundle
python -B .\tools\snapshot_release.py Project_Blueboot_0.1.1 --variant system-larkrom-bundle
```
