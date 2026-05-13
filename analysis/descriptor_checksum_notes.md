# Descriptor Checksum Notes

Generated during static analysis of the stock-parity system image.

## Confirmed Integrity Layers (system image)

Every modify-then-reseal pass needs to recompute these in this order:

1. **Per-descriptor `stored_word`** -- standard CRC32 over the bytes
   immediately following each descriptor's `stored_word` field, ending at the
   start of the next descriptor (or end-of-file for the last one).
   - stream1 desc `0x24bb9c` -> CRC32 of `image[0x24bba4 : 0x676104]` =
     `0x224fc950`
   - stream2 desc `0x676104` -> CRC32 of `image[0x67610c : 0x677516]` =
     `0x4117dcf1`
   - stream3 desc `0x677516` -> CRC32 of `image[0x67751e : 0x677d42]` =
     `0x99ee1a38`
   - stream4 desc `0x677d42` -> CRC32 of `image[0x677d4a : 0x1323127]` =
     `0x4d472cfc`
   - stream5 desc `0x1323127` -> CRC32 of `image[0x132312f : 0x136cc92]` =
     `0xcdfdf41e`
2. **System outer header CRC** at offset `0x4` -- standard CRC32 over
   `image[0x8 : 0x24bb9c]`. Stored value `0x6332d5eb`.
3. **SHDb outer header CRC** at offset `0x4` -- standard CRC32 over
   `image[0x8 : end]`. Stored value `0x77d4f17f`.
4. zlib's internal Adler-32 trailer is recomputed automatically by Python's
   `zlib` module during recompression; nothing to do manually.

`tools/recompute_image_checksums.py` rewrites layers 1 and 2 in one shot for
the system image, and layer 3 for the SHDb image.

## How The Per-Descriptor CRC Was Found

Codex's earlier sweep checked the obvious shapes (compressed stream, inflated
payload, descriptor with the stored_word byte zeroed) and ruled out standard
CRC32, Adler-32, POSIX cksum, sums/xors, and named crccheck variants. The
shape it didn't try is the one that worked:

> CRC32 of the descriptor block from `desc + 8` (the byte right after
> `stored_word`) all the way to the start of the next descriptor.

That range happens to subsume the descriptor's own `start_field`/`end_field`
words, the compression flag byte, the entire compressed zlib stream
(including its zlib Adler-32 trailer), and any tail data before the next
descriptor. For the last descriptor there is no "next" so the range runs to
the byte before the outer file CRC's covered region ends. This is verified
end-to-end by `tools/brute_descriptor_checksum.py` and reproduced manually
with a one-liner:

```python
import zlib, pathlib
data = pathlib.Path("opt/TurboSystem_sw/51.80.300.021/image.bin").read_bytes()
specs = [
    (0x24BB9C, 0x676104),
    (0x676104, 0x677516),
    (0x677516, 0x677D42),
    (0x677D42, 0x1323127),
    (0x1323127, len(data)),
]
for desc, end in specs:
    stored = int.from_bytes(data[desc + 4 : desc + 8], "little")
    calc = zlib.crc32(data[desc + 8 : end]) & 0xFFFFFFFF
    print(f"desc=0x{desc:x}: stored=0x{stored:08x} calc=0x{calc:08x} {stored==calc}")
```

All five rows print `True` against the stock-parity image.

## Implications For Editing The System Image

With layers 1-3 known, a payload edit pass is now well-defined:

1. Edit bytes anywhere in the system image. Most useful target ranges are
   inside one of the inflated zlib payloads (stream1 has the FW reader
   strings; stream4 has the SHDb verifier strings).
2. If the edit was inside a zlib payload, recompress the payload (any
   length is fine, but if the new compressed length differs the descriptor's
   `start_field`/`end_field`/next-descriptor offsets shift; for the simple
   case keep the recompressed length identical via a stored block tail, as
   `tools/make_test_package.py system-zlib-recompress-noop` already does).
3. Run `tools/recompute_image_checksums.py opt/.../image.bin`. The tool
   rewrites the system descriptor stored words and the outer header CRC in
   place.
4. Sanity check with `tools/verify_current_package.py --details` (it now
   accepts edited binaries as long as both checksum layers agree).
5. Bench test on USB.

The previous bench finding -- `system-zlib-recompress-noop` rejected at the
device -- is most likely explained by step 3 having been skipped on that
test: the outer header CRC was unchanged (the edit was after `0x24bb9c`)
*but* the stream1 descriptor stored_word was not refreshed even though the
compressed stream bytes had changed. With recompute_image_checksums.py we
can rerun that test cleanly and get a real signal.

## Bench-State Reconciliation

The "stock-parity USB still fails" datapoint is **not** explained by these
checksum layers. Stock-parity copies have all CRCs intact by definition.
That failure is therefore a USB-side or version-policy-side issue and is
covered separately by `tools/inspect_usb_package.py` and
`tools/make_versioned_package.py`. See `analysis/usb_triage.md` for the
current diagnostic flow.
