"""Critical routing for the 34 x 23 mm board, in groups (run with KiCad 9's python).

Usage:  python route_critical.py [--groups rf,xtal,...] [--keep]

Starts from the committed placement (git HEAD's smartwatch.kicad_pcb) so the run is
repeatable, applies the small placement tweaks below, adds the tracks and vias of each
group, locks them (Freerouting treats locked items as fixed) and saves with
SaveBoard(..., True) so smartwatch.kicad_pro (JLCPCB rules) is not overwritten.
--keep starts from the current board file instead of git HEAD (adds to existing work).

Done by Harsh Thakur.
"""
import os
import subprocess
import sys
import tempfile

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.normpath(os.path.join(HERE, "..", "smartwatch.kicad_pcb"))

# 50 ohm microstrip width on F.Cu over L2 for JLC04081H-3313. My own calculation
# (docs: hardware/JLCPCB_DESIGN_RULES.md 1a), NOT yet JLCPCB's figure: change here only.
RF_W = 0.17
SIG_W = 0.12          # ordinary short signals
PWR_W = 0.30          # power class (matches the project's power net class)
VIA_D, VIA_H = 0.45, 0.20

mm = pcbnew.FromMM
F, IN1, IN2, B = pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu


def load():
    if "--keep" in sys.argv:
        return pcbnew.LoadBoard(BOARD)
    rel = "hardware/schematic/smartwatch.kicad_pcb"
    top = subprocess.check_output(["git", "-C", HERE, "rev-parse", "--show-toplevel"], text=True).strip()
    data = subprocess.check_output(["git", "-C", top, "show", "HEAD:" + rel])
    tmp = os.path.join(tempfile.mkdtemp(), "smartwatch.kicad_pcb")
    open(tmp, "wb").write(data)
    return pcbnew.LoadBoard(tmp)


board = load()


def fp(ref):
    f = board.FindFootprintByReference(ref)
    assert f, ref
    return f


def pad(ref, num):
    for p in fp(ref).Pads():
        if p.GetNumber() == str(num):
            return p
    raise KeyError((ref, num))


def xy(ref, num):
    p = pad(ref, num).GetPosition()
    return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)


def net_of(ref, num):
    return pad(ref, num).GetNetname()


def trk(net, layer, w, pts):
    """Polyline of tracks. pts: list of (x, y) in mm or ('ref', pad) tuples."""
    pts = [xy(*p) if isinstance(p[0], str) else p for p in pts]
    ni = board.FindNet(net)
    assert ni, "net not found: " + net
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if (x1, y1) == (x2, y2):
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        t.SetWidth(mm(w))
        t.SetLayer(layer)
        t.SetNet(ni)
        t.SetLocked(True)
        board.Add(t)


def via(net, x, y, d=VIA_D, h=VIA_H):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetWidth(mm(d))
    v.SetDrill(mm(h))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(board.FindNet(net))
    v.SetLocked(True)
    board.Add(v)


def gnd_via(ref, num, dx, dy, w=SIG_W):
    """Ground via at an offset from a ground pad, joined to the pad by a short track."""
    x, y = xy(ref, num)
    assert net_of(ref, num) == "GND", (ref, num, net_of(ref, num))
    trk("GND", F, w, [(x, y), (x + dx, y + dy)])
    via("GND", x + dx, y + dy)


def move(ref, x, y):
    fp(ref).SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))


def rotate(ref, deg):
    f = fp(ref)
    f.SetOrientationDegrees(f.GetOrientationDegrees() + deg)


def group_rf():
    # C14 (tee shunt): rotate 180 so its RF pad faces the line and its ground pad faces away
    rotate("C14", 180)
    move("C5", 8.76, 12.54)   # makes room for the VSS_PA via east of NT1
    move("C12", 9.54, 12.68)
    n_rf = "/mcu/RF_ANT"
    # nRF54L15 pin 31 -> L2 -> C6 node -> L3 -> C9 node -> L4 (all on y = 11.2)
    trk(n_rf, F, RF_W, [(10.45, 11.20), ("L2", 1)])
    trk("Net-(C6-Pad1)", F, RF_W, [("L2", 2), ("L3", 1)])
    x6, y6 = xy("C6", 1)
    trk("Net-(C6-Pad1)", F, RF_W, [(x6, 11.20), (x6, y6)])            # shunt stub up to C6
    trk("Net-(C9-Pad1)", F, RF_W, [("L3", 2), ("L4", 1)])
    x9, y9 = xy("C9", 1)
    trk("Net-(C9-Pad1)", F, RF_W, [(x9 + 0.05, 11.20), (x9 + 0.05, y9)])  # shunt stub down to C9
    # long run: L4 pad 2 -> north -> east -> north to R2 pad 1 and C11 (45 degree corners)
    xa, ya = xy("L4", 2)
    xr, yr = xy("R2", 1)
    xc, yc = xy("C11", 1)
    c = 0.6
    trk("Net-(C11-Pad1)", F, RF_W, [
        (xa, ya), (xa, 7.4 + c), (xa + c, 7.4), (xr - c, 7.4), (xr, 7.4 - c),
        (xr, yr + 0.3), (xr, 3.35), (xc, 3.35), (xc, yc)])
    # tee: R2 -> R3, C14 stub down, R3 -> antenna feed pad
    trk("Net-(C14-Pad1)", F, RF_W, [("R2", 2), ("R3", 1)])
    xs, ys = xy("C14", 1)
    trk("Net-(C14-Pad1)", F, RF_W, [(xs, 2.50), (xs, ys)])
    trk("Net-(AE1-FEED)", F, RF_W, [("R3", 2), ("AE1", 1)])
    # grounds of the shunt parts: via next to each ground pad, outside the antenna box
    gnd_via("C11", 2, 0.0, -0.65)
    gnd_via("C14", 2, 0.0, 0.65)
    gnd_via("NT1", 1, 0.0, 0.65)
    gnd_via("NT2", 1, -0.6, 0.0)
    # VSS_PA star: U1 pin 32 and C6 pad 2 meet at the net tie NT1 (the only link to ground).
    # C6 is on the other side of the RF line from NT1, so its tie goes under the line on In2.
    xp, yp = xy("U1", 32)
    xn, yn = xy("NT1", 2)
    trk("/mcu/VSS_PA", F, SIG_W, [(10.45, 11.65), (xn + 0.9, 11.65), (xn + 0.25, yn)])
    x62, y62 = xy("C6", 2)
    vN = (x62, 9.45)      # north of C6: clear of the bottom photodiode pads (through via)
    vS = (8.22, 11.95)    # east of NT1: 0.3 mm from every foreign pad and the tie copper
    trk("/mcu/VSS_PA", F, SIG_W, [(x62, y62), vN])
    via("/mcu/VSS_PA", *vN)
    trk("/mcu/VSS_PA", IN2, SIG_W, [vN, (vS[0], vN[1]), vS])
    via("/mcu/VSS_PA", *vS)
    trk("/mcu/VSS_PA", F, SIG_W, [vS, (xn, yn)])
    # C9 pad 2 -> NT2 pad 2 (its own ground tie)
    trk("Net-(C9-Pad2)", F, SIG_W, [("C9", 2), ("NT2", 2)])


def group_xtal():
    # 32.768 kHz crystal X1 (right of U1): two short top-layer tracks, no vias, nothing between them
    xl1 = "Net-(U1A-P1.00{slash}XL1)"
    xl2 = "Net-(U1A-P1.01{slash}XL2)"
    x1a, y1a = xy("X1", 1)
    x1b, y1b = xy("X1", 2)
    trk(xl1, F, SIG_W, [(16.55, 13.20), (17.10, 13.75), (x1a - 0.15, 13.75), (x1a - 0.15, y1a - 0.5)])
    trk(xl2, F, SIG_W, [(16.55, 12.80), (17.00, 12.80), (17.65, 13.45), (x1b, 13.45), (x1b, y1b - 0.5)])


GROUPS = {"rf": group_rf, "xtal": group_xtal}


def main():
    want = ["rf", "xtal"]
    if "--groups" in sys.argv:
        want = sys.argv[sys.argv.index("--groups") + 1].split(",")
    for g in want:
        GROUPS[g]()
    pcbnew.SaveBoard(BOARD, board, True)
    print("saved", BOARD, "groups:", want)


if __name__ == "__main__":
    main()
