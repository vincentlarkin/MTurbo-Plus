"""Length check for SYSINFO_REPLACEMENTS without shell-quoting headaches."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.patch_mturbo_strings import SYSINFO_REPLACEMENTS, TIMER_REPLACEMENTS

print("SYSINFO_REPLACEMENTS:")
bad = 0
for old, new in SYSINFO_REPLACEMENTS:
    ok = len(old) == len(new)
    if not ok:
        bad += 1
    flag = "OK" if ok else "BAD"
    print(f"  {len(old):2d} vs {len(new):2d}  {flag:3s}  {old.decode():<26}  ->  {new.decode()}")
print()
print("TIMER_REPLACEMENTS (existing):")
for old, new in TIMER_REPLACEMENTS:
    ok = len(old) == len(new)
    if not ok:
        bad += 1
    flag = "OK" if ok else "BAD"
    print(f"  {len(old):2d} vs {len(new):2d}  {flag:3s}  {old.decode():<32}  ->  {new.decode()}")
print()
print(f"bad pairs: {bad}")
