"""MAX30208 (U4) escape for the two inner centre pads (KiCad 9 python).

Pads 8 (SDA) and 9 (SCL) are the inner pads of the centre column: walled in by the side pads
(0.55 x 0.40 at y 0, +/-0.65) and the outer centre pads. The horizontal channel between two side
pads is 0.25 mm; a 0.09 mm track with 0.10 mm clearance each side needs 0.29 mm. So the six side
pads are trimmed to 0.36 mm tall (vendor land pattern 90-100101 says 0.40; the package land is
smaller than that) which opens the channel to 0.29 mm, and the two escapes are drawn here as
fixed 0.09 mm stubs through the channels towards the +1V8 side (pads 1-3), ending on the 0.05 mm
routing grid so route_v2.py can continue from them.

Done by Harsh Thakur.
"""
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.normpath(os.path.join(HERE, "..", "smartwatch.kicad_pcb"))
mm, tomm = pcbnew.FromMM, pcbnew.ToMM
SIDE_H = 0.36
W = 0.09

board = pcbnew.LoadBoard(BOARD)
u4 = [f for f in board.GetFootprints() if f.GetReference() == "U4"][0]
layer = pcbnew.B_Cu if u4.IsFlipped() else pcbnew.F_Cu
pads = {p.GetNumber(): p for p in u4.Pads() if p.IsOnLayer(layer)}
for n in "123456":
    s = pads[n].GetSize()
    pads[n].SetSize(pcbnew.VECTOR2I(s.x, mm(SIDE_H)))
cx, cy = tomm(u4.GetPosition().x), tomm(u4.GetPosition().y)
side_x = tomm(pads["2"].GetPosition().x) - cx            # -0.60 (the +1V8 side)
ux = -1 if side_x < 0 else 1
for num in ("8", "9"):
    p = pads[num]
    px, py = tomm(p.GetPosition().x), tomm(p.GetPosition().y)
    y = py + (0.075 if py > cy else -0.075)             # centre of the channel between two side pads
    x_end = round((cx + ux * 1.2) / 0.05) * 0.05         # past the side pads, on the 0.05 mm grid
    y_end = round(y / 0.05) * 0.05 + (0.05 if abs(round(y / 0.05) * 0.05 - y) < 1e-6 else 0)
    y_end = round((y + (0.025 if py > cy else -0.025)) / 0.05) * 0.05
    for (x1, y1), (x2, y2) in (((px, y), (x_end, y)), ((x_end, y), (x_end, y_end))):
        if abs(x2 - x1) + abs(y2 - y1) < 1e-6:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        t.SetWidth(mm(W))
        t.SetLayer(layer)
        t.SetNet(p.GetNet())
        t.SetLocked(True)
        board.Add(t)
    print("U4.%s %s: escape stub at y=%.3f to (%.2f, %.2f)" % (num, p.GetNetname(), y, x_end, y_end))
pcbnew.SaveBoard(BOARD, board, True)
print("U4 side pads trimmed to %.2f mm; saved" % SIDE_H)
