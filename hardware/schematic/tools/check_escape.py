"""Pin-escape check (run with KiCad 9's python): is there a free lane out of every IC signal pad?

For each signal pad of an IC (QFN/LGA-style pads, not the exposed pad, not BGA balls) it follows
the pad's long axis outward for 0.7 mm and tests the cells against the obstacles of OTHER nets
(clearance 0.105 + half a 0.1 mm track). A pad whose lane is blocked cannot be routed on its own
layer without moving a neighbour. Passing DRC does not guarantee this.

Done by Harsh Thakur.
"""
import importlib.util
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0]]
spec = importlib.util.spec_from_file_location("ro", os.path.join(HERE, "route_own.py"))
ro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ro)
tomm = ro.tomm
LANE = 0.7


def blocked_pads():
    out = []
    total = 0
    for f in ro.board.GetFootprints():
        ref = f.GetReference()
        if not ref.startswith("U"):
            continue
        c = f.GetPosition()
        for p in f.Pads():
            net = p.GetNetname()
            if net in ro.PLANE or net == "" or net.startswith("unconnected") or p.GetNumber() == "":
                continue
            bb = p.GetBoundingBox()
            w, h = tomm(bb.GetWidth()), tomm(bb.GetHeight())
            if min(w, h) > 1.2 or abs(w - h) < 0.05:      # exposed pad / round ball
                continue
            px, py = tomm(p.GetPosition().x), tomm(p.GetPosition().y)
            dx, dy = px - tomm(c.x), py - tomm(c.y)
            if w > h:
                ux, uy, half = (1 if dx > 0 else -1), 0, w / 2
            else:
                ux, uy, half = 0, (1 if dy > 0 else -1), h / 2
            l = 2 if f.IsFlipped() else 0
            code = ro.NETCODE[net]
            ot = ro.G.t[0.1][l]
            total += 1
            ok = True
            for k in range(int(0.02 / ro.RES), int(LANE / ro.RES)):
                x = px + ux * (half + k * ro.RES)
                y = py + uy * (half + k * ro.RES)
                v = ot[ro.cy(y), ro.cx(x)]
                if v not in (0, code):
                    ok = False
                    blocker = ro.NETNAME.get(int(v), "several nets") if v != -1 else "several nets"
                    break
            if not ok:
                # which footprint pad lies on the blocking cell?
                culprit = "?"
                bx, by = x, y
                for f2 in ro.board.GetFootprints():
                    b2 = f2.GetBoundingBox(False)
                    if f2 is not f and tomm(b2.GetLeft()) - 0.2 <= bx <= tomm(b2.GetRight()) + 0.2 and tomm(b2.GetTop()) - 0.2 <= by <= tomm(b2.GetBottom()) + 0.2:
                        culprit = f2.GetReference()
                        break
                out.append((ref, p.GetNumber(), net, culprit))
    return out, total


bad, total = blocked_pads()
print("signal pads checked: %d, boxed in: %d" % (total, len(bad)))
by = {}
for ref, num, net, k in bad:
    by.setdefault(ref, []).append("%s(%s)<-%s" % (num, net[-12:], k))
for ref, v in by.items():
    print(" ", ref, len(v), v[:8])
sys.exit(0 if not bad else 1)
