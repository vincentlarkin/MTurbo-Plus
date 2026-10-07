#!/usr/bin/env python3
"""Extract and patch the MTurbo mini-boot splash image."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_IMAGE_GLOB = "opt/TurboSystem_sw/*/image.bin"
SPLASH_POINTER_TABLE_OFFSET = 0x214EDC
SPLASH_FRAME_COUNT = 12
MTURBO_SPLASH_INDEX = 0
WIDTH = 640
HEIGHT = 480
PIXELS = WIDTH * HEIGHT

# The splash payload stores 4-bit palette indices as value,count byte pairs.
# On common 4-bit palettes index 9 is bright blue and 15 is white. If this
# target uses a grayscale palette, index 9 still gives a visibly changed field.
BACKGROUND_INDEX = 9
WIRE_INDEX = 15
DIM_WIRE_INDEX = 14

EGA_PREVIEW_PALETTE = [
    (0, 0, 0),
    (0, 0, 170),
    (0, 170, 0),
    (0, 170, 170),
    (170, 0, 0),
    (170, 0, 170),
    (170, 85, 0),
    (170, 170, 170),
    (85, 85, 85),
    (85, 85, 255),
    (85, 255, 85),
    (85, 255, 255),
    (255, 85, 85),
    (255, 85, 255),
    (255, 255, 85),
    (255, 255, 255),
]

GRAYSCALE_PREVIEW_PALETTE = [(i * 17, i * 17, i * 17) for i in range(16)]

BLOCK_FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
}


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def resolve_single(glob_pattern: str, label: str) -> Path:
    matches = sorted(ROOT.glob(glob_pattern))
    if len(matches) != 1:
        fail(f"expected one {label}, found {len(matches)} using {glob_pattern}")
    return matches[0]


def splash_pointers(data: bytes) -> list[int]:
    ptrs = [
        int.from_bytes(data[SPLASH_POINTER_TABLE_OFFSET + i * 4 : SPLASH_POINTER_TABLE_OFFSET + i * 4 + 4], "little")
        for i in range(SPLASH_FRAME_COUNT)
    ]
    if any(ptr <= 0 or ptr >= len(data) for ptr in ptrs):
        fail("splash pointer table contains out-of-range offsets")
    if ptrs != sorted(ptrs):
        fail("splash pointer table is not sorted")
    return ptrs


def decode_rle_with_consumed(chunk: bytes) -> tuple[bytearray, int]:
    out = bytearray()
    for idx in range(0, len(chunk) - 1, 2):
        value = chunk[idx] & 0x0F
        count = chunk[idx + 1]
        if count:
            out.extend([value] * count)
        if len(out) >= PIXELS:
            break
    if len(out) != PIXELS:
        fail(f"decoded splash length was {len(out)}, expected {PIXELS}")
    return out, idx + 2


def decode_rle(chunk: bytes) -> bytearray:
    out, _ = decode_rle_with_consumed(chunk)
    return out


def encode_rle_pairs(indices: bytes | bytearray) -> list[list[int]]:
    if len(indices) != PIXELS:
        fail(f"cannot encode {len(indices)} pixels, expected {PIXELS}")
    pairs: list[list[int]] = []
    current = indices[0] & 0x0F
    run = 0
    for raw in indices:
        value = raw & 0x0F
        if value == current and run < 255:
            run += 1
            continue
        pairs.append([current, run])
        current = value
        run = 1
    pairs.append([current, run])
    return pairs


def pairs_to_bytes(pairs: list[list[int]]) -> bytes:
    encoded = bytearray()
    for value, count in pairs:
        encoded.extend([value & 0x0F, count])
    return bytes(encoded)


def encode_rle_exact(indices: bytes | bytearray, target_len: int) -> bytes:
    if target_len % 2:
        fail(f"target RLE length must be even, got {target_len}")
    pairs = encode_rle_pairs(indices)
    target_pairs = target_len // 2
    if len(pairs) > target_pairs:
        fail(f"patched splash RLE is too large: {len(pairs) * 2} > {target_len}")

    extra = target_pairs - len(pairs)
    expanded: list[list[int]] = []
    for value, count in pairs:
        pieces = 1 + min(extra, count - 1)
        base = count // pieces
        remainder = count % pieces
        for idx in range(pieces):
            expanded.append([value, base + (1 if idx < remainder else 0)])
        extra -= pieces - 1
    if extra:
        fail(f"could not expand RLE to exact chunk size; {extra} pairs short")
    return pairs_to_bytes(expanded)


def render(indices: bytes | bytearray, palette: list[tuple[int, int, int]]) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = img.load()
    for y in range(HEIGHT):
        row = indices[y * WIDTH : (y + 1) * WIDTH]
        for x, value in enumerate(row):
            pixels[x, y] = palette[value & 0x0F]
    return img


def draw_rect(indices: bytearray, x: int, y: int, w: int, h: int, value: int) -> None:
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(WIDTH, x + w)
    y1 = min(HEIGHT, y + h)
    for yy in range(y0, y1):
        row = yy * WIDTH
        for xx in range(x0, x1):
            indices[row + xx] = value & 0x0F


def block_text_width(text: str, scale: int) -> int:
    width = 0
    for ch in text.upper():
        if ch == " ":
            width += 4 * scale
            continue
        pattern = BLOCK_FONT.get(ch)
        if pattern is None:
            width += 4 * scale
            continue
        width += (len(pattern[0]) + 1) * scale
    return max(0, width - scale)


def draw_block_text(indices: bytearray, text: str, x: int, y: int, scale: int, value: int) -> None:
    cursor = x
    for ch in text.upper():
        if ch == " ":
            cursor += 4 * scale
            continue
        pattern = BLOCK_FONT.get(ch)
        if pattern is None:
            cursor += 4 * scale
            continue
        for row, bits in enumerate(pattern):
            for col, bit in enumerate(bits):
                if bit == "1":
                    draw_rect(indices, cursor + col * scale, y + row * scale, scale, scale, value)
        cursor += (len(pattern[0]) + 1) * scale


def draw_centered_block_text(indices: bytearray, text: str, y: int, scale: int, value: int) -> None:
    draw_block_text(indices, text, (WIDTH - block_text_width(text, scale)) // 2, y, scale, value)


def component_bbox(indices: bytes | bytearray) -> tuple[int, int, int, int]:
    # Manual crop excludes the right-side logo/product text and bottom copyright,
    # keeping the M-Turbo line drawing from the original splash.
    minx, miny, maxx, maxy = WIDTH, HEIGHT, 0, 0
    for y in range(65, 365):
        for x in range(0, 455):
            value = indices[y * WIDTH + x]
            if value >= 7:
                minx = min(minx, x)
                miny = min(miny, y)
                maxx = max(maxx, x)
                maxy = max(maxy, y)
    if minx > maxx or miny > maxy:
        fail("could not isolate original M-Turbo wireframe")
    return minx, miny, maxx, maxy


def build_blue_wireframe(original: bytes | bytearray) -> bytearray:
    minx, miny, maxx, maxy = component_bbox(original)
    source_w = maxx - minx + 1
    source_h = maxy - miny + 1
    dest_x = (WIDTH - source_w) // 2
    dest_y = (HEIGHT - source_h) // 2

    result = bytearray([BACKGROUND_INDEX] * PIXELS)
    for y in range(source_h):
        for x in range(source_w):
            source_value = original[(miny + y) * WIDTH + minx + x]
            if source_value >= 7:
                result[(dest_y + y) * WIDTH + dest_x + x] = WIRE_INDEX if source_value >= 10 else DIM_WIRE_INDEX

    # Convert a small text marker back into index pixels for an extra visible cue.
    marker = Image.new("1", (WIDTH, HEIGHT), 0)
    marker_draw = ImageDraw.Draw(marker)
    marker_draw.text((216, 418), "MTURBO+ BLUE BOOT", fill=1)
    marker_pixels = marker.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if marker_pixels[x, y]:
                result[y * WIDTH + x] = WIRE_INDEX
    return result


def build_larkrom_blueboot(original: bytes | bytearray, frame_index: int = 0) -> bytearray:
    minx, miny, maxx, maxy = component_bbox(original)
    source_w = maxx - minx + 1
    source_h = maxy - miny + 1
    dest_x = (WIDTH - source_w) // 2
    dest_y = max(84, min(110, ((HEIGHT - source_h) // 2) - 10))

    result = bytearray([BACKGROUND_INDEX] * PIXELS)
    for y in range(source_h):
        for x in range(source_w):
            source_value = original[(miny + y) * WIDTH + minx + x]
            if source_value >= 7:
                result[(dest_y + y) * WIDTH + dest_x + x] = WIRE_INDEX if source_value >= 10 else DIM_WIRE_INDEX

    draw_centered_block_text(result, "BLUEBOOT", 28, 5, WIRE_INDEX)
    draw_centered_block_text(result, "LARKROM SYSTEM OS", 404, 3, WIRE_INDEX)
    draw_rect(result, 118, 86, 404, 3, DIM_WIRE_INDEX)
    draw_rect(result, 118, 382, 404, 3, DIM_WIRE_INDEX)

    dot_count = SPLASH_FRAME_COUNT
    dot_w = 12
    gap = 6
    start_x = (WIDTH - dot_count * dot_w - (dot_count - 1) * gap) // 2
    for idx in range(dot_count):
        value = WIRE_INDEX if idx <= frame_index else DIM_WIRE_INDEX
        draw_rect(result, start_x + idx * (dot_w + gap), 452, dot_w, 6, value)
    return result


def looks_patched(indices: bytes | bytearray) -> bool:
    counts = Counter(indices)
    return (
        counts[BACKGROUND_INDEX] > 280_000
        and counts[WIRE_INDEX] > 5_000
        and counts[DIM_WIRE_INDEX] > 2_000
        and counts[1] < 10_000
    )


def write_previews(outdir: Path, original: bytes | bytearray, patched: bytes | bytearray) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    render(original, GRAYSCALE_PREVIEW_PALETTE).save(outdir / "original_mturbo_splash_gray.png")
    render(original, EGA_PREVIEW_PALETTE).save(outdir / "original_mturbo_splash_ega.png")
    render(patched, EGA_PREVIEW_PALETTE).save(outdir / "patched_mturbo_blue_wireframe.png")


def extract_all_frames(image_path: Path, outdir: Path) -> None:
    data = image_path.read_bytes()
    ptrs = splash_pointers(data)
    outdir.mkdir(parents=True, exist_ok=True)
    rows: list[Image.Image] = []
    # Reports may be committed; keep local account and directory names out.
    resolved_image = image_path.resolve()
    public_image_path = (
        resolved_image.relative_to(ROOT).as_posix()
        if resolved_image.is_relative_to(ROOT)
        else resolved_image.name
    )
    summary: list[str] = [
        f"image={public_image_path}",
        f"pointer_table=0x{SPLASH_POINTER_TABLE_OFFSET:x}",
    ]

    for index, start in enumerate(ptrs):
        end = ptrs[index + 1] if index + 1 < len(ptrs) else SPLASH_POINTER_TABLE_OFFSET
        chunk = data[start:end]
        try:
            indices, consumed = decode_rle_with_consumed(chunk)
        except SystemExit:
            summary.append(f"frame[{index:02d}] 0x{start:x}-0x{end:x} bytes={len(chunk)} decode=FAILED")
            continue

        ega = render(indices, EGA_PREVIEW_PALETTE)
        gray = render(indices, GRAYSCALE_PREVIEW_PALETTE)
        ega_path = outdir / f"frame_{index:02d}_ega.png"
        gray_path = outdir / f"frame_{index:02d}_gray.png"
        ega.save(ega_path)
        gray.save(gray_path)
        counts = Counter(indices).most_common(5)
        rest_nonzero = sum(1 for value in chunk[consumed:] if value)
        summary.append(
            f"frame[{index:02d}] 0x{start:x}-0x{end:x} bytes={len(chunk)} "
            f"consumed={consumed} rest_nonzero={rest_nonzero} top={counts}"
        )

        thumb = ega.resize((160, 120))
        rows.append(thumb)

    if rows:
        sheet = Image.new("RGB", (160 * 4, 120 * ((len(rows) + 3) // 4)), (0, 0, 0))
        for index, thumb in enumerate(rows):
            sheet.paste(thumb, ((index % 4) * 160, (index // 4) * 120))
        sheet.save(outdir / "contact_sheet_ega.png")

    summary_path = outdir / "summary.txt"
    summary_path.write_text("\n".join(summary) + "\n", encoding="ascii", errors="backslashreplace")
    print(f"extracted {len(rows)} splash frame previews: {outdir.resolve()}")
    print(f"summary written: {summary_path.resolve()}")


def patch_image(image_path: Path, dry_run: bool, extract_only: bool, outdir: Path) -> None:
    data = bytearray(image_path.read_bytes())
    ptrs = splash_pointers(data)
    start = ptrs[MTURBO_SPLASH_INDEX]
    end = ptrs[MTURBO_SPLASH_INDEX + 1]
    chunk = bytes(data[start:end])
    original, consumed = decode_rle_with_consumed(chunk)
    if looks_patched(original):
        outdir.mkdir(parents=True, exist_ok=True)
        render(original, EGA_PREVIEW_PALETTE).save(outdir / "patched_mturbo_blue_wireframe.png")
        print(f"extracted patched preview: {(outdir / 'patched_mturbo_blue_wireframe.png').resolve()}")
        print(f"M-Turbo splash chunk: 0x{start:x}-0x{end:x} ({len(chunk)} bytes)")
        print(f"decoded frame consumes {consumed} of {len(chunk)} bytes")
        print(f"patched most-common indices: {Counter(original).most_common(5)}")
        if consumed == len(chunk):
            print("splash already patched")
            return
        target = encode_rle_exact(original, len(chunk))
        if extract_only:
            print("extract only; compact patched RLE not rewritten")
            return
        if dry_run:
            print("dry run only; compact patched RLE not rewritten")
            return
        data[start:end] = target
        image_path.write_bytes(data)
        print(f"repacked patched splash to exact chunk length: {image_path}")
        return

    patched_indices = build_blue_wireframe(original)
    patched_chunk = encode_rle_exact(patched_indices, len(chunk))

    write_previews(outdir, original, patched_indices)
    print(f"extracted previews: {outdir.resolve()}")
    print(f"M-Turbo splash chunk: 0x{start:x}-0x{end:x} ({len(chunk)} bytes)")
    print(f"patched RLE size: {len(patched_chunk)} bytes")
    print(f"original most-common indices: {Counter(original).most_common(5)}")
    print(f"patched most-common indices: {Counter(patched_indices).most_common(5)}")

    target = patched_chunk
    if chunk == target:
        print("splash already patched")
        return
    if extract_only:
        print("extract only; image not written")
        return
    if dry_run:
        print("dry run only; image not written")
        return
    data[start:end] = target
    image_path.write_bytes(data)
    print(f"patched image written: {image_path}")


def patch_larkrom_all_frames(image_path: Path, dry_run: bool, extract_only: bool, outdir: Path) -> None:
    data = bytearray(image_path.read_bytes())
    ptrs = splash_pointers(data)
    base_start = ptrs[0]
    base_end = ptrs[1]
    base_original, _ = decode_rle_with_consumed(bytes(data[base_start:base_end]))
    outdir.mkdir(parents=True, exist_ok=True)
    thumbs: list[Image.Image] = []
    first_preview: Image.Image | None = None
    changed = False
    summary: list[str] = []

    for index, start in enumerate(ptrs):
        end = ptrs[index + 1] if index + 1 < len(ptrs) else SPLASH_POINTER_TABLE_OFFSET
        chunk = bytes(data[start:end])
        original, consumed = decode_rle_with_consumed(chunk)
        patched_indices = build_larkrom_blueboot(base_original, index)
        patched_chunk = encode_rle_exact(patched_indices, consumed) + chunk[consumed:]
        preview = render(patched_indices, EGA_PREVIEW_PALETTE)
        preview.save(outdir / f"larkrom_frame_{index:02d}_ega.png")
        if first_preview is None:
            first_preview = preview
        thumbs.append(preview.resize((160, 120)))
        if patched_chunk != chunk:
            changed = True
        data[start:end] = patched_chunk
        summary.append(
            f"frame[{index:02d}] 0x{start:x}-0x{end:x} bytes={len(chunk)} "
            f"consumed={consumed} patched={len(patched_chunk)}"
        )

    if thumbs:
        sheet = Image.new("RGB", (160 * 4, 120 * ((len(thumbs) + 3) // 4)), (0, 0, 0))
        for index, thumb in enumerate(thumbs):
            sheet.paste(thumb, ((index % 4) * 160, (index // 4) * 120))
        sheet.save(outdir / "larkrom_contact_sheet_ega.png")
    if first_preview is not None:
        first_preview.save(outdir / "larkrom_splash_preview.png")

    (outdir / "larkrom_summary.txt").write_text("\n".join(summary) + "\n", encoding="ascii")
    print(f"wrote LarkROM splash previews: {outdir.resolve()}")

    if not changed:
        print("all splash frames already match the LarkROM Blueboot variant")
        return
    if extract_only:
        print("extract only; image not written")
        return
    if dry_run:
        print("dry run only; image not written")
        return
    image_path.write_bytes(data)
    print(f"patched all {SPLASH_FRAME_COUNT} splash frames: {image_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, default=None)
    parser.add_argument("--outdir", type=Path, default=ROOT / "analysis" / "splash_candidates")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--extract-only", action="store_true")
    parser.add_argument("--extract-all", action="store_true")
    parser.add_argument("--larkrom-all-frames", action="store_true")
    args = parser.parse_args()

    image_path = (args.image or resolve_single(SYSTEM_IMAGE_GLOB, "system image")).resolve()
    if args.extract_all:
        extract_all_frames(image_path, args.outdir)
        return
    if args.larkrom_all_frames:
        patch_larkrom_all_frames(image_path, args.dry_run, args.extract_only, args.outdir)
        return
    patch_image(image_path, args.dry_run, args.extract_only, args.outdir)


if __name__ == "__main__":
    main()
