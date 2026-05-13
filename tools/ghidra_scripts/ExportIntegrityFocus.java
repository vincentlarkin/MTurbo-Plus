// Export focused upgrade/integrity xrefs and decompilation from a Ghidra program.
// @category MTurbo

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

public class ExportIntegrityFocus extends GhidraScript {
    private static final String[] NEEDLES = {
        "Upgrade CRC Failure",
        "Upgrade/bootloader image invalid",
        "Primary image invalid",
        "BBootImageHeaderPtr",
        "FpgaBootOK",
        "aUpgradeMgrImpl.cpp",
        "aUpgradeMgrImpl::CheckForUpgrades",
        "aUpgradeReader.cpp",
        "aUpgradeFWReader",
        "aUpgradeSHReader",
        "aUpgradeFWInstaller.cpp",
        "aUpgradeSHInstaller.cpp",
        "IMAGE.BIN",
        "\\opt\\TurboSystem_sw",
        "\\opt\\TurboSHDb",
        "NULL != packHeader",
        "upgradeFile.Open",
        "Verifying CRC",
        "ERROR (CRC)",
        "Checksum mismatch",
        "TURBO_FLASH_UPGRADE_START",
        "SystemUpgradeBuffer",
        "STATE_UPGRADE_STAGED",
    };

    private static final long[] STREAM1_FOCUS_ADDRS = {
        0x2045d4L,
        0x204798L,
        0x204adcL,
        0x204bb0L,
        0x204c80L,
        0x204d60L,
        0x204e54L,
        0x205244L,
        0x205310L,
        0x20553cL,
        0x205924L,
        0x206ca4L,
        0x206d60L,
        0x206cbcL,
        0x206fb4L,
        0x2084c8L,
        0x2086bcL,
        0x2086fcL,
        0x208738L,
        0x208804L,
    };

    private final Map<String, Function> focusFuncs = new TreeMap<String, Function>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            throw new IllegalArgumentException("output markdown path required");
        }

        List<String> lines = new ArrayList<String>();
        String programName = currentProgram.getName();

        lines.add("# Ghidra Integrity Focus");
        lines.add("");
        lines.add("Program: `" + programName + "`");
        lines.add("");
        lines.add("## String Hits And Xrefs");
        lines.add("");

        int hits = collectStringHits(lines);
        if (hits == 0) {
            lines.add("- none");
        }
        lines.add("");

        if (programName.startsWith("system_stream1")) {
            for (long rawAddr : STREAM1_FOCUS_ADDRS) {
                addUniqueFunc(getOrCreateFunction(toAddr(rawAddr)));
            }
        }

        lines.add("## Focus Function Decompilation");
        lines.add("");
        if (focusFuncs.isEmpty()) {
            lines.add("- none");
            lines.add("");
        }
        else {
            DecompInterface ifc = new DecompInterface();
            ifc.openProgram(currentProgram);
            for (Function func : focusFuncs.values()) {
                lines.add("### `" + func.getName() + "` at `" + func.getEntryPoint() + "`");
                lines.add("");
                lines.add("```c");
                lines.add(decompileFunction(ifc, func));
                lines.add("```");
                lines.add("");
            }
        }

        File outFile = new File(args[0]);
        File parent = outFile.getParentFile();
        if (parent != null) {
            parent.mkdirs();
        }
        Files.write(outFile.toPath(), String.join("\n", lines).getBytes(StandardCharsets.UTF_8));
        println("wrote " + args[0]);
    }

    private int collectStringHits(List<String> lines) {
        int hitCount = 0;
        MemoryBlock[] blocks = currentProgram.getMemory().getBlocks();
        for (String needle : NEEDLES) {
            byte[] pattern = needle.getBytes(StandardCharsets.US_ASCII);
            for (MemoryBlock block : blocks) {
                if (!block.isInitialized() || monitor.isCancelled()) {
                    continue;
                }
                byte[] bytes = new byte[(int) block.getSize()];
                try {
                    block.getBytes(block.getStart(), bytes);
                }
                catch (Exception exc) {
                    continue;
                }
                int index = indexOf(bytes, pattern, 0);
                while (index >= 0) {
                    Address addr = block.getStart().add(index);
                    String context = readAsciiContext(block, bytes, index, pattern.length);
                    hitCount++;
                    lines.add("- `" + needle + "` at `" + addr + "`: `" + esc(trim(context, 180)) + "`");
                    List<String> refs = collectRefs(addr, needle.length());
                    if (refs.isEmpty()) {
                        lines.add("  - no Ghidra xrefs");
                    }
                    else {
                        for (String ref : refs) {
                            lines.add("  - " + ref);
                        }
                    }
                    index = indexOf(bytes, pattern, index + 1);
                }
            }
        }
        return hitCount;
    }

    private int indexOf(byte[] haystack, byte[] needle, int start) {
        if (needle.length == 0 || haystack.length < needle.length) {
            return -1;
        }
        for (int i = Math.max(start, 0); i <= haystack.length - needle.length; i++) {
            int j = 0;
            while (j < needle.length && haystack[i + j] == needle[j]) {
                j++;
            }
            if (j == needle.length) {
                return i;
            }
        }
        return -1;
    }

    private String readAsciiContext(MemoryBlock block, byte[] bytes, int index, int needleLen) {
        int start = Math.max(0, index - 48);
        int end = Math.min(bytes.length, index + needleLen + 120);
        StringBuilder sb = new StringBuilder();
        for (int i = start; i < end; i++) {
            int value = bytes[i] & 0xff;
            if (value >= 0x20 && value <= 0x7e) {
                sb.append((char) value);
            }
            else if (value == 0x0a) {
                sb.append("\\n");
            }
            else if (value == 0x0d) {
                sb.append("\\r");
            }
            else {
                sb.append(".");
            }
        }
        return sb.toString();
    }

    private List<String> collectRefs(Address addr, int textLen) {
        List<String> refs = new ArrayList<String>();
        Listing listing = currentProgram.getListing();
        int limit = Math.max(textLen, 1);
        for (int i = 0; i < limit && refs.size() < 24; i++) {
            Address target;
            try {
                target = addr.add(i);
            }
            catch (Exception exc) {
                break;
            }
            ReferenceIterator refIter = currentProgram.getReferenceManager().getReferencesTo(target);
            while (refIter.hasNext() && refs.size() < 24) {
                Reference ref = refIter.next();
                Address src = ref.getFromAddress();
                Function func = listing.getFunctionContaining(src);
                if (func == null) {
                    refs.add("ref from `" + src + "`, function unknown");
                }
                else {
                    addUniqueFunc(func);
                    refs.add("ref from `" + src + "`, function `" + func.getName() + "` at `" + func.getEntryPoint() + "`");
                }
            }
        }
        return refs;
    }

    private Function getOrCreateFunction(Address addr) {
        Listing listing = currentProgram.getListing();
        Function func = listing.getFunctionContaining(addr);
        if (func != null) {
            return func;
        }
        func = listing.getFunctionAt(addr);
        if (func != null) {
            return func;
        }
        try {
            createFunction(addr, "focus_" + addr.toString());
        }
        catch (Exception ignored) {
        }
        return listing.getFunctionContaining(addr);
    }

    private void addUniqueFunc(Function func) {
        if (func == null) {
            return;
        }
        focusFuncs.put(func.getEntryPoint().toString(), func);
    }

    private String decompileFunction(DecompInterface ifc, Function func) {
        try {
            DecompileResults result = ifc.decompileFunction(func, 45, monitor);
            if (result == null || !result.decompileCompleted()) {
                return "/* decompile failed */";
            }
            String code = result.getDecompiledFunction().getC().trim();
            if (code.length() > 14000) {
                return code.substring(0, 14000) + "\n/* truncated */";
            }
            return code;
        }
        catch (Exception exc) {
            return "/* decompile exception: " + exc.toString() + " */";
        }
    }

    private String esc(String text) {
        return text.replace("\r", "\\r").replace("\n", "\\n");
    }

    private String trim(String text, int limit) {
        if (text.length() <= limit) {
            return text;
        }
        return text.substring(0, limit) + "...";
    }
}
