"""Route quality report (run with KiCad 9's python). Reads smartwatch.kicad_pcb, changes nothing.

Rules (from the learned style of the existing boards and JLCPCB's limits):
  - angles 0 / 45 / 90 degrees only
  - no track under 0.09 mm
  - signals: at most 2 vias per net; none on the crystal nets and the RF chain
  - no dead-end stubs (a track end must meet a pad, a via or another track of its net)
  - no tracks inside the antenna clearance except the RF feed
Prints a table and a PASS / FAIL line; exits 1 on FAIL.

Done by Harsh Thakur.
"""
import collections
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.normpath(os.path.join(HERE, "..", "smartwatch.kicad_pcb"))
b = pcbnew.LoadBoard(BOARD)
mm = pcbnew.ToMM
NO_VIA = {"Net-(U1A-XC1)", "Net-(U1A-XC2)", "Net-(U1A-P1.00{slash}XL1)", "Net-(U1A-P1.01{slash}XL2)",
          "/mcu/RF_ANT", "Net-(C6-Pad1)", "Net-(C9-Pad1)", "Net-(C11-Pad1)", "Net-(C14-Pad1)", "Net-(AE1-FEED)"}
PLANES = {"GND", "+1V8"}
ANT = (0.0, 0.0, 6.5, 6.5)

tracks = [t for t in b.GetTracks() if t.GetClass() != "PCB_VIA"]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
bad = collections.defaultdict(list)
length = collections.Counter()
nvia = collections.Counter(v.GetNetname() for v in vias)
ends = collections.defaultdict(list)

for t in tracks:
    s, e = t.GetStart(), t.GetEnd()
    x1, y1, x2, y2 = mm(s.x), mm(s.y), mm(e.x), mm(e.y)
    L = math.hypot(x2 - x1, y2 - y1)
    n = t.GetNetname()
    length[n] += L
    if mm(t.GetWidth()) < 0.0899:
        bad["width<0.09"].append((n, round(x1, 2), round(y1, 2), round(mm(t.GetWidth()), 3)))
    if L > 0.06:
        ang = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 45
        if min(ang, 45 - ang) > 0.8:
            bad["odd angle"].append((n, round(x1, 2), round(y1, 2), round(ang, 1)))
    ends[n] += [(x1, y1, t.GetLayer()), (x2, y2, t.GetLayer())]
    if ANT[0] < x1 < ANT[2] and ANT[1] < y1 < ANT[3] and n != "Net-(AE1-FEED)" and not n.startswith("Net-(C14") and n != "Net-(C11-Pad1)":
        bad["track in antenna clearance"].append((n, round(x1, 2), round(y1, 2)))

# dead ends
pads = []
for f in b.GetFootprints():
    for p in f.Pads():
        pads.append((p.GetNetname(), p.GetEffectiveShape(pcbnew.F_Cu), p))
for n, pts in ends.items():
    cnt = collections.Counter((round(x, 3), round(y, 3), l) for x, y, l in pts)
    for (x, y, l), c in cnt.items():
        if c > 1:
            continue
        pt = pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
        hit = any(pn == n and sh.Collide(pt, 1) for pn, sh, p in pads)
        hit = hit or any(v.GetNetname() == n and math.hypot(mm(v.GetPosition().x) - x, mm(v.GetPosition().y) - y) < 0.25 for v in vias)
        hit = hit or any(t2.GetNetname() == n and t2.GetLayer() == l and t2.HitTest(pt, 2000) for t2 in tracks
                         if not (abs(mm(t2.GetStart().x) - x) < 1e-3 and abs(mm(t2.GetStart().y) - y) < 1e-3)
                         and not (abs(mm(t2.GetEnd().x) - x) < 1e-3 and abs(mm(t2.GetEnd().y) - y) < 1e-3))
        if not hit:
            bad["dead end"].append((n, round(x, 2), round(y, 2)))

for n, c in nvia.items():
    if n in NO_VIA:
        bad["via on no-via net"].append((n, c))
    elif n not in PLANES and c > 2:
        bad[">2 vias"].append((n, c))

print("%-36s %8s %5s" % ("net", "mm", "vias"))
for n, L in sorted(length.items(), key=lambda kv: -kv[1])[:14]:
    print("%-36s %8.1f %5d" % (n[-36:], L, nvia.get(n, 0)))
print("tracks %d, vias %d, total length %.0f mm" % (len(tracks), len(vias), sum(length.values())))
ok = True
for k, v in bad.items():
    ok = False
    print("FAIL %-26s %3d  e.g. %s" % (k, len(v), v[:3]))
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
