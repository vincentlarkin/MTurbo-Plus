# Project Blueboot - Release History

Each subfolder here is a complete, self-contained, bench-installable
firmware package for the M-Turbo. The folder contains an `opt/` tree that
can be copied directly to a FAT32 USB stick to install.

| Version | Variant | Bench result | Notes |
| --- | --- | --- | --- |
| `Project_Blueboot_0.0.1` | `system-contact-string` | PASS | First end-to-end working modified firmware. Replaces `ffss-service@fujifilm.com` with `MT STRING VISIBLE 2019!!!` in the inflated payload, reseals stream1 descriptor + outer header CRC. Confirmed installable. |
| `Project_Blueboot_0.0.2` | `system-blueboot-bundle` | PASS | First firmware to combine an outer-image edit (custom blue wireframe boot splash on frame 0) with an inflated-payload edit (contact string), in a single sealed package. |
| `Project_Blueboot_0.1.0` | `system-larkrom-bundle` | FAIL | Do not install. Bench failure: system preparation rebooted to black screen, full fans, lit keyboard. Static analysis found frame 11 tail bytes overwritten in mini-boot/splash region. |
| `Project_Blueboot_0.1.1` | `system-larkrom-bundle` | UNTESTED | Tail-preserving LarkROM rebrand candidate. Same visible rebrand goal as 0.1.0, but frame 11 keeps its stock `5874` byte tail exactly. Local CRC and frame-tail checks pass; hardware bench result pending. |

## Anatomy of a release folder

```
Project_Blueboot_0.0.x/
  RELEASE.md       human-readable description, install instructions, bench notes
  manifest.md      table of every file with size, CRC32, SHA256
  splash_preview.png  (0.0.2+) preview render of the patched boot splash
  opt/             the actual USB payload tree
    TurboSystem_sw/51.80.300.021/
      image.bin
      eFilmLite/tempFL.bin
    TurboSHDb/50.80.111.018/
      image.bin
```

## Install any release

Replace `<version>` and `<USB-drive>` with the right values:

```powershell
Copy-Item -Recurse -Force releases\<version>\opt\* <USB-drive>:\opt\
python -B .\tools\verify_usb_package.py <USB-drive>:\
python -B .\tools\recompute_image_checksums.py <USB-drive>:\opt\TurboSystem_sw\51.80.300.021\image.bin --check
python -B .\tools\recompute_image_checksums.py <USB-drive>:\opt\TurboSHDb\50.80.111.018\image.bin --check
```

`verify_usb_package.py` will report mismatch on the system `image.bin` for
any non-stock variant -- that's expected; the byte-parity check is against
the active local `opt/` tree, not against stock. The
`recompute_image_checksums.py --check` calls are the ones that must all
report `[OK]`.

Then eject, plug into the M-Turbo, run the upgrade.

## Reproduce any release from scratch

```powershell
python -B .\tools\make_test_package.py <variant>
python -B .\tools\snapshot_release.py Project_Blueboot_<version> --variant <variant>
```

The `make_test_package.py` step auto-reseals integrity layers, so the
output is bench-ready by the time `snapshot_release.py` immortalizes it.

## Versioning

`Project_Blueboot_<major>.<minor>.<patch>`. Bump `patch` for
back-to-back iterations of the same edit set. Bump `minor` when adding a
new visible change category (e.g. splash on top of strings). Bump `major`
when something structural changes (e.g. SHDb edits land, or the integrity
model changes).
