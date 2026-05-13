# Project_Blueboot_0.0.1

First end-to-end working modified firmware. Replaces ffss-service@fujifilm.com with MT STRING VISIBLE 2019!!! in the inflated stream1 payload, then reseals stream1 descriptor stored_word + outer header CRC. Bench-confirmed installable on the M-Turbo.

- Variant: `system-contact-string`
- Snapshot taken: 2026-05-12 22:39
- Bench result: `pass`
- Bench note: patched string visible after upgrade; folder bump 51.80.300.021 / 50.80.111.018

## Install

Copy the contents of this release's `opt/` folder to a FAT32 USB
root, eject the stick, plug it into the M-Turbo, and run the upgrade
from the unit's update flow.

```powershell
Copy-Item -Recurse -Force releases\Project_Blueboot_0.0.1\opt\* <USB-drive>:\opt\
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
python -B .\tools\make_test_package.py system-contact-string
python -B .\tools\snapshot_release.py Project_Blueboot_0.0.1 --variant system-contact-string
```
