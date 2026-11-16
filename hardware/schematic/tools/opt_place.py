"""Improve the placement for routability (run with KiCad 9's python).

Fixed (never moved): connectors J1-J5, SW1, test points, the antenna and its tee (AE1, R3, C14,
R2, C11), the whole back-face optics group (PD1, D1, PD2, U2, U4, U6 and their passives).
Movable: the top-face ICs U1, U3, U5, U7, U8 and the crystals X1, X2, each moved RIGIDLY with
the passives that serve it (a cluster), shifted and turned in 90 degree steps.

Cost = weighted half-perimeter wire length of every net that leaves a cluster
       + large penalties for overlapping courtyards, leaving the board, or entering the
         6.5 x 6.5 mm antenna clearance.

Usage:  python opt_place.py [--apply] [--seed N] [--iters N]
Without --apply it only reports (before/after wire length) and writes poses to opt_poses.json.
--apply writes the new poses into the board file (loaded from git HEAD, so it is repeatable).

Done by Harsh Thakur.
"""
import json
import math
import os
import random
import subprocess
import sys
import tempfile

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.normpath(os.path.join(HERE, "..", "smartwatch.kicad_pcb"))
mm = pcbnew.ToMM
W, H, EDGE = 34.0, 23.0, 0.3
ANT_BOX = (0.0, 0.0, 6.5, 6.5)
MOVABLE = ["U1", "U3", "U5", "U7", "U8", "X1", "X2"]
FIXED_CLUSTER = {"AE1", "R3", "C14", "R2", "C11"}
WEIGHT = {"GND": 0.0, "+1V8": 0.35}          # GND and 1.8 V are planes/short stubs
HOT = ("/mcu/RF_ANT", "Net-(C11-Pad1)", "Net-(C6-Pad1)", "Net-(C9-Pad1)", "Net-(U1A-XC1)",
       "Net-(U1A-XC2)", "Net-(U1A-P1.00{slash}XL1)", "Net-(U1A-P1.01{slash}XL2)")


def load():
    rel = "hardware/schematic/smartwatch.kicad_pcb"
    top = subprocess.check_output(["git", "-C", HERE, "rev-parse", "--show-toplevel"], text=True).strip()
    data = subprocess.check_output(["git", "-C", top, "show", "HEAD:" + rel])
    tmp = os.path.join(tempfile.mkdtemp(), "smartwatch.kicad_pcb")
    open(tmp, "wb").write(data)
    return pcbnew.LoadBoard(tmp)


board = load()
board.BuildCourtyardCaches() if hasattr(board, "BuildCourtyardCaches") else None

# ---- snapshot every footprint -------------------------------------------------------------
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
        x=x, y=y, rot=f.GetOrientationDegrees(), bottom=f.IsFlipped(),
        box=(mm(bb.GetLeft()) - x, mm(bb.GetTop()) - y, mm(bb.GetRight()) - x, mm(bb.GetBottom()) - y),
        pads=[(pd.GetNetname(), mm(pd.GetPosition().x) - x, mm(pd.GetPosition().y) - y) for pd in f.Pads()],
        tht=any(pd.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for pd in f.Pads()),
    )

# ---- clusters: each passive follows the IC that owns its smallest non-ground net ----------
netpads = {}
for ref, d in parts.items():
    for n, ox, oy in d["pads"]:
        netpads.setdefault(n, []).append((ref, d["x"] + ox, d["y"] + oy))
ICS = [r for r in parts if r.startswith(("U", "X")) and r not in ("U9",)]


def owner(ref):
    d = parts[ref]
    best = None
    for n, ox, oy in d["pads"]:
        if n in ("GND", "") or n.startswith("unconnected"):
            continue
        for r2, x2, y2 in netpads[n]:
            if r2 in ICS and r2 != ref and parts[r2]["bottom"] == d["bottom"]:
                dist = math.hypot(d["x"] + ox - x2, d["y"] + oy - y2)
                key = (len(netpads[n]) > 40, dist)
                if best is None or key < best[0]:
                    best = (key, r2)
    return best[1] if best else None


cluster = {m: [m] for m in MOVABLE}
fixed = set(r for r in parts if r not in MOVABLE)
for ref in list(parts):
    if ref in MOVABLE or ref.startswith(("TP", "J", "SW", "AE", "PD", "D")) or ref in FIXED_CLUSTER:
        continue
    if parts[ref]["bottom"]:
        continue
    o = owner(ref)
    if o in cluster:
        cluster[o].append(ref)
        fixed.discard(ref)
member_of = {r: m for m, rs in cluster.items() for r in rs}
# the RF tee and crystal-adjacent parts that stay with the antenna
for r in FIXED_CLUSTER:
    fixed.add(r)
print({m: len(v) for m, v in cluster.items()})


# ---- geometry helpers ---------------------------------------------------------------------
def rotv(dx, dy, k):
    """Rotate a vector by k*90 degrees counter-clockwise on screen (y points down)."""
    for _ in range(k % 4):
        dx, dy = dy, -dx
    return dx, dy


def rotbox(b, k):
    xs, ys = [], []
    for cx, cy in ((b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])):
        a, c = rotv(cx, cy, k)
        xs.append(a)
        ys.append(c)
    return (min(xs), min(ys), max(xs), max(ys))


def pose(state):
    """state: {cluster: (dx, dy, k)} -> {ref: (x, y, boxabs, padabs[])} for every part."""
    out = {}
    for ref, d in parts.items():
        m = member_of.get(ref)
        if m and m in state:
            dx, dy, k = state[m]
            px, py = parts[m]["x"], parts[m]["y"]
            rx, ry = rotv(d["x"] - px, d["y"] - py, k)
            x, y = px + dx + rx, py + dy + ry
            b = rotbox(d["box"], k)
            pads = []
            for n, ox, oy in d["pads"]:
                a, c = rotv(ox, oy, k)
                pads.append((n, x + a, y + c))
        else:
            x, y, b = d["x"], d["y"], d["box"]
            pads = [(n, x + ox, y + oy) for n, ox, oy in d["pads"]]
        out[ref] = (x, y, (x + b[0], y + b[1], x + b[2], y + b[3]), pads)
    return out


def overlap(a, b, gap=0.0):
    w = min(a[2], b[2]) - max(a[0], b[0]) + gap
    h = min(a[3], b[3]) - max(a[1], b[1]) + gap
    return w * h if w > 0.002 and h > 0.002 else 0.0


PITCH = 0.2          # 0.1 mm track + 0.1 mm gap (JLCPCB rules in the project)
DERATE = 0.5         # practical share of the theoretical track capacity
NOROUTE = ("GND", "+1V8")


def mst(pts):
    """Prim minimum spanning tree over (x, y, owner) points -> list of segments."""
    n = len(pts)
    seen = {0}
    segs = []
    d = [(math.hypot(pts[0][0] - p[0], pts[0][1] - p[1]), 0) for p in pts]
    while len(seen) < n:
        k = min((i for i in range(n) if i not in seen), key=lambda i: d[i][0])
        seen.add(k)
        a = pts[d[k][1]]
        segs.append((a[0], a[1], pts[k][0], pts[k][1]))
        for i in range(n):
            if i not in seen:
                dd = math.hypot(pts[k][0] - pts[i][0], pts[k][1] - pts[i][1])
                if dd < d[i][0]:
                    d[i] = (dd, k)
    return segs


def crosses(a, b):
    ax, ay, bx, by = a
    cx, cy, dx, dy = b
    if max(ax, bx) < min(cx, dx) or max(cx, dx) < min(ax, bx) or max(ay, by) < min(cy, dy) or max(cy, dy) < min(ay, by):
        return False

    def o(px, py, qx, qy, rx, ry):
        return (qx - px) * (ry - py) - (qy - py) * (rx - px)
    d1, d2 = o(ax, ay, bx, by, cx, cy), o(ax, ay, bx, by, dx, dy)
    d3, d4 = o(cx, cy, dx, dy, ax, ay), o(cx, cy, dx, dy, bx, by)
    return d1 * d2 < -1e-9 and d3 * d4 < -1e-9


def congestion(P, nets):
    """RUDY-style demand map (wire length per mm2 spread over each net's bounding box)
    against the track capacity left by the parts on each face. Returns (overflow, peak ratio)."""
    gx, gy = int(W), int(H)
    dem = [[0.0] * gx for _ in range(gy)]
    for n, pts in nets.items():
        if n in NOROUTE or len(pts) < 2:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        w = max(max(xs) - min(xs), 0.5)
        h = max(max(ys) - min(ys), 0.5)
        rudy = (w + h) / (w * h)
        for cy in range(max(0, int(min(ys))), min(gy, int(max(ys)) + 1)):
            for cx in range(max(0, int(min(xs))), min(gx, int(max(xs)) + 1)):
                dem[cy][cx] += rudy
    # capacity: top and bottom layers lose the area covered by courtyards on that face;
    # In2 (L3) is a routing layer with 20 % lost to vias.
    cov = {False: [[0.0] * gx for _ in range(gy)], True: [[0.0] * gx for _ in range(gy)]}
    for ref, (x, y, b, pads) in P.items():
        face = parts[ref]["bottom"]
        for cy in range(max(0, int(b[1])), min(gy, int(b[3]) + 1)):
            for cx in range(max(0, int(b[0])), min(gx, int(b[2]) + 1)):
                ox = max(0.0, min(b[2], cx + 1) - max(b[0], cx))
                oy = max(0.0, min(b[3], cy + 1) - max(b[1], cy))
                cov[face][cy][cx] = min(1.0, cov[face][cy][cx] + ox * oy)
    cap_unit = DERATE / PITCH
    over = 0.0
    peak = 0.0
    for cy in range(gy):
        for cx in range(gx):
            cap = cap_unit * ((1 - 0.6 * cov[False][cy][cx]) + (1 - 0.6 * cov[True][cy][cx]) + 0.8)
            r = dem[cy][cx] / cap
            peak = max(peak, r)
            if r > 1:
                over += (r - 1)
    return over, peak


def cost(state, detail=False):
    P = pose(state)
    nets = {}
    for ref, (x, y, b, pads) in P.items():
        for n, px, py in pads:
            if n == "" or n.startswith("unconnected"):
                continue
            nets.setdefault(n, []).append((px, py, member_of.get(ref, ref)))
    wl = 0.0
    segs = []
    for n, pts in nets.items():
        if len({c for _, _, c in pts}) < 2:
            continue                        # entirely inside one cluster: moves with it
        wgt = WEIGHT.get(n, 1.0) * (3.0 if n in HOT else 1.0)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        wl += wgt * ((max(xs) - min(xs)) + (max(ys) - min(ys)))
        if n not in NOROUTE:
            for sg in mst(pts):
                segs.append((n, sg))
    nx = 0
    for i in range(len(segs)):
        ni, si = segs[i]
        for j2 in range(i + 1, len(segs)):
            if segs[j2][0] != ni and crosses(si, segs[j2][1]):
                nx += 1
    over, peak = congestion(P, nets)
    pen = 0.0
    refs = list(P)
    for i, a in enumerate(refs):
        ba = P[a][2]
        da = parts[a]
        if not (a in FIXED_CLUSTER or a == "AE1"):
            if ba[0] < EDGE or ba[1] < EDGE or ba[2] > W - EDGE or ba[3] > H - EDGE:
                pen += 50 + 20 * (max(EDGE - ba[0], EDGE - ba[1], ba[2] - W + EDGE, ba[3] - H + EDGE, 0))
        if a not in fixed and not da["bottom"]:
            pen += 200 * overlap(ba, ANT_BOX)
        for b_ in refs[i + 1:]:
            if parts[b_]["bottom"] != da["bottom"] and not (da["tht"] or parts[b_]["tht"]):
                continue
            if a in fixed and b_ in fixed:
                continue
            ov = overlap(ba, P[b_][2])
            if ov:
                pen += 80 + 400 * ov
    total = wl + 1.5 * nx + 25.0 * over + pen
    if detail:
        return dict(wire=wl, crossings=nx, overflow=over, peak=peak, penalty=pen, total=total)
    return total


def random_state():
    return {m: (0.0, 0.0, 0) for m in MOVABLE}


def anneal(seed, iters):
    rnd = random.Random(seed)
    st = random_state()
    cur = cost(st)
    best, bc = dict(st), cur
    T0 = 6.0
    for i in range(iters):
        T = T0 * (1 - i / iters) + 0.02
        m = rnd.choice(MOVABLE)
        dx, dy, k = st[m]
        r = rnd.random()
        if r < 0.15:
            nk = (k + rnd.choice((1, 2, 3))) % 4
            cand = (dx, dy, nk)
        else:
            s = max(0.4, 3.0 * (1 - i / iters))
            cand = (dx + rnd.gauss(0, s), dy + rnd.gauss(0, s), k)
        old = st[m]
        st[m] = cand
        c = cost(st)
        if c < cur or rnd.random() < math.exp((cur - c) / T):
            cur = c
            if c < bc:
                best, bc = dict(st), c
        else:
            st[m] = old
    return best, bc


def fmt(d):
    return "wire %.1f mm | crossings %d | congestion overflow %.2f, peak %.2f | penalty %.1f | score %.1f" % (
        d["wire"], d["crossings"], d["overflow"], d["peak"], d["penalty"], d["total"])


def main():
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 1
    iters = int(sys.argv[sys.argv.index("--iters") + 1]) if "--iters" in sys.argv else 4000
    base = random_state()
    print("current   :", fmt(cost(base, True)))
    if "--poses" in sys.argv:
        snap = json.load(open(sys.argv[sys.argv.index("--poses") + 1]))
        st = {m: tuple(v) for m, v in snap.items()}
    else:
        st, c = anneal(seed, iters)
        snap = {m: [round(v[0], 3), round(v[1], 3), v[2]] for m, v in st.items()}
        json.dump(snap, open(os.path.join(HERE, "opt_poses_%d.json" % seed), "w"), indent=1)
    print("candidate :", fmt(cost(st, True)))
    print(snap)
    if "--apply" in sys.argv:
        P = pose(st)
        for ref, (x, y, b, pads) in P.items():
            m = member_of.get(ref)
            if m and m in st and ref not in fixed:
                f = board.FindFootprintByReference(ref)
                f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
                f.SetOrientationDegrees(f.GetOrientationDegrees() + 90 * st[m][2])
                for pd, (n, px, py) in zip(f.Pads(), pads):
                    assert abs(mm(pd.GetPosition().x) - px) < 0.01 and abs(mm(pd.GetPosition().y) - py) < 0.01,                         (ref, pd.GetNumber(), mm(pd.GetPosition().x), px)
        pcbnew.SaveBoard(BOARD, board, True)
        print("applied to", BOARD)


if __name__ == "__main__":
    main()
