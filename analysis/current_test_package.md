# Current Test Package

Variant: `system-larkrom-bundle`

replaced all 12 boot splash frames with the LarkROM Blueboot animation:
- frame 00 0x182bbc..0x18d036 (42106 bytes)
- frame 01 0x18d036..0x199c24 (52206 bytes)
- frame 02 0x199c24..0x1a66e8 (51908 bytes)
- frame 03 0x1a66e8..0x1b30ec (51716 bytes)
- frame 04 0x1b30ec..0x1bfc6e (52098 bytes)
- frame 05 0x1bfc6e..0x1cc72c (51902 bytes)
- frame 06 0x1cc72c..0x1d79a4 (45688 bytes)
- frame 07 0x1d79a4..0x1e50b0 (55052 bytes)
- frame 08 0x1e50b0..0x1f1bc2 (51986 bytes)
- frame 09 0x1f1bc2..0x1fea80 (52926 bytes)
- frame 10 0x1fea80..0x20926a (42986 bytes)
- frame 11 0x20926a..0x214edc (48242 bytes)
preview written: analysis\splash_larkrom_preview
fujifilm support contact already present
patched license heading at inflated offsets +0xa2245e
patched contact heading at inflated offsets +0xa224f6
patched system info mini-boot label at inflated offsets +0x8c3982, +0x8ca094
patched license entry heading at inflated offsets +0xa22a94
patched worldwide support number at inflated offsets +0xa2307a
patched product label at inflated offsets +0x9df0d1
patched password reset contact at inflated offsets +0xbd258e
patched patent list title at inflated offsets +0xa13fb3
recompressed stream1 at 0x24bbb5: 4367690 -> 4332003 bytes

Reseal:
- sealed image.bin stream1: 0x224fc950 -> 0x209c6fec
- sealed image.bin outer header: 0x6332d5eb -> 0x7db4d0f6

Diff summary:

```text
system image crc32 stock=3a25b18d current=2fd43665
system image diff bytes=4789999
  diff 0x00000004-0x00000008 len=4
  diff 0x00182bbc-0x00182c53 len=151
  diff 0x00182c54-0x00182c55 len=1
  diff 0x00182c56-0x00182c57 len=1
  diff 0x00182c58-0x00182c59 len=1
  diff 0x00182c5a-0x00182c5b len=1
  diff 0x00182c5c-0x00182c5d len=1
  diff 0x00182c5e-0x00182c61 len=3

SHDb image crc32 stock=e6874a61 current=e6874a61
SHDb image diff bytes=0

tempFL crc32 stock=3da4bd54 current=3da4bd54
tempFL diff bytes=0
```

Reset to stock-parity baseline with:

```powershell
python -B .\tools\make_test_package.py stock
```
