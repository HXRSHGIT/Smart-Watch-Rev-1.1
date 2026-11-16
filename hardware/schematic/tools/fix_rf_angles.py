"""Redraw the VSS_PA star and the C9 ground-tie stub with 45 degree corners (KiCad 9 python).

route_critical.py drew them with a few off-angle segments (check_routes.py: "odd angle").
This removes those tracks and vias and puts back the same connections:
  U1 pin 32 -> NT1 pad 2 (top layer), C6 pad 2 -> via north of C6 -> In2 -> via east of NT1 -> NT1 pad 2,
  C9 pad 2 -> NT2 pad 2.
Works on the current board file (no git reset), so it can run after other routing.

Done by Harsh Thakur.
"""
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.normpath(os.path.join(HERE, "..", "smartwatch.kicad_pcb"))
board = pcbnew.LoadBoard(BOARD)
mm = pcbnew.FromMM
F, IN2 = pcbnew.F_Cu, pcbnew.In2_Cu
W = 0.12

KEEP = []      # removed items must stay referenced: freeing them crashes KiCad's Python (segfault)
for t in list(board.GetTracks()):
    if t.GetNetname() in ("/mcu/VSS_PA", "Net-(C9-Pad2)"):
        board.RemoveNative(t)
        KEEP.append(t)


def pad(ref, num):
    for f in board.GetFootprints():            # (FindFootprintByReference misbehaves after Remove)
        if f.GetReference() == ref:
            for p in f.Pads():
                if p.GetNumber() == str(num):
                    return pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)


def trk(net, layer, pts):
    ni = board.FindNet(net)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if (x1, y1) == (x2, y2):
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        t.SetWidth(mm(W))
        t.SetLayer(layer)
        t.SetNet(ni)
        t.SetLocked(True)
        board.Add(t)


def via(net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetWidth(mm(0.45))
    v.SetDrill(mm(0.20))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(board.FindNet(net))
    v.SetLocked(True)
    board.Add(v)


n = "/mcu/VSS_PA"
xn, yn = pad("NT1", 2)
x62, y62 = pad("C6", 2)
vN = (x62, 9.45)
vS = (8.22, yn)
trk(n, F, [(10.45, 11.65), (8.50, 11.65), (8.50 - (yn - 11.65), yn), (xn, yn)])
trk(n, F, [(x62, y62), vN])
via(n, *vN)
trk(n, IN2, [vN, (vS[0], vN[1]), vS])
via(n, *vS)
x9, y9 = pad("C9", 2)
xt, yt = pad("NT2", 2)
d = xt - x9
trk("Net-(C9-Pad2)", F, [(x9, y9), (x9, yt - d), (xt, yt)])
pcbnew.SaveBoard(BOARD, board, True)
print("redrawn: VSS_PA star and C9 tie with 45 degree corners", flush=True)
os._exit(0)        # skip interpreter teardown (the removed SWIG objects crash it)
