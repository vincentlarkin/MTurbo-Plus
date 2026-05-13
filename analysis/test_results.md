# Test Results

## system-slack-byte

Result: failed on device during the `Reading` / system initialize stage.

Package state:

- Directory versions were bumped.
- System `image.bin` differed from stock by exactly one byte.
- Changed offset: `0x00117322`.
- Change: `00 -> 01`.
- The changed byte was in the longest zero run outside detected zlib streams.
- SHDb `image.bin` and `tempFL.bin` matched stock.
- Main zlib stream and inflated payload still matched stock exactly.

Interpretation:

The old interpretation was too broad. This failure is now explained by a mapped
outer header CRC. System `image.bin` stores a standard CRC32 at offset `0x4`:

- stored value: `0x6332d5eb`
- covered range: `image.bin[0x8:0x24bb9c]`

Offset `0x00117322` sits inside that covered range and inside the first
sync-word-delimited boot/configuration region:

- region: `0x00000030-0x00159660`
- sync word at region start: `55 99 aa 66`
- matching sync words also appear at `0x00159660` and `0x0021d5d8`

So this failure proves that touching that covered boot/configuration range
without recomputing the outer header CRC is invalid. It does not prove that
every byte in the later zlib application payload is covered by the same CRC.

Next better system-only probe: `system-zlib-recompress-noop`. It leaves the
inflated application payload unchanged and changes only the compressed zlib
container. If that passes, we can try a length-preserving payload edit. If it
fails, the gate likely covers compressed stream bytes or higher-level system
image bytes.

## system-zlib-recompress-noop

Result: failed on device with the same system preparation error.

Package state at the time of test:

- Directory versions were bumped.
- SHDb `image.bin` and `tempFL.bin` matched stock.
- System `image.bin` differed only in the main zlib stream at offset
  `0x0024bbb5`.
- The zlib stream kept the original compressed length: `0x42a54a`.
- The inflated payload was byte-identical to stock:
  - payload CRC32: `962aa149`
  - Adler-32: `0fd8b686`
- The compressed stream CRC32 changed from `51adc03e` to `d20c632f`.

Updated interpretation:

That failure is now fully explained by the descriptor CRC layer. The edit
changed bytes in `image[0x24bbb5..0x676104]`, which is inside the range
covered by stream1's descriptor `stored_word` (CRC32 of
`image[0x24bba4..0x676104]`). The 2026-05 brute-force pass solved this
formula:

- stream1 descriptor offset: `0x24bb9c`
- magic: `0xaabb0340`
- stored word: `0x224fc950`
- covered range: `image[0x24bba4 : 0x676104]`
- algorithm: standard CRC32 (zlib polynomial)

The bench package shipped with the *old* `0x224fc950` even though the
covered bytes had changed. So the unit's integrity check was right to
reject it.

Re-test plan:

`make_test_package.py system-zlib-recompress-noop` now auto-reseals after
the patch (use `--no-reseal` only to reproduce this exact broken-integrity
state). The reseal step writes the new stream1 stored_word; the outer
header CRC is unaffected because the edit is after `0x24bb9c`. The next
bench cycle should give a real signal:

- pass: payload bytes are not separately signed; we are free to recompress
  and edit. The "editable binary" path is unblocked.
- fail: there is yet another integrity layer beyond CRC, almost certainly
  a digital signature. In that case continue Ghidra-side: trace the
  function that consumes the descriptor `stored_word` and look for a
  signature/digest verifier upstream.

## stock-parity USB copy (2026-05)

Result: failed on device with the same system preparation error even
though the local `opt/` tree was byte-identical to a previously accepted
stock-parity package.

This is not explained by any of the binary-integrity layers we know
about. The active triage flow is in `analysis/usb_triage.md`. The
filesystem-side probe (`tools/inspect_usb_package.py`) and the
version-policy probe (`tools/make_versioned_package.py`) are the next two
bench tests, in that order.
