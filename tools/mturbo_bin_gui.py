#!/usr/bin/env python3
"""Small GUI for safe MTurbo .bin string edits."""

from __future__ import annotations

import shutil
import string
import tkinter as tk
import zlib
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


KNOWN_TIMER_ZLIB_OFFSET = 0x24BBB5
PRINTABLE = set(bytes(string.printable, "ascii")) - {0x0B, 0x0C}


@dataclass(frozen=True)
class StringEntry:
    key: str
    offset: int
    length: int
    text: str


@dataclass(frozen=True)
class TimerPayload:
    stream_offset: int
    stream_len: int
    payload: bytes


def is_printable_byte(value: int) -> bool:
    return value in PRINTABLE and value not in {0x0A, 0x0D, 0x09}


def scan_ascii(data: bytes, min_len: int) -> list[StringEntry]:
    entries: list[StringEntry] = []
    start: int | None = None
    for idx, value in enumerate(data):
        if is_printable_byte(value):
            if start is None:
                start = idx
            continue
        if start is not None and idx - start >= min_len:
            text = data[start:idx].decode("ascii", errors="replace")
            entries.append(StringEntry(f"plain:{start}", start, idx - start, text))
        start = None
    if start is not None and len(data) - start >= min_len:
        text = data[start:].decode("ascii", errors="replace")
        entries.append(StringEntry(f"plain:{start}", start, len(data) - start, text))
    return entries


def decompress_stream(data: bytes, offset: int) -> tuple[bytes, int]:
    obj = zlib.decompressobj()
    payload = obj.decompress(data[offset:])
    if not obj.eof:
        raise ValueError("zlib stream did not terminate")
    consumed = len(data) - offset - len(obj.unused_data)
    return payload, consumed


def find_timer_payload(data: bytes) -> TimerPayload:
    anchors = [b"3. Enter license key:", b"3. MT KEY MARKER!!!!!"]
    offsets = [KNOWN_TIMER_ZLIB_OFFSET]
    start = 0
    while True:
        found = data.find(b"\x78\x9c", start)
        if found < 0:
            break
        if found not in offsets:
            offsets.append(found)
        start = found + 1

    for offset in offsets:
        try:
            payload, consumed = decompress_stream(data, offset)
        except zlib.error:
            continue
        except ValueError:
            continue
        if any(anchor in payload for anchor in anchors):
            return TimerPayload(offset, consumed, payload)
    raise ValueError("could not find known timer/license zlib payload")


def recompress_to_fit(payload: bytes, limit: int) -> bytes:
    best: bytes | None = None
    strategies = [
        zlib.Z_DEFAULT_STRATEGY,
        zlib.Z_FILTERED,
        zlib.Z_RLE,
        zlib.Z_HUFFMAN_ONLY,
    ]
    for level in range(9, 0, -1):
        for strategy in strategies:
            compressor = zlib.compressobj(level, zlib.DEFLATED, zlib.MAX_WBITS, zlib.DEF_MEM_LEVEL, strategy)
            candidate = compressor.compress(payload) + compressor.flush()
            if best is None or len(candidate) < len(best):
                best = candidate
            if len(candidate) <= limit:
                return candidate
    best_len = len(best) if best is not None else 0
    raise ValueError(f"recompressed zlib payload is too large: best={best_len}, limit={limit}")


class BinStringEditor(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MTurbo Bin String Editor")
        self.geometry("1040x700")
        self.minsize(900, 560)

        self.file_path = tk.StringVar()
        self.mode = tk.StringVar(value="Plain ASCII strings")
        self.min_len = tk.IntVar(value=6)
        self.filter_text = tk.StringVar()
        self.status = tk.StringVar(value="Choose a .bin file, then scan.")
        self.entries: dict[str, StringEntry] = {}
        self.pending: dict[str, str] = {}
        self.timer_payload: TimerPayload | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill=tk.BOTH, expand=True)

        file_row = ttk.Frame(root)
        file_row.pack(fill=tk.X)
        ttk.Label(file_row, text="File").pack(side=tk.LEFT)
        ttk.Entry(file_row, textvariable=self.file_path).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(file_row, text="Browse", command=self.browse).pack(side=tk.LEFT)

        options = ttk.Frame(root)
        options.pack(fill=tk.X, pady=(8, 8))
        ttk.Label(options, text="Mode").pack(side=tk.LEFT)
        ttk.Combobox(
            options,
            textvariable=self.mode,
            state="readonly",
            width=28,
            values=["Plain ASCII strings", "Known timer zlib payload"],
        ).pack(side=tk.LEFT, padx=(6, 14))
        ttk.Label(options, text="Min length").pack(side=tk.LEFT)
        ttk.Spinbox(options, from_=4, to=80, textvariable=self.min_len, width=5).pack(side=tk.LEFT, padx=(6, 14))
        ttk.Label(options, text="Filter").pack(side=tk.LEFT)
        ttk.Entry(options, textvariable=self.filter_text, width=34).pack(side=tk.LEFT, padx=6)
        ttk.Button(options, text="Scan", command=self.scan).pack(side=tk.LEFT, padx=(8, 0))

        main = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main)
        right = ttk.Frame(main, padding=(10, 0, 0, 0))
        main.add(left, weight=3)
        main.add(right, weight=2)

        columns = ("offset", "length", "text")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("offset", text="Offset")
        self.tree.heading("length", text="Len")
        self.tree.heading("text", text="Text")
        self.tree.column("offset", width=120, stretch=False)
        self.tree.column("length", width=60, stretch=False)
        self.tree.column("text", width=520)
        yscroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        ttk.Label(right, text="Original").pack(anchor=tk.W)
        self.original = tk.Text(right, height=7, wrap=tk.WORD)
        self.original.pack(fill=tk.X, pady=(3, 10))
        self.original.configure(state=tk.DISABLED)

        ttk.Label(right, text="Replacement").pack(anchor=tk.W)
        self.replacement = tk.Text(right, height=7, wrap=tk.WORD)
        self.replacement.pack(fill=tk.X, pady=(3, 8))

        self.byte_info = tk.StringVar(value="Select a string.")
        ttk.Label(right, textvariable=self.byte_info).pack(anchor=tk.W)

        button_row = ttk.Frame(right)
        button_row.pack(fill=tk.X, pady=(10, 12))
        ttk.Button(button_row, text="Queue Change", command=self.queue_change).pack(side=tk.LEFT)
        ttk.Button(button_row, text="Clear Queued", command=self.clear_changes).pack(side=tk.LEFT, padx=6)

        save_row = ttk.Frame(right)
        save_row.pack(fill=tk.X)
        ttk.Button(save_row, text="Apply to Copy", command=self.apply_to_copy).pack(side=tk.LEFT)
        ttk.Button(save_row, text="Apply In Place + Backup", command=self.apply_in_place).pack(side=tk.LEFT, padx=6)

        notes = (
            "Rules: replacements must be ASCII and no longer than the original byte length. "
            "Shorter replacements are padded with spaces. Plain mode edits bytes directly. "
            "Timer mode edits the known compressed timer/license payload and recompresses it without changing file size."
        )
        ttk.Label(right, text=notes, wraplength=360).pack(anchor=tk.W, pady=(16, 0))

        ttk.Label(root, textvariable=self.status).pack(fill=tk.X, pady=(8, 0))

    def browse(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Binary files", "*.bin *.BIN"), ("All files", "*.*")])
        if path:
            self.file_path.set(path)

    def scan(self) -> None:
        path = Path(self.file_path.get())
        if not path.is_file():
            messagebox.showerror("No file", "Choose a valid .bin file first.")
            return
        try:
            data = path.read_bytes()
            self.timer_payload = None
            if self.mode.get() == "Known timer zlib payload":
                self.timer_payload = find_timer_payload(data)
                entries = scan_ascii(self.timer_payload.payload, self.min_len.get())
                prefix = f"timer zlib 0x{self.timer_payload.stream_offset:x}"
            else:
                entries = scan_ascii(data, self.min_len.get())
                prefix = "plain file"
        except Exception as exc:
            messagebox.showerror("Scan failed", str(exc))
            return

        needle = self.filter_text.get().lower()
        if needle:
            entries = [entry for entry in entries if needle in entry.text.lower()]

        self.entries = {entry.key: entry for entry in entries}
        self.pending.clear()
        self.tree.delete(*self.tree.get_children())
        for entry in entries:
            offset = f"0x{entry.offset:x}"
            self.tree.insert("", tk.END, iid=entry.key, values=(offset, entry.length, entry.text))
        self.status.set(f"Scanned {prefix}: {len(entries)} strings shown.")
        self.show_entry(None)

    def selected_key(self) -> str | None:
        selected = self.tree.selection()
        return selected[0] if selected else None

    def on_select(self, _event: tk.Event[tk.Widget]) -> None:
        self.show_entry(self.selected_key())

    def show_entry(self, key: str | None) -> None:
        self.original.configure(state=tk.NORMAL)
        self.original.delete("1.0", tk.END)
        self.replacement.delete("1.0", tk.END)
        if key is None or key not in self.entries:
            self.original.configure(state=tk.DISABLED)
            self.byte_info.set("Select a string.")
            return
        entry = self.entries[key]
        replacement = self.pending.get(key, entry.text)
        self.original.insert("1.0", entry.text)
        self.original.configure(state=tk.DISABLED)
        self.replacement.insert("1.0", replacement)
        self.byte_info.set(f"Offset 0x{entry.offset:x}; max {entry.length} ASCII bytes.")

    def queue_change(self) -> None:
        key = self.selected_key()
        if key is None or key not in self.entries:
            messagebox.showerror("No selection", "Select a string first.")
            return
        entry = self.entries[key]
        replacement = self.replacement.get("1.0", "end-1c")
        try:
            raw = replacement.encode("ascii")
        except UnicodeEncodeError:
            messagebox.showerror("Invalid text", "Replacement must be ASCII only.")
            return
        if len(raw) > entry.length:
            messagebox.showerror("Too long", f"Replacement is {len(raw)} bytes; max is {entry.length}.")
            return
        self.pending[key] = replacement
        self.tree.set(key, "text", replacement + (" " * max(0, entry.length - len(raw))))
        self.status.set(f"Queued {len(self.pending)} change(s).")

    def clear_changes(self) -> None:
        self.pending.clear()
        for key, entry in self.entries.items():
            if self.tree.exists(key):
                self.tree.set(key, "text", entry.text)
        self.show_entry(self.selected_key())
        self.status.set("Cleared queued changes.")

    def apply_to_copy(self) -> None:
        source = Path(self.file_path.get())
        if not source.is_file():
            messagebox.showerror("No file", "Choose a valid .bin file first.")
            return
        default = source.with_suffix(source.suffix + ".patched")
        target = filedialog.asksaveasfilename(initialfile=default.name, initialdir=str(source.parent))
        if not target:
            return
        self.apply_changes(source, Path(target), backup=False)

    def apply_in_place(self) -> None:
        source = Path(self.file_path.get())
        if not source.is_file():
            messagebox.showerror("No file", "Choose a valid .bin file first.")
            return
        self.apply_changes(source, source, backup=True)

    def apply_changes(self, source: Path, target: Path, backup: bool) -> None:
        if not self.pending:
            messagebox.showinfo("No changes", "Queue at least one change first.")
            return
        try:
            data = bytearray(source.read_bytes())
            if self.mode.get() == "Known timer zlib payload":
                if self.timer_payload is None:
                    self.timer_payload = find_timer_payload(data)
                payload = bytearray(self.timer_payload.payload)
                for key, replacement in self.pending.items():
                    entry = self.entries[key]
                    raw = replacement.encode("ascii").ljust(entry.length, b" ")
                    payload[entry.offset : entry.offset + entry.length] = raw
                compressed = recompress_to_fit(bytes(payload), self.timer_payload.stream_len)
                start = self.timer_payload.stream_offset
                end = start + self.timer_payload.stream_len
                data[start : start + len(compressed)] = compressed
                data[start + len(compressed) : end] = b"\x00" * (self.timer_payload.stream_len - len(compressed))
            else:
                for key, replacement in self.pending.items():
                    entry = self.entries[key]
                    raw = replacement.encode("ascii").ljust(entry.length, b" ")
                    data[entry.offset : entry.offset + entry.length] = raw

            if backup and target.exists():
                backup_path = target.with_suffix(target.suffix + ".bak")
                if not backup_path.exists():
                    shutil.copy2(target, backup_path)
            target.write_bytes(data)
        except Exception as exc:
            messagebox.showerror("Apply failed", str(exc))
            return

        self.status.set(f"Wrote {len(self.pending)} change(s) to {target}. File size stayed {len(data)} bytes.")
        messagebox.showinfo("Done", f"Wrote {target}")


def main() -> None:
    app = BinStringEditor()
    app.mainloop()


if __name__ == "__main__":
    main()
