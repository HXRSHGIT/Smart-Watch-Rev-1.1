"""Drawing lint: python lint.py   -> wire crossings and net labels per sheet (STYLE_GUIDE.md rules 3 and 18)."""
import re
import sys
from pathlib import Path

PRJ = Path(__file__).resolve().parent.parent
bad = 0
for f in sorted(PRJ.glob("*.kicad_sch")):
    t = f.read_text(encoding="utf-8")
    wires = [tuple(map(float, m)) for m in re.findall(r"\(wire \(pts \(xy ([\d.-]+) ([\d.-]+)\) \(xy ([\d.-]+) ([\d.-]+)\)\)", t)]
    junc = {tuple(map(float, m)) for m in re.findall(r"\(junction \(at ([\d.-]+) ([\d.-]+)\)", t)}
    hs = [w for w in wires if abs(w[1] - w[3]) < 1e-3]
    vs = [w for w in wires if abs(w[0] - w[2]) < 1e-3]
    cross = []
    for h in hs:
        for v in vs:
            x, y = v[0], h[1]
            if min(h[0], h[2]) + 1e-3 < x < max(h[0], h[2]) - 1e-3 and min(v[1], v[3]) + 1e-3 < y < max(v[1], v[3]) - 1e-3 \
                    and (x, y) not in junc:
                cross.append((x, y))
    labels = len(re.findall(r"^\t\(label ", t, re.M))
    print(f"{f.name:28s} wires {len(wires):3d}  crossings {len(cross)}  net labels {labels}")
    for c in cross:
        print("   crossing at", c)
    bad += len(cross)
sys.exit(1 if bad else 0)
