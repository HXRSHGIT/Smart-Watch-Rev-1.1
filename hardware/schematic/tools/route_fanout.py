"""Ground and 1.8 V via fan-out (run with KiCad 9's python).

For every GND and +1V8 pad that is not yet connected, find the nearest legal via spot
(0.45 / 0.20 mm via, JLCPCB rules from the project), join it to the pad with a short track and
lock both. A via already placed for the same net within reach is shared instead of adding
a new one. Exposed pads get a small via array. GND goes to the In1 plane, +1V8 to the In2 pour
that route_zones.py / the final step adds.

Usage:  python route_fanout.py            (works on the current board file)

Done by Harsh Thakur.
"""
import math
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.normpath(os.path.join(HERE, "..", "smartwatch.kicad_pcb"))
mm, tomm = pcbnew.FromMM, pcbnew.ToMM
VIA_D, VIA_H = 0.45, 0.20
CLR = 0.11                    # copper clearance used for the search (rule is 0.10)
EDGE = 0.60                   # via centre to board edge
ANT = (0.0, 0.0, 6.6, 6.6)    # antenna clearance: no vias
STUB = {"GND": 0.12, "+1V8": 0.15}
TARGETS = ("GND", "+1V8")
REACH = 1.5                   # share an existing via within this distance

board = pcbnew.LoadBoard(BOARD)
W = tomm(board.GetBoardEdgesBoundingBox().GetRight())
H = tomm(board.GetBoardEdgesBoundingBox().GetBottom())


def vec(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def shapes_all():
    """(net, layer-set, shape) for every pad, track and via on the board."""
    items = []
    for f in board.GetFootprints():
        for p in f.Pads():
            layers = [l for l in (pcbnew.F_Cu, pcbnew.B_Cu) if p.IsOnLayer(l)]
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                layers = [pcbnew.F_Cu]          # through pad: its shape is the same on every layer
            for l in layers[:1]:
                items.append((p.GetNetname(), p, p.GetEffectiveShape(l)))
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            items.append((t.GetNetname(), t, t.GetEffectiveShape(pcbnew.F_Cu)))
        else:
            items.append((t.GetNetname(), t, t.GetEffectiveShape()))
    return items


ITEMS = shapes_all()


def free(shape, net, ignore=(), clr=CLR):
    for n, obj, sh in ITEMS:
        if obj in ignore:
            continue
        if n == net and n != "":
            continue
        if shape.Collide(sh, mm(clr)):
            return False
    return True


def new_via(net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(vec(x, y))
    v.SetWidth(mm(VIA_D))
    v.SetDrill(mm(VIA_H))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(board.FindNet(net))
    v.SetLocked(True)
    board.Add(v)
    ITEMS.append((net, v, v.GetEffectiveShape(pcbnew.F_Cu)))
    return v


def new_track(net, layer, w, x1, y1, x2, y2):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(vec(x1, y1))
    t.SetEnd(vec(x2, y2))
    t.SetWidth(mm(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    t.SetLocked(True)
    board.Add(t)
    ITEMS.append((net, t, t.GetEffectiveShape()))
    return t


def probe_via(net, x, y, own_pad):
    if not (EDGE <= x <= W - EDGE and EDGE <= y <= H - EDGE):
        return None
    if ANT[0] - 0.4 <= x <= ANT[2] and ANT[1] - 0.4 <= y <= ANT[3]:
        return None
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(vec(x, y))
    v.SetWidth(mm(VIA_D))
    v.SetDrill(mm(VIA_H))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    sh = v.GetEffectiveShape(pcbnew.F_Cu)
    for n2, obj, sh2 in ITEMS:                       # hole to hole: 0.25 mm between drills, any net
        if obj.GetClass() == "PCB_VIA":
            if math.hypot(tomm(obj.GetPosition().x) - x, tomm(obj.GetPosition().y) - y) < VIA_D + 0.05:
                return None
    # keep clear of every other-net item, and of its own pad's copper edge (no via in a small pad)
    if not free(sh, net, ignore=(own_pad,)):
        return None
    if own_pad.GetSize().x < mm(1.5) and sh.Collide(own_pad.GetEffectiveShape(pcbnew.F_Cu), mm(0.08)):
        return None
    return sh


def stub_ok(net, layer, w, x1, y1, x2, y2, own_pad, via_obj=None):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(vec(x1, y1))
    t.SetEnd(vec(x2, y2))
    t.SetWidth(mm(w))
    t.SetLayer(layer)
    return free(t.GetEffectiveShape(), net, ignore=(own_pad, via_obj))


def connected(pad, net):
    bb = pad.GetBoundingBox()
    for n, obj, sh in ITEMS:
        if n == net and obj is not pad and obj.GetClass() in ("PCB_TRACK", "PCB_VIA"):
            if obj.GetClass() == "PCB_VIA":
                if bb.Contains(obj.GetPosition()):
                    return True
            elif bb.Contains(obj.GetStart()) or bb.Contains(obj.GetEnd()):
                return True
    return False


def vias_of(net):
    return [obj for n, obj, sh in ITEMS if n == net and obj.GetClass() == "PCB_VIA"]


stats = {"new": 0, "shared": 0, "fail": []}


def fan_pad(f, pad):
    net = pad.GetNetname()
    layer = pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
    px, py = tomm(pad.GetPosition().x), tomm(pad.GetPosition().y)
    w = STUB[net]
    # 1) share a via that is already close and reachable
    best = None
    for v in vias_of(net):
        vx, vy = tomm(v.GetPosition().x), tomm(v.GetPosition().y)
        d = math.hypot(vx - px, vy - py)
        ddx, ddy = abs(vx - px), abs(vy - py)
        aligned = ddx < 0.02 or ddy < 0.02 or abs(ddx - ddy) < 0.02      # 0 / 45 / 90 degrees only
        if aligned and d <= REACH and (best is None or d < best[0]):
            if stub_ok(net, layer, w, px, py, vx, vy, pad, v):
                best = (d, vx, vy)
    if best:
        new_track(net, layer, w, px, py, best[1], best[2])
        stats["shared"] += 1
        return True
    # 2) new via on the nearest legal spot (16 directions, growing radius)
    for r in [0.50 + 0.05 * i for i in range(0, 30)]:
        cands = []
        for k in range(8):                      # 0 / 45 / 90 degrees only
            a = 2 * math.pi * k / 8
            cands.append((px + r * math.cos(a), py + r * math.sin(a)))
        for x, y in cands:
            if probe_via(net, x, y, pad) is None:
                continue
            if stub_ok(net, layer, w, px, py, x, y, pad):
                new_via(net, x, y)
                new_track(net, layer, w, px, py, x, y)
                stats["new"] += 1
                return True
    stats["fail"].append((f.GetReference(), pad.GetNumber(), net))
    return False


def fan_exposed(f, pad):
    """Exposed pad (large): a grid of vias inside it (tented by JLCPCB's default via covering)."""
    net = pad.GetNetname()
    bb = pad.GetBoundingBox()
    x0, x1 = tomm(bb.GetLeft()), tomm(bb.GetRight())
    y0, y1 = tomm(bb.GetTop()), tomm(bb.GetBottom())
    nx = max(1, int((x1 - x0) // 1.4))
    ny = max(1, int((y1 - y0) // 1.4))
    n = 0
    for i in range(nx):
        for j in range(ny):
            x = x0 + (i + 0.5) * (x1 - x0) / nx
            y = y0 + (j + 0.5) * (y1 - y0) / ny
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(vec(x, y))
            v.SetWidth(mm(VIA_D))
            v.SetDrill(mm(VIA_H))
            if free(v.GetEffectiveShape(pcbnew.F_Cu), net, ignore=(pad,)):
                new_via(net, x, y)
                n += 1
    stats["new"] += n


def main():
    for f in list(board.GetFootprints()):
        for pad in list(f.Pads()):
            net = pad.GetNetname()
            if net not in TARGETS:
                continue
            if pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                continue                      # through-hole pads reach every layer already
            if f.GetReference().startswith("NT"):
                continue                      # net-tie pads: handled with the RF group
            if connected(pad, net):
                continue
            if min(pad.GetSize().x, pad.GetSize().y) > mm(2.0):
                fan_exposed(f, pad)
            elif pad.GetNumber() == "":
                continue                      # paste sub-pads of an exposed pad
            else:
                fan_pad(f, pad)
    pcbnew.SaveBoard(BOARD, board, True)
    print("fan-out: %d new vias, %d shared, %d failed" % (stats["new"], stats["shared"], len(stats["fail"])))
    for x in stats["fail"]:
        print("  failed:", x)


if __name__ == "__main__":
    main()
