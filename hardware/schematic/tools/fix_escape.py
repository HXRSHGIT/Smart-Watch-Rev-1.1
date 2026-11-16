"""Escape-aware placement fix (run with KiCad 9's python).

The first placement put passives right in front of IC pin ends. DRC is happy, but those pins
have no way out for a track (see check_escape.py). This moves ONLY loose passives (not ICs,
connectors, test points, the optics group, the RF chain or the crystals) to the nearest legal
spot that keeps every IC signal pin lane free, and stays close to the pins the part serves.

A "lane" is the strip in front of an IC pad: pad width + 0.2 mm wide, from the pad end 0.7 mm
outward (0.45 mm for GND / +1V8 pads). A passive may stand in a lane only if one of its own
pads is on that pad's net. Candidates: every 0.05 mm within 4 mm, 4 rotations, same face.

Usage:  python fix_escape.py [--dry]

Done by Harsh Thakur.
"""
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.normpath(os.path.join(HERE, "..", "smartwatch.kicad_pcb"))
mm = pcbnew.ToMM
board = pcbnew.LoadBoard(BOARD)
board.BuildCourtyardCaches() if hasattr(board, "BuildCourtyardCaches") else None
_e = board.GetBoardEdgesBoundingBox()
W, H, EDGE = mm(_e.GetRight()), mm(_e.GetBottom()), 0.3
ANT = (0.0, 0.0, 6.5, 6.5)
FROZEN = {"AE1", "R3", "C14", "R2", "C11", "L2", "L3", "L4", "C6", "C9", "NT1", "NT2", "X1", "X2"}   # RF chain + crystals
RADIUS, STEP = 4.0, 0.1
PLANE = {"GND", "+1V8"}


def rotv(dx, dy, k):
    for _ in range(k % 4):
        dx, dy = dy, -dx
    return dx, dy


parts = {}
for f in board.GetFootprints():
    ref = f.GetReference()
    p = f.GetPosition()
    side = pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd
    bb = f.GetCourtyard(side).BBox()
    if bb.GetWidth() == 0:
        bb = f.GetBoundingBox(False)
    x, y = mm(p.x), mm(p.y)
    parts[ref] = dict(
        fp=f, x=x, y=y, rot=f.GetOrientationDegrees(), bottom=f.IsFlipped(),
        box=(mm(bb.GetLeft()) - x, mm(bb.GetTop()) - y, mm(bb.GetRight()) - x, mm(bb.GetBottom()) - y),
        pads=[(pd.GetNetname(), mm(pd.GetPosition().x) - x, mm(pd.GetPosition().y) - y) for pd in f.Pads()],
        psz=[(mm(pd.GetBoundingBox().GetWidth()), mm(pd.GetBoundingBox().GetHeight())) for pd in f.Pads()],
        tht=any(pd.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for pd in f.Pads()),
    )


def rbox(b, k):
    xs, ys = [], []
    for cx, cy in ((b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])):
        a, c = rotv(cx, cy, k)
        xs.append(a)
        ys.append(c)
    return (min(xs), min(ys), max(xs), max(ys))


def inter(a, b):
    return min(a[2], b[2]) - max(a[0], b[0]) > 0.002 and min(a[3], b[3]) - max(a[1], b[1]) > 0.002


# ---- lanes in front of every IC / emitter / photodiode pad ----------------------------------
def is_signal_part(ref):
    return ref.startswith(("U", "PD", "D")) and not ref.startswith(("DNP",))


lanes = []   # (rect, net, bottom)
for ref, d in parts.items():
    if not is_signal_part(ref):
        continue
    f = d["fp"]
    cb = d["box"]
    bx0, by0, bx1, by1 = d["x"] + cb[0], d["y"] + cb[1], d["x"] + cb[2], d["y"] + cb[3]
    for pd in f.Pads():
        net = pd.GetNetname()
        if net == "" or net.startswith("unconnected") or pd.GetNumber() == "":
            continue
        bb = pd.GetBoundingBox()
        w, h = mm(bb.GetWidth()), mm(bb.GetHeight())
        if min(w, h) > 1.2:
            continue                                   # exposed pad
        px, py = mm(pd.GetPosition().x), mm(pd.GetPosition().y)
        L = 0.45 if net in PLANE else 0.7
        dirs = []
        if abs(w - h) >= 0.05:                         # elongated pad: out along its long axis
            dx, dy = px - d["x"], py - d["y"]
            dirs.append(((1 if dx > 0 else -1), 0) if w > h else (0, (1 if dy > 0 else -1)))
        else:                                          # ball / square pad: every side that faces the part edge
            if px - w / 2 - bx0 < 0.45: dirs.append((-1, 0))
            if bx1 - (px + w / 2) < 0.45: dirs.append((1, 0))
            if py - h / 2 - by0 < 0.45: dirs.append((0, -1))
            if by1 - (py + h / 2) < 0.45: dirs.append((0, 1))
        for ux, uy in dirs:
            if ux:
                x0 = px + ux * w / 2
                rect = (min(x0, x0 + ux * L), py - h / 2 - 0.1, max(x0, x0 + ux * L), py + h / 2 + 0.1)
            else:
                y0 = py + uy * h / 2
                rect = (px - w / 2 - 0.1, min(y0, y0 + uy * L), px + w / 2 + 0.1, max(y0, y0 + uy * L))
            lanes.append((rect, net, d["bottom"]))

movable = [r for r, d in parts.items()
           if r[0] in "RCLF" and not r.startswith(("FB", "FID")) and r not in FROZEN or r.startswith("FB") and r not in FROZEN]
movable = [r for r in movable if not r.startswith(("TP", "J", "SW"))]


def world(ref, x, y, k):
    d = parts[ref]
    b = rbox(d["box"], k)
    box = (x + b[0], y + b[1], x + b[2], y + b[3])
    pads = []
    for n, ox, oy in d["pads"]:
        a, c = rotv(ox, oy, k)
        pads.append((n, x + a, y + c))
    return box, pads


def lane_violations(ref, box, pads):
    nets = {n for n, _, _ in pads}
    bottom = parts[ref]["bottom"]
    n = 0
    for rect, net, lb in lanes:
        if lb == bottom and inter(box, rect) and net not in nets:
            n += 1
    return n


cur = {r: (d["x"], d["y"], 0) for r, d in parts.items()}      # (x, y, extra quarter turns)
box_of = {r: world(r, *cur[r])[0] for r in parts}
ic_pads = []
for r, d in parts.items():
    if is_signal_part(r):
        for n, ox, oy in d["pads"]:
            if n not in PLANE and n != "" and not n.startswith("unconnected"):
                ic_pads.append((n, d["x"] + ox, d["y"] + oy, d["bottom"]))


def cost(ref, x, y, k):
    box, pads = world(ref, x, y, k)
    c = 0.0
    for n, px, py in pads:
        if n in ("GND", "") or n.startswith("unconnected"):
            continue
        best = min((math.hypot(px - qx, py - qy) for m, qx, qy, bt in ic_pads if m == n and bt == parts[ref]["bottom"]), default=0)
        c += best
    return c


def pad_boxes(ref, x, y, k):
    """World bounding boxes (net, box) of every pad of ref at (x, y) with k extra quarter turns."""
    d = parts[ref]
    out = []
    for (n, ox, oy), (w, h) in zip(d["pads"], d["psz"]):
        a, c = rotv(ox, oy, k)
        if k % 2:
            w, h = h, w
        out.append((n, (x + a - w / 2, y + c - h / 2, x + a + w / 2, y + c + h / 2)))
    return out


def all_pad_boxes():
    res = []
    for r, d in parts.items():
        xk = cur[r] if r in cur else (d["x"], d["y"], 0)
        for n, b in pad_boxes(r, *xk):
            res.append((r, n, b, d["bottom"], d["tht"]))
    return res


PADS = None
LANE_P = 0.6


def pad_lanes_free(ref, x, y, k):
    """Every signal pad of ref needs one free direction: a strip LANE_P long past the pad edge,
    clear (0.15 mm) of every other part's pad copper and of the board edge."""
    d = parts[ref]
    for n, b in pad_boxes(ref, x, y, k):
        if n in ("GND", "") or n.startswith("unconnected"):
            continue
        w, h = b[2] - b[0], b[3] - b[1]
        free = False
        for ux, uy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if ux:
                x0 = b[2] if ux > 0 else b[0]
                rect = (min(x0, x0 + ux * LANE_P), b[1] - 0.05, max(x0, x0 + ux * LANE_P), b[3] + 0.05)
            else:
                y0 = b[3] if uy > 0 else b[1]
                rect = (b[0] - 0.05, min(y0, y0 + uy * LANE_P), b[2] + 0.05, max(y0, y0 + uy * LANE_P))
            if rect[0] < 0.25 or rect[1] < 0.25 or rect[2] > W - 0.25 or rect[3] > H - 0.25:
                continue
            ok = True
            fat = (rect[0] - 0.15, rect[1] - 0.15, rect[2] + 0.15, rect[3] + 0.15)
            for r2, n2, b2, bot2, tht2 in PADS:
                if r2 == ref or (bot2 != d["bottom"] and not (tht2 or d["tht"])) or n2 == n:
                    continue
                if inter(fat, b2):
                    ok = False
                    break
            if ok:
                free = True
                break
        if not free:
            return False
    return True


def track_rects():
    out = []
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            r = mm(t.GetWidth(pcbnew.F_Cu)) / 2 + 0.15
            out.append(((mm(p.x) - r, mm(p.y) - r, mm(p.x) + r, mm(p.y) + r), None))
        else:
            a, b = t.GetStart(), t.GetEnd()
            r = mm(t.GetWidth()) / 2 + 0.15
            out.append(((min(mm(a.x), mm(b.x)) - r, min(mm(a.y), mm(b.y)) - r, max(mm(a.x), mm(b.x)) + r, max(mm(a.y), mm(b.y)) + r),
                        t.GetLayer() == pcbnew.B_Cu))
    return out


TRACKS = track_rects()


def legal(ref, box, pads, x=None, y=None, k=0):
    for rect, onbottom in TRACKS:
        if (onbottom is None or onbottom == parts[ref]["bottom"]) and inter(box, rect):
            return False
    if box[0] < EDGE or box[1] < EDGE or box[2] > W - EDGE or box[3] > H - EDGE:
        return False
    if inter(box, ANT):
        return False
    d = parts[ref]
    for r2, b2 in box_of.items():
        if r2 == ref:
            continue
        d2 = parts[r2]
        if d2["bottom"] != d["bottom"] and not (d2["tht"] or d["tht"]):
            continue
        if inter(box, b2):
            return False
    if lane_violations(ref, box, pads) != 0:
        return False
    return pad_lanes_free(ref, x, y, k)


def current_bad():
    out = []
    for r in movable:
        box, pads = world(r, *cur[r])
        if lane_violations(r, box, pads) or not pad_lanes_free(r, *cur[r]):
            out.append(r)
    return out


def main():
    global PADS
    moved = {}
    for sweep in range(6):
        PADS = all_pad_boxes()
        bad = current_bad()
        print("sweep %d: %d passives block a pin lane" % (sweep, len(bad)))
        if not bad:
            break
        for r in bad:
            x0, y0, k0 = cur[r]
            best = None
            for rad in (RADIUS, 2 * RADIUS, 4 * RADIUS):          # widen the search if nothing fits nearby
                n = int(rad / STEP)
                for i in range(-n, n + 1):
                    for j in range(-n, n + 1):
                        x, y = x0 + i * STEP, y0 + j * STEP
                        if math.hypot(x - x0, y - y0) > rad:
                            continue
                        for k in range(4):
                            box, pads = world(r, x, y, k)
                            if not legal(r, box, pads, x, y, k):
                                continue
                            c = cost(r, x, y, k) + 0.4 * math.hypot(x - x0, y - y0)
                            if best is None or c < best[0]:
                                best = (c, x, y, k, box)
                if best:
                    break
            if best:
                _, x, y, k, box = best
                cur[r] = (x, y, k)
                box_of[r] = box
                moved[r] = (x, y, k)
                PADS = all_pad_boxes()
            else:
                print("   no legal spot for", r)
    PADS = all_pad_boxes()
    left = current_bad()
    print("moved %d passives; still blocking: %s" % (len(moved), left))
    if "--dry" in sys.argv:
        return
    for r, (x, y, k) in moved.items():
        f = parts[r]["fp"]
        _, pads = world(r, x, y, k)
        f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        f.SetOrientationDegrees(parts[r]["rot"] + 90 * k)
        for pd, (n, px, py) in zip(f.Pads(), pads):
            assert abs(mm(pd.GetPosition().x) - px) < 0.01 and abs(mm(pd.GetPosition().y) - py) < 0.01, \
                (r, pd.GetNumber(), mm(pd.GetPosition().x), px)
    pcbnew.SaveBoard(BOARD, board, True)
    print("saved", BOARD)


if __name__ == "__main__":
    main()
