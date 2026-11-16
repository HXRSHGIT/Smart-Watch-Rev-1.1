"""Remove copper of the given nets within a radius of a point (KiCad 9 python), so a buried pad can be
routed first. Usage: python clear_near.py X Y RADIUS NET[,NET...]
Done by Harsh Thakur."""
import math, os, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.normpath(os.path.join(HERE, "..", "smartwatch.kicad_pcb"))
x0, y0, r = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
nets = set(sys.argv[4].split(","))
b = pcbnew.LoadBoard(BOARD)
keep, n = [], 0
for t in list(b.GetTracks()):
    if t.GetNetname() not in nets:
        continue
    pts = [t.GetPosition()] if t.GetClass() == "PCB_VIA" else [t.GetStart(), t.GetEnd()]
    if any(math.hypot(pcbnew.ToMM(p.x) - x0, pcbnew.ToMM(p.y) - y0) < r for p in pts):
        b.RemoveNative(t); keep.append(t); n += 1
pcbnew.SaveBoard(BOARD, b, True)
print("removed", n, "items of", nets, flush=True)
os._exit(0)
