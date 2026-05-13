# Project_Blueboot_0.0.2

Blueboot bundle: custom blue wireframe boot splash (frame 0) + contact string visible-edit. First firmware to combine outer-image (splash) and inflated-payload (contact string) edits in a single sealed package.

- Variant: `system-blueboot-bundle`
- Snapshot taken: 2026-05-12 22:42
- Bench result: `pass`
- Bench note: bench-confirmed installable; blue wireframe splash visible at boot, patched contact string visible in unit's about screen

## Install

Copy the contents of this release's `opt/` folder to a FAT32 USB
root, eject the stick, plug it into the M-Turbo, and run the upgrade
from the unit's update flow.

```powershell
Copy-Item -Recurse -Force releases\Project_Blueboot_0.0.2\opt\* <USB-drive>:\opt\
python -B .\tools\verify_usb_package.py <USB-drive>:\
python -B .\tools\recompute_image_checksums.py <USB-drive>:\opt\TurboSystem_sw\51.80.300.021\image.bin --check
python -B .\tools\recompute_image_checksums.py <USB-drive>:\opt\TurboSHDb\50.80.111.018\image.bin --check
```

All four invocations above should report PASS / [OK].

## Integrity

See `manifest.md` for per-file CRC32 and SHA256.

## Reproduce

From a fresh stock-parity tree, this snapshot can be rebuilt with:

```powershell
python -B .\tools\make_test_package.py system-blueboot-bundle
python -B .\tools\snapshot_release.py Project_Blueboot_0.0.2 --variant system-blueboot-bundle
```
