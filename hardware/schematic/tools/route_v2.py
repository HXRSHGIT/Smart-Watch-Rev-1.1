"""Router v2 for the 34 x 23 mm board (run with KiCad 9's python + numpy).

What it does, in order:
  1. Obstacles from the board, with exact clearance shapes (capsules / rounded rectangles on a
     0.05 mm grid, no rounding loss): pads, tracks and vias already there, net-tie copper,
     board edge, antenna clearance (no vias).
  2. Vias inside the exposed pads (GND) of U1 and U7.
  3. A straight exit reserved in front of every pad to be routed, so no net crosses another's.
  4. GND and +1V8 pads: shortest path on the pad's own layer to the nearest legal via spot
     (0.45/0.20 mm via; 0.30/0.15 mm only where the large one does not fit). In1 = GND plane,
     In2 = +1V8 plane, so a via is the whole connection.
  5. Power nets (0.2 mm) and signals (0.1 mm) on F.Cu and B.Cu with 45-degree corners; a route
     may end on a pad, a via or a track of its own net (T-junction). No vias on crystal / RF nets.
  6. Rip-up and reroute: if a connection cannot be made, a relaxed search finds which routed nets
     are in the way, those are removed and queued again (each net at most 3 times).
Rules: JLCPCB from the project (0.1 mm clearance, 0.09 mm min track, via hole 0.2 mm to copper,
copper 0.2 mm from the edge). Usage:  python route_v2.py
Done by Harsh Thakur.
"""
import collections
import heapq
import math
import os
import sys
import time

import numpy as np
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.normpath(os.path.join(HERE, "..", "smartwatch.kicad_pcb"))
RES = 0.05
CLR = 0.101                                  # JLCPCB rule 0.10 (exact shapes and distances; 0.001 float margin)
VB = (0.45, 0.20)                            # standard JLCPCB via (no surcharge)
VS = (0.30, 0.15)                            # JLCPCB minimum via, fallback only
VB_EXTRA = max(VB[0] / 2 + CLR, VB[1] / 2 + 0.2 + 0.01)
VS_EXTRA = max(VS[0] / 2 + CLR, VS[1] / 2 + 0.2 + 0.01)
WCLS = (0.1, 0.15, 0.17, 0.2)
RF_NETS = {"/mcu/RF_ANT", "Net-(C6-Pad1)", "Net-(C9-Pad1)", "Net-(C11-Pad1)", "Net-(C14-Pad1)", "Net-(AE1-FEED)"}
PROTECT = set()                              # filled in main(): RF, crystals, GND / +1V8 are never ripped
RF_W = 0.17                                   # 50 ohm on JLC04081H-3313 (my calculation, to confirm with JLCPCB)
POWER = {"VSYS", "VBUS_PROT", "VLED", "VLED_BOOST", "VBAT"}
PLANE = {"GND", "+1V8"}
NO_VIA = {"Net-(U1A-XC1)", "Net-(U1A-XC2)", "Net-(U1A-P1.00{slash}XL1)", "Net-(U1A-P1.01{slash}XL2)",
          "/mcu/RF_ANT", "Net-(C6-Pad1)", "Net-(C9-Pad1)", "Net-(C11-Pad1)", "Net-(C14-Pad1)", "Net-(AE1-FEED)"}
SIG = (0, 2)                                 # F.Cu, B.Cu (In2 is the +1V8 plane)
IN2 = "--in2" in sys.argv                    # leftover pass: short hops on In2 allowed (cost x3)
if IN2:
    SIG = (0, 1, 2)
IN2_COST = float(os.environ.get("IN2_COST", "3"))   # lower it to let the last nets use In2 freely
VIA_COST = 30
TURN = 0.6
HW = 1.4
MAXPOP = 5000000
RIP_PEN = 1.0
HW_RELAXED = 2.5                             # rip-up search: greedy, so it crosses blockers instead of flooding the board
STUB = 0.5
RIP_BUDGET = 45                              # total rip-ups per run (stops churning)
mm, tomm = pcbnew.FromMM, pcbnew.ToMM
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]

board = pcbnew.LoadBoard(BOARD)
_bb = board.GetBoardEdgesBoundingBox()
BW, BH = tomm(_bb.GetRight()), tomm(_bb.GetBottom())
NX, NY = int(BW / RES) + 1, int(BH / RES) + 1
NETCODE, NETNAME = {}, {}
for code, ni in board.GetNetsByNetcode().items():
    NETCODE[ni.GetNetname()] = code
    NETNAME[code] = ni.GetNetname()
KEEP = []                                    # removed SWIG objects must stay referenced


def cx(v):
    return int(round(v / RES))


NECK = {}                                   # net -> width override after a failed 0.2 mm attempt
W_USED = {}


def wclass(net):
    if net in NECK:
        return NECK[net]
    if net in RF_NETS:
        return RF_W
    return 0.2 if net in POWER else (0.15 if net in PLANE else 0.1)


# ------------------------------------------------------------------ grids --------------
class Grid:
    def __init__(self):
        self.t = {w: np.zeros((3, NY, NX), np.int32) for w in WCLS}
        self.vb = np.zeros((3, NY, NX), np.int32)
        self.vs = np.zeros((3, NY, NX), np.int32)

    def copy(self):
        g = Grid.__new__(Grid)
        g.t = {w: a.copy() for w, a in self.t.items()}
        g.vb, g.vs = self.vb.copy(), self.vs.copy()
        return g

    def kinds(self):
        return [(self.t[w], CLR + w / 2) for w in WCLS] + [(self.vb, VB_EXTRA), (self.vs, VS_EXTRA)]

    @staticmethod
    def _apply(sub, m, net):
        cur = sub[m]
        sub[m] = np.where(cur == 0, net, np.where(cur == net, net, -1))

    def capsule(self, layers, x1, y1, x2, y2, rad, net):
        for arr, extra in self.kinds():
            R = rad + extra
            ix0 = max(0, int(math.floor((min(x1, x2) - R) / RES)))
            ix1 = min(NX, int(math.ceil((max(x1, x2) + R) / RES)) + 1)
            iy0 = max(0, int(math.floor((min(y1, y2) - R) / RES)))
            iy1 = min(NY, int(math.ceil((max(y1, y2) + R) / RES)) + 1)
            if ix0 >= ix1 or iy0 >= iy1:
                continue
            X, Y = np.meshgrid(np.arange(ix0, ix1) * RES, np.arange(iy0, iy1) * RES)
            dx, dy = x2 - x1, y2 - y1
            L2 = dx * dx + dy * dy
            if L2 == 0:
                d2 = (X - x1) ** 2 + (Y - y1) ** 2
            else:
                t = np.clip(((X - x1) * dx + (Y - y1) * dy) / L2, 0, 1)
                d2 = (X - x1 - t * dx) ** 2 + (Y - y1 - t * dy) ** 2
            m = d2 <= R * R
            for l in layers:
                self._apply(arr[l, iy0:iy1, ix0:ix1], m, net)

    def rect(self, layers, x0, y0, x1, y1, net):
        for arr, extra in self.kinds():
            ix0 = max(0, int(math.floor((x0 - extra) / RES)))
            ix1 = min(NX, int(math.ceil((x1 + extra) / RES)) + 1)
            iy0 = max(0, int(math.floor((y0 - extra) / RES)))
            iy1 = min(NY, int(math.ceil((y1 + extra) / RES)) + 1)
            if ix0 >= ix1 or iy0 >= iy1:
                continue
            X, Y = np.meshgrid(np.arange(ix0, ix1) * RES, np.arange(iy0, iy1) * RES)
            ddx = np.maximum(np.maximum(x0 - X, 0), X - x1)
            ddy = np.maximum(np.maximum(y0 - Y, 0), Y - y1)
            m = ddx * ddx + ddy * ddy <= extra * extra
            for l in layers:
                self._apply(arr[l, iy0:iy1, ix0:ix1], m, net)


def has_copper(p):
    return any(p.IsOnLayer(l) for l in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu))


def is_tht(p):
    return p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)


def pad_layers(p):
    if is_tht(p):
        return [0, 1, 2]
    return [0] if p.IsOnLayer(pcbnew.F_Cu) else [2]


def pad_rect(p):
    b = p.GetBoundingBox()
    return tomm(b.GetLeft()), tomm(b.GetTop()), tomm(b.GetRight()), tomm(b.GetBottom())


def stamp_obj(g, o):
    net = o.GetNetCode() or 999999
    c = o.GetClass()
    if c == "PAD":
        if o.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:          # bare hole (KiCad lists it on *.Cu): 0.2 mm hole to copper
            p = o.GetPosition()
            r = tomm(o.GetDrillSize().x) / 2 + 0.2 - CLR + 0.005
            g.capsule([0, 1, 2], tomm(p.x), tomm(p.y), tomm(p.x), tomm(p.y), r, 999999)
        elif has_copper(o):
            if o.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:          # BGA / WLCSP balls: real circle, not the bbox
                p = o.GetPosition()
                g.capsule(pad_layers(o), tomm(p.x), tomm(p.y), tomm(p.x), tomm(p.y), tomm(o.GetSize().x) / 2, net)
            else:
                g.rect(pad_layers(o), *pad_rect(o), net)
    elif c == "PCB_VIA":
        p = o.GetPosition()
        x, y = tomm(p.x), tomm(p.y)
        g.capsule([0, 1, 2], x, y, x, y, tomm(o.GetWidth(pcbnew.F_Cu)) / 2, net)
        hr = tomm(o.GetDrillValue()) / 2
        for arr, own_h in ((g.vb, VB[1] / 2), (g.vs, VS[1] / 2)):   # hole to hole 0.25 mm, any net
            R = hr + 0.26 + own_h
            ix0, ix1 = max(0, int((x - R) / RES)), min(NX, int((x + R) / RES) + 2)
            iy0, iy1 = max(0, int((y - R) / RES)), min(NY, int((y + R) / RES) + 2)
            sx, sy = np.meshgrid(np.arange(ix0, ix1) * RES, np.arange(iy0, iy1) * RES)
            m = (sx - x) ** 2 + (sy - y) ** 2 < R * R
            for l in range(3):
                sub = arr[l, iy0:iy1, ix0:ix1]
                sub[m] = -1
    elif o.GetLayer() in LAYERS:
        s, e = o.GetStart(), o.GetEnd()
        g.capsule([LAYERS.index(o.GetLayer())], tomm(s.x), tomm(s.y), tomm(e.x), tomm(e.y), tomm(o.GetWidth()) / 2, net)


ADOPT = "--adopt" in sys.argv                # leftover pass: tracks of earlier runs may be ripped too


def adoptable(t):
    """Copper from an earlier router run that a leftover pass may rip: not RF / crystal / plane
    fan-out, and not the fixed 0.09 mm U4 escape stubs."""
    n = t.GetNetname()
    if n in RF_NETS or n in NO_VIA:
        return False
    if n in PLANE:
        if "--pf" not in sys.argv or not os.environ.get("PF_PLANES"):
            return False                          # plane fan-out stays fixed (negotiating it made PF diverge)
        if t.GetClass() == "PCB_VIA":            # exposed-pad vias stay fixed
            p = t.GetPosition()
            for f in board.GetFootprints():
                for pd in f.Pads():
                    if pd.GetNetname() == n and has_copper(pd) and min(tomm(pd.GetSize().x), tomm(pd.GetSize().y)) > 2.0 and pd.GetBoundingBox().Contains(p):
                        return False
    if t.GetClass() != "PCB_VIA" and abs(tomm(t.GetWidth()) - 0.09) < 0.001:
        return False
    return True


def rebuild_fixed_from_board():
    """Stamp every fixed obstacle of the board into GF (pads, existing copper, net-tie copper,
    board edge, antenna clearance, In2 closed for new tracks)."""
    for f in board.GetFootprints():
        for p in f.Pads():
            stamp_obj(GF, p)
        for gi in f.GraphicalItems():
            if gi.GetLayer() in LAYERS:
                b = gi.GetBoundingBox()
                GF.rect([LAYERS.index(gi.GetLayer())], tomm(b.GetLeft()), tomm(b.GetTop()), tomm(b.GetRight()), tomm(b.GetBottom()), 999999)
    for t in board.GetTracks():
        if ADOPT and adoptable(t):
            continue                          # adopted later as rippable routed copper
        stamp_obj(GF, t)
    for w in WCLS:
        GF.t[w][:, EDGE < 0.2 + w / 2 + 0.01] = -1
        if not IN2:
            GF.t[w][1, :, :] = np.where(GF.t[w][1] == 0, -1, GF.t[w][1])
    GF.vb[:, EDGE < 0.2 + VB[0] / 2 + 0.01] = -1
    GF.vs[:, EDGE < 0.2 + VS[0] / 2 + 0.01] = -1
    GF.vb[:, ANT] = -1
    GF.vs[:, ANT] = -1


t0 = time.time()
GF = Grid()
X, Y = np.meshgrid(np.arange(NX) * RES, np.arange(NY) * RES)
EDGE = np.minimum(np.minimum(X, BW - X), np.minimum(Y, BH - Y))
ANT = (X < 6.5 + VB[0] / 2 + 0.05) & (Y < 6.5 + VB[0] / 2 + 0.05)
# no via whose copper would touch any pad (no via-in-pad on small pads)
NOV_B = np.zeros((NY, NX), bool)
NOV_S = np.zeros((NY, NX), bool)
for f in board.GetFootprints():
    for p in f.Pads():
        if not has_copper(p):
            continue
        x0, y0, x1, y1 = pad_rect(p)
        for arr, r in ((NOV_B, VB[0] / 2 + 0.06), (NOV_S, VS[0] / 2 + 0.06)):
            ix0, ix1 = max(0, int(math.floor((x0 - r) / RES))), min(NX, int(math.ceil((x1 + r) / RES)) + 1)
            iy0, iy1 = max(0, int(math.floor((y0 - r) / RES))), min(NY, int(math.ceil((y1 + r) / RES)) + 1)
            sx, sy = np.meshgrid(np.arange(ix0, ix1) * RES, np.arange(iy0, iy1) * RES)
            ddx = np.maximum(np.maximum(x0 - sx, 0), sx - x1)
            ddy = np.maximum(np.maximum(y0 - sy, 0), sy - y1)
            arr[iy0:iy1, ix0:ix1] |= (ddx * ddx + ddy * ddy) < r * r
print("grids built %.1fs" % (time.time() - t0), flush=True)

ROUTED = collections.defaultdict(list)       # net -> objects added by this run (rippable)


def rebuild():
    g = GF.copy()
    for net, objs in ROUTED.items():
        for o in objs:
            stamp_obj(g, o)
    return g


GA = GF.copy()


# ------------------------------------------------------------------ board edits ---------
def add_track(net, l, x1, y1, x2, y2, w, fixed=False):
    if math.hypot(x2 - x1, y2 - y1) < 0.001:
        return None
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(w))
    t.SetLayer(LAYERS[l])
    t.SetNet(board.FindNet(net))
    board.Add(t)
    for g in ((GF, GA) if fixed else (GA,)):
        stamp_obj(g, t)
    if not fixed:
        ROUTED[net].append(t)
    return t


def add_via(net, x, y, size, fixed=False):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetWidth(mm(size[0]))
    v.SetDrill(mm(size[1]))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(board.FindNet(net))
    board.Add(v)
    for g in ((GF, GA) if fixed else (GA,)):
        stamp_obj(g, v)
    if not fixed:
        ROUTED[net].append(v)
    return v


def rip(net):
    for o in ROUTED.pop(net, []):
        board.RemoveNative(o)
        KEEP.append(o)


# ------------------------------------------------------------------ connectivity --------
def items_of(net):
    out = [p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() == net and has_copper(p)]
    out += [t for t in board.GetTracks() if t.GetNetname() == net]
    return out


def layers_of(o):
    if o.GetClass() == "PCB_VIA":
        return {0, 1, 2}
    if o.GetClass() == "PAD":
        return set(pad_layers(o))
    return {LAYERS.index(o.GetLayer())} if o.GetLayer() in LAYERS else set()


def shape_of(o):
    return o.GetEffectiveShape(pcbnew.F_Cu) if o.GetClass() in ("PAD", "PCB_VIA") else o.GetEffectiveShape()


def groups_of(net):
    its = items_of(net)
    sh = [shape_of(o) for o in its]
    ly = [layers_of(o) for o in its]
    par = list(range(len(its)))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for i in range(len(its)):
        for j in range(i + 1, len(its)):
            if ly[i] & ly[j] and sh[i].Collide(sh[j], 1):
                par[find(i)] = find(j)
    if net in PLANE:
        vias = [i for i, o in enumerate(its) if o.GetClass() == "PCB_VIA"]
        for a, b in zip(vias, vias[1:]):
            par[find(a)] = find(b)
    gs = collections.defaultdict(list)
    for i in range(len(its)):
        gs[find(i)].append(its[i])
    return list(gs.values())


def terminals(group, with_tracks):
    out = []
    for o in group:
        c = o.GetClass()
        if c in ("PAD", "PCB_VIA"):
            p = o.GetPosition()
            for l in layers_of(o):
                if l in SIG:
                    out.append((l, cx(tomm(p.x)), cx(tomm(p.y)), o))
        elif with_tracks and o.GetLayer() in LAYERS and LAYERS.index(o.GetLayer()) in SIG:
            s, e = o.GetStart(), o.GetEnd()
            x1, y1, x2, y2 = tomm(s.x), tomm(s.y), tomm(e.x), tomm(e.y)
            n = max(1, int(math.hypot(x2 - x1, y2 - y1) / RES))
            l = LAYERS.index(o.GetLayer())
            for i in range(n + 1):
                out.append((l, cx(x1 + (x2 - x1) * i / n), cx(y1 + (y2 - y1) * i / n), None))
    return out


# ------------------------------------------------------------------ search --------------
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
COST = [1, 1, 1, 1, 1.4142, 1.4142, 1.4142, 1.4142]


def protected_base():
    """GBASE + copper of protected nets: what a relaxed (rip-up) search may never cross."""
    g = GBASE.copy()
    for n in PROTECT:
        for o in ROUTED.get(n, []):
            stamp_obj(g, o)
    return g


def own_core(net):
    core = np.zeros((3, NY, NX), bool)
    for o in items_of(net):
        if o.GetClass() == "PAD":
            x0, y0, x1, y1 = pad_rect(o)
            for l in pad_layers(o):
                core[l, cx(y0):cx(y1) + 1, cx(x0):cx(x1) + 1] = True
    return core


def search(net, srcs, tgts, goal_via=None, relaxed=False):
    """goal_via: None, 'b' or 's' -> also accept any cell where that via fits (path then ends in a via).
    Returns (path, via_at_end) or (None, None)."""
    code = NETCODE[net]
    w = wclass(net)
    core = own_core(net)
    oka = (GA.t[w] == 0) | (GA.t[w] == code) | core
    gfx = protected_base() if (relaxed and GBASE is not None) else GF
    okf = (gfx.t[w] == 0) | (gfx.t[w] == code) | core
    ok = okf if relaxed else oka
    pen = (okf & ~oka) if relaxed else None
    vgrid, nov = (GA.vb, NOV_B) if goal_via != "s" else (GA.vs, NOV_S)
    vgf = gfx.vb if goal_via != "s" else gfx.vs
    vsrc = vgf if relaxed else vgrid
    okv = ((vsrc == 0) | (vsrc == code)).all(axis=0) & ~nov
    allow_via = net not in NO_VIA and goal_via is None
    okb = [ok[l].tobytes() for l in range(3)]
    penb = [pen[l].tobytes() for l in range(3)] if relaxed else None
    okvb = okv.tobytes()
    tset = {(t[0], t[1], t[2]) for t in tgts}
    sset = {(s[0], s[1], s[2]) for s in srcs}
    if tset and goal_via is None:
        txs = [t[1] for t in tset]
        tys = [t[2] for t in tset]
        bx0, bx1, by0, by1 = min(txs), max(txs), min(tys), max(tys)

        hw = HW_RELAXED if relaxed else HW

        def h(x, y):
            dx = max(bx0 - x, 0, x - bx1)
            dy = max(by0 - y, 0, y - by1)
            return hw * ((dx + dy) - 0.5858 * min(dx, dy))
    else:
        def h(x, y):
            return 0.0
    heap, g, par, ctr = [], {}, {}, 0
    for l, x, y, _ in srcs:
        k = (l, x, y, 8)
        g[k] = 0.0
        heap.append((h(x, y), ctr, k))
        ctr += 1
    heapq.heapify(heap)
    pops = 0
    while heap:
        pops += 1
        if pops > MAXPOP:
            return None, None
        f, _, k = heapq.heappop(heap)
        l, x, y, d = k
        gc = g[k]
        if f - h(x, y) > gc + 1e-6:
            continue
        idx = y * NX + x
        done = (l, x, y) in tset
        via_end = None
        if not done and goal_via and gc > 0 and okvb[idx] and (l, x, y) not in sset:
            done, via_end = True, goal_via
        if done:
            path = [(l, x, y)]
            while k in par:
                k = par[k]
                path.append(k[:3])
            return path[::-1], via_end
        okl = okb[l]
        for di, (dx, dy) in enumerate(DIRS):
            nx_, ny_ = x + dx, y + dy
            if nx_ < 0 or ny_ < 0 or nx_ >= NX or ny_ >= NY:
                continue
            ni = ny_ * NX + nx_
            if not okl[ni]:
                continue
            # (no corner-cutting test: obstacles are inflated with exact distances, so a diagonal step
            # between two legal cells stays legal to within 0.001 mm; the test blocked 45-degree escapes)
            c = COST[di] + (TURN if (d != 8 and d != di) else 0.0)
            if l == 1:
                c *= IN2_COST                        # In2 is the 1.8 V plane: use it only when nothing else fits
            if relaxed and penb[l][ni]:
                c += RIP_PEN
            nk = (l, nx_, ny_, di)
            ng = gc + c
            if ng < g.get(nk, 1e18):
                g[nk] = ng
                par[nk] = k
                heapq.heappush(heap, (ng + h(nx_, ny_), ctr, nk))
                ctr += 1
        if allow_via and okvb[idx]:
            for l2 in SIG:
                if l2 == l or not okb[l2][idx]:
                    continue
                nk = (l2, x, y, 8)
                ng = gc + VIA_COST
                if ng < g.get(nk, 1e18):
                    g[nk] = ng
                    par[nk] = k
                    heapq.heappush(heap, (ng + h(x, y), ctr, nk))
                    ctr += 1
    return None, None


def simplify(path):
    out, i = [], 0
    while i < len(path) - 1:
        l, x, y = path[i]
        l2, x2, y2 = path[i + 1]
        if l2 != l:
            out.append(("via", x, y))
            i += 1
            continue
        d = (x2 - x, y2 - y)
        j = i + 1
        while j + 1 < len(path) and path[j + 1][0] == l and (path[j + 1][1] - path[j][1], path[j + 1][2] - path[j][2]) == d:
            j += 1
        out.append(("seg", l, x, y, path[j][1], path[j][2]))
        i = j
    return out


def commit(net, path, via_end, pa, pb, width=None):
    w = width or wclass(net)
    parts = simplify(path)
    segs = [p for p in parts if p[0] == "seg"]
    for p in parts:
        if p[0] == "via":
            add_via(net, p[1] * RES, p[2] * RES, VB)
            continue
        _, l, x1, y1, x2, y2 = p
        ax, ay, bx, by = x1 * RES, y1 * RES, x2 * RES, y2 * RES
        if segs and p is segs[0] and pa and 0.001 < math.hypot(ax - pa[0], ay - pa[1]) < 0.2:
            add_track(net, l, pa[0], pa[1], ax, ay, w)
        if segs and p is segs[-1] and pb and 0.001 < math.hypot(bx - pb[0], by - pb[1]) < 0.2:
            add_track(net, l, bx, by, pb[0], pb[1], w)
        add_track(net, l, ax, ay, bx, by, w)
    if not segs and pa:                        # path of one cell (via right at the pad exit)
        l, x, y = path[-1]
        add_track(net, l, pa[0], pa[1], x * RES, y * RES, w)
    if via_end:
        l, x, y = path[-1]
        add_via(net, x * RES, y * RES, VB if via_end == "b" else VS)


# ------------------------------------------------------------------ net routing ---------
def next_connection(net):
    gs = groups_of(net)
    if net in PLANE:
        main = [g for g in gs if any(o.GetClass() == "PCB_VIA" for o in g)]
        others = [g for g in gs if g not in main and any(o.GetClass() == "PAD" for o in g)]
        if not others:
            return None
        mt = [t for g in main for t in terminals(g, False) if t[3] is not None and t[3].GetClass() == "PCB_VIA"]
        og = others[0]
        src = [t for t in terminals(og, False) if t[3] is not None and t[3].GetClass() == "PAD"]
        return src, mt, True
    if len(gs) <= 1:
        return None
    main = max(gs, key=len)
    mt = terminals(main, net not in NO_VIA)
    best = None
    for og in gs:
        if og is main:
            continue
        ot = terminals(og, True)
        if not ot:
            continue
        d = min(abs(a[1] - b[1]) + abs(a[2] - b[2]) for a in ot[::max(1, len(ot) // 40)] for b in mt[::4] or mt)
        if best is None or d < best[0]:
            best = (d, ot)
    if best is None:
        return None
    src = best[1]
    return src, mt, False


def endpoints(path, src, tgt):
    pa = pb = None
    for s in src:
        if (s[0], s[1], s[2]) == path[0] and s[3] is not None:
            p = s[3].GetPosition()
            pa = (tomm(p.x), tomm(p.y))
    for s in tgt:
        if (s[0], s[1], s[2]) == path[-1] and s[3] is not None:
            p = s[3].GetPosition()
            pb = (tomm(p.x), tomm(p.y))
    return pa, pb


def route_net(net):
    """Route every missing connection of net. Returns (True, None) or (False, failing connection)."""
    for _ in range(200):
        conn = next_connection(net)
        if conn is None:
            return True, None
        src, tgt, plane = conn
        if plane:
            path, ve = search(net, src, tgt, goal_via="b")
            if path is None:
                path, ve = search(net, src, tgt, goal_via="s")
        else:
            path, ve = search(net, src, tgt)
            while path is None and wclass(net) > 0.1:      # neck down power tracks before giving up
                NECK[net] = 0.15 if wclass(net) > 0.15 else 0.1
                path, ve = search(net, src, tgt)
            if net in NECK:
                W_USED[net] = NECK.pop(net)
        if path is None:
            return False, conn
        pa, pb = endpoints(path, src, tgt)
        commit(net, path, ve, pa, pb if not ve else None, width=W_USED.get(net))
        W_USED.pop(net, None)
    return False, None


def exits_hit(net, path):
    """Nets whose reserved exit lies within clearance of the relaxed path."""
    P = path_pts(net, path)
    hit = set()
    for m, caps in EXITS.items():
        if m == net:
            continue
        for (layers, x1, y1, x2, y2, rad, code) in caps:
            sel = P[np.isin(P[:, 2], layers)]
            if not len(sel):
                continue
            dx, dy = x2 - x1, y2 - y1
            L2 = dx * dx + dy * dy or 1e-12
            t = np.clip(((sel[:, 0] - x1) * dx + (sel[:, 1] - y1) * dy) / L2, 0, 1)
            d = np.hypot(sel[:, 0] - x1 - t * dx, sel[:, 1] - y1 - t * dy)
            if (d < rad + CLR + sel[:, 3] + RES).any():
                hit.add(m)
                break
    return hit


def path_pts(net, path):
    """(x, y, layer, half-width) of the path; layer changes are vias, checked on every layer at via size."""
    w = wclass(net)
    out = [(x * RES, y * RES, l, w / 2) for l, x, y in path]
    for (l1, x1, y1), (l2, x2, y2) in zip(path, path[1:]):
        if l1 != l2 and (x1, y1) == (x2, y2):
            out += [(x1 * RES, y1 * RES, l, VB[0] / 2) for l in range(3)]
    return np.array(out)


def blockers(net, path):
    """Routed nets whose copper is within clearance of the relaxed path (vias at full via size)."""
    P = path_pts(net, path)
    hit = set()
    for m, objs in ROUTED.items():
        if m == net:
            continue
        for o in objs:
            if o.GetClass() == "PCB_VIA":
                p = o.GetPosition()
                d = np.hypot(P[:, 0] - tomm(p.x), P[:, 1] - tomm(p.y))
                if (d < tomm(o.GetWidth(pcbnew.F_Cu)) / 2 + CLR + P[:, 3] + RES).any():
                    hit.add(m)
                    break
            else:
                l = LAYERS.index(o.GetLayer())
                s, e = o.GetStart(), o.GetEnd()
                x1, y1, x2, y2 = tomm(s.x), tomm(s.y), tomm(e.x), tomm(e.y)
                sel = P[P[:, 2] == l]
                if not len(sel):
                    continue
                dx, dy = x2 - x1, y2 - y1
                L2 = dx * dx + dy * dy or 1e-12
                t = np.clip(((sel[:, 0] - x1) * dx + (sel[:, 1] - y1) * dy) / L2, 0, 1)
                d = np.hypot(sel[:, 0] - x1 - t * dx, sel[:, 1] - y1 - t * dy)
                if (d < tomm(o.GetWidth()) / 2 + CLR + sel[:, 3] + RES).any():
                    hit.add(m)
                    break
    return hit


# ------------------------------------------------------------------ setup steps ---------
def exposed_pad_vias():
    n = 0
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() not in PLANE or not has_copper(p) or is_tht(p):
                continue
            x0, y0, x1, y1 = pad_rect(p)
            if min(x1 - x0, y1 - y0) < 2.0:
                continue
            k = max(1, int((x1 - x0) // 1.3))
            j = max(1, int((y1 - y0) // 1.3))
            for a in range(k):
                for b in range(j):
                    add_via(p.GetNetname(), x0 + (a + 0.5) * (x1 - x0) / k, y0 + (b + 0.5) * (y1 - y0) / j, VB, fixed=True)
                    n += 1
    print("exposed-pad vias:", n, flush=True)


EXITS = collections.defaultdict(list)       # net -> reserved exit capsules (released when routed)
GBASE = None


def refresh():
    """GF = fixed obstacles + exits of nets not yet routed; GA = GF + routed copper."""
    global GF, GA
    GF = GBASE.copy()
    for n, caps in EXITS.items():
        for c in caps:
            GF.capsule(*c)
    GA = rebuild()


def reserve_exits(nets):
    global GA
    ok = no = 0
    for net in nets:
        code, w = NETCODE[net], wclass(net)
        for p in items_of(net):
            if p.GetClass() != "PAD" or is_tht(p):
                continue
            if not p.GetParentFootprint().GetReference().startswith(("U", "X", "D", "PD")):
                continue                              # passives have room around them
            x0, y0, x1, y1 = pad_rect(p)
            if min(x1 - x0, y1 - y0) > 1.5:
                continue
            f = p.GetParentFootprint()
            l = 2 if f.IsFlipped() else 0
            pw, ph = x1 - x0, y1 - y0
            px, py = tomm(p.GetPosition().x), tomm(p.GetPosition().y)
            fx, fy = tomm(f.GetPosition().x), tomm(f.GetPosition().y)
            fb = f.GetBoundingBox(False)
            if abs(pw - ph) >= 0.05:
                if pw > ph:
                    a = (1 if px >= fx else -1, 0)
                    cands = [a, (-a[0], 0), (0, 1), (0, -1)]
                else:
                    a = (0, 1 if py >= fy else -1)
                    cands = [a, (0, -a[1]), (1, 0), (-1, 0)]
            else:
                ed = [(px - tomm(fb.GetLeft()), (-1, 0)), (tomm(fb.GetRight()) - px, (1, 0)),
                      (py - tomm(fb.GetTop()), (0, -1)), (tomm(fb.GetBottom()) - py, (0, 1))]
                cands = [d for _, d in sorted(ed)]
            for ux, uy in cands:
                half = (pw if ux else ph) / 2
                L = half + STUB
                free = True
                for i in range(1, int(L / RES) + 1):
                    xx, yy = cx(px + ux * i * RES), cx(py + uy * i * RES)
                    if not (0 <= xx < NX and 0 <= yy < NY) or GA.t[w][l, yy, xx] not in (0, code):
                        free = False
                        break
                if free:
                    cap = ([l], px, py, px + ux * L, py + uy * L, w / 2, code)
                    for g in (GF, GA):
                        g.capsule(*cap)
                    EXITS[net].append(cap)
                    ok += 1
                    break
            else:
                no += 1
    print("exits reserved %d, no free exit %d" % (ok, no), flush=True)


def unrouted():
    out = []
    for n in NETCODE:
        if n == "" or n.startswith("unconnected"):
            continue
        gs = groups_of(n)
        if n in PLANE:
            if any(not any(o.GetClass() == "PCB_VIA" for o in g) and any(o.GetClass() == "PAD" for o in g) for g in gs):
                out.append(n)
        elif len(gs) > 1:
            out.append(n)
    return out


def hpwl(n):
    pts = [(tomm(o.GetPosition().x), tomm(o.GetPosition().y)) for o in items_of(n) if o.GetClass() == "PAD"]
    if not pts:
        return 0
    xs, ys = zip(*pts)
    return max(xs) - min(xs) + max(ys) - min(ys)


def main():
    global GA
    global GBASE
    T = time.time()
    GF.__init__()
    rebuild_fixed_from_board()
    if ADOPT:
        for t in list(board.GetTracks()):
            if adoptable(t):
                ROUTED[t.GetNetname()].append(t)
    GA = rebuild() if ADOPT else GF.copy()
    if not ADOPT:
        exposed_pad_vias()
    GBASE = GF.copy()
    todo = unrouted()
    reserve_exits(todo)                      # exits for every net, so plane vias stay out of signal lanes
    if "--hard-only" in sys.argv:             # RF chain, crystals and GND / +1V8 fan-out only
        todo = [n for n in todo if n in RF_NETS or n in NO_VIA or n in PLANE]
    order = sorted(todo, key=lambda n: (-2 if n in RF_NETS else -1 if n in NO_VIA else 0 if n in PLANE else 1 if n in POWER else 2, hpwl(n)))
    if "--first" in sys.argv:                 # route these before everything else (buried pads)
        first = sys.argv[sys.argv.index("--first") + 1].split(",")
        order = [n for n in first if n in order] + [n for n in order if n not in first]
    if os.environ.get("SEED"):                # repeated leftover passes: a different order finds other rip-ups
        __import__("random").Random(int(os.environ["SEED"])).shuffle(order)
    print("nets to route:", len(order), flush=True)
    PROTECT.update(RF_NETS | NO_VIA | PLANE)
    queue = collections.deque(order)
    tries, ripped, failed = collections.Counter(), collections.Counter(), []
    CKPT = os.path.join(os.path.dirname(BOARD), "route_checkpoint.kicad_pcb")
    done_n = 0
    while queue:
        net = queue.popleft()
        ok, conn = route_net(net)
        done_n += 1
        if done_n % 10 == 0:                  # checkpoint copy so a stopped run loses nothing
            pcbnew.SaveBoard(CKPT, board, True)
        if ok:
            print("  ok   %-30s (%.0fs)" % (net[-30:], time.time() - T), flush=True)
            if EXITS.pop(net, None):
                refresh()
            continue
        tries[net] += 1
        if conn is None or tries[net] > 6:
            failed.append(net)
            print("  FAIL %-30s (%.0fs)" % (net[-30:], time.time() - T), flush=True)
            continue
        src, tgt, plane = conn
        path, _ = search(net, src, tgt, goal_via="b" if plane else None, relaxed=True)
        hit = {m for m in blockers(net, path) if ripped[m] < 3 and m not in PROTECT} if path else set()
        if sum(ripped.values()) >= RIP_BUDGET:
            hit = set()
        soft = exits_hit(net, path) if path else set()
        if not hit and not soft:
            failed.append(net)
            print("  FAIL %-30s no rip-up path (%.0fs) relaxed path %s, raw blockers %s, conn %s->%s" % (
                net[-30:], time.time() - T, len(path) if path else None, sorted(blockers(net, path)) if path else "-",
                src[0][:3] if src else "?", tgt[0][:3] if tgt else "?"), flush=True)
            continue
        for m in soft:                        # reserved exits are soft: release the ones in the way
            EXITS.pop(m, None)
        # all or nothing: rip the blockers, route this net, re-route every blocker; if anything fails put
        # the old copper back, so a pass can never leave more nets open than it started with
        saved = {m: list(ROUTED.get(m, [])) for m in hit | {net}}
        for m in hit:
            rip(m)
            ripped[m] += 1
        refresh()
        good = route_net(net)[0]
        if good:
            for m in sorted(hit, key=hpwl):
                if not route_net(m)[0]:
                    good = False
                    break
        if good:
            for m in hit | {net}:
                EXITS.pop(m, None)
            refresh()
            print("  ok   %-30s by rip-up of %s (%.0fs)" % (net[-30:], sorted(x[-18:] for x in hit), time.time() - T), flush=True)
            continue
        for m in hit | {net}:
            rip(m)
        for m, objs in saved.items():
            for o in objs:
                board.Add(o)
                ROUTED[m].append(o)
        refresh()
        failed.append(net)
        print("  FAIL %-30s rip-up of %s undone (%.0fs)" % (net[-30:], sorted(x[-18:] for x in hit), time.time() - T), flush=True)
    for t in board.GetTracks():               # everything routed here is fixed for later stages
        t.SetLocked(True)
    pcbnew.SaveBoard(BOARD, board, True)
    left = unrouted()
    print("DONE %.0fs; nets still open: %d %s" % (time.time() - T, len(left), left), flush=True)
    os._exit(0)


# ------------------------------------------------------------------ negotiated congestion (PathFinder) --
class Claims:
    """How many routed nets claim each cell (inflated like obstacles), per track class and for vias."""
    def __init__(self):
        self.t = {w: np.zeros((3, NY, NX), np.int16) for w in WCLS}
        self.vb = np.zeros((3, NY, NX), np.int16)

    def kinds(self):
        return [(self.t[w], CLR + w / 2) for w in WCLS] + [(self.vb, VB_EXTRA)]

    def capsule(self, layers, x1, y1, x2, y2, rad, d):
        for arr, extra in self.kinds():
            R = rad + extra
            ix0 = max(0, int(math.floor((min(x1, x2) - R) / RES)))
            ix1 = min(NX, int(math.ceil((max(x1, x2) + R) / RES)) + 1)
            iy0 = max(0, int(math.floor((min(y1, y2) - R) / RES)))
            iy1 = min(NY, int(math.ceil((max(y1, y2) + R) / RES)) + 1)
            if ix0 >= ix1 or iy0 >= iy1:
                continue
            X_, Y_ = np.meshgrid(np.arange(ix0, ix1) * RES, np.arange(iy0, iy1) * RES)
            dx, dy = x2 - x1, y2 - y1
            L2 = dx * dx + dy * dy
            if L2 == 0:
                d2 = (X_ - x1) ** 2 + (Y_ - y1) ** 2
            else:
                t = np.clip(((X_ - x1) * dx + (Y_ - y1) * dy) / L2, 0, 1)
                d2 = (X_ - x1 - t * dx) ** 2 + (Y_ - y1 - t * dy) ** 2
            m = (d2 <= R * R).astype(np.int16) * d
            for l in layers:
                arr[l, iy0:iy1, ix0:ix1] += m


CL = None
HIST = None
PRES = 1.0


def claim_net(net, d):
    for o in ROUTED.get(net, []):
        if o.GetClass() == "PCB_VIA":
            p = o.GetPosition()
            x, y = tomm(p.x), tomm(p.y)
            CL.capsule([0, 1, 2], x, y, x, y, tomm(o.GetWidth(pcbnew.F_Cu)) / 2, d)
        elif o.GetLayer() in LAYERS:
            s_, e_ = o.GetStart(), o.GetEnd()
            CL.capsule([LAYERS.index(o.GetLayer())], tomm(s_.x), tomm(s_.y), tomm(e_.x), tomm(e_.y), tomm(o.GetWidth()) / 2, d)


def centre_cells(net):
    out = []
    for o in ROUTED.get(net, []):
        if o.GetClass() == "PCB_VIA":
            p = o.GetPosition()
            out.append(("v", 0, cx(tomm(p.x)), cx(tomm(p.y)), 0.1))
        elif o.GetLayer() in LAYERS:
            s_, e_ = o.GetStart(), o.GetEnd()
            x1, y1, x2, y2 = tomm(s_.x), tomm(s_.y), tomm(e_.x), tomm(e_.y)
            n = max(1, int(math.hypot(x2 - x1, y2 - y1) / RES))
            w = min(WCLS, key=lambda c: abs(c - tomm(o.GetWidth())))
            for i in range(n + 1):
                out.append(("t", LAYERS.index(o.GetLayer()), cx(x1 + (x2 - x1) * i / n), cx(y1 + (y2 - y1) * i / n), w))
    return out


def conflicted(net):
    """Cells where this net's copper sits inside another net's claim (overlap still being negotiated)."""
    claim_net(net, -1)
    bad = []
    for k, l, x, y, w in centre_cells(net):
        if not (0 <= x < NX and 0 <= y < NY):
            continue
        if k == "v":
            if (CL.vb[:, y, x] > 0).any():
                bad.append((0, x, y))
        elif CL.t[w][l, y, x] > 0:
            bad.append((l, x, y))
    claim_net(net, +1)
    return bad


def search_pf(net, srcs, tgts):
    code = NETCODE[net]
    w = wclass(net)
    core = own_core(net)
    ok = (GF.t[w] == 0) | (GF.t[w] == code) | core
    okv = ((GF.vb == 0) | (GF.vb == code)).all(axis=0) & ~NOV_B
    pen = (PRES * CL.t[w].astype(np.float32) * (1.0 + HIST)).astype(np.float32)
    vpen = PRES * 4.0 * CL.vb.max(axis=0).astype(np.float32)
    okb = [ok[l].tobytes() for l in range(3)]
    penl = [pen[l].ravel().tolist() for l in range(3)]
    vpl = vpen.ravel().tolist()
    okvb = okv.tobytes()
    allow_via = net not in NO_VIA
    tset = {(t[0], t[1], t[2]) for t in tgts}
    txs = [t[1] for t in tset]
    tys = [t[2] for t in tset]
    bx0, bx1, by0, by1 = min(txs), max(txs), min(tys), max(tys)

    def h(x, y):
        dx = max(bx0 - x, 0, x - bx1)
        dy = max(by0 - y, 0, y - by1)
        return HW * ((dx + dy) - 0.5858 * min(dx, dy))
    heap, g, par, ctr = [], {}, {}, 0
    for l, x, y, _ in srcs:
        k = (l, x, y, 8)
        g[k] = 0.0
        heap.append((h(x, y), ctr, k))
        ctr += 1
    heapq.heapify(heap)
    pops = 0
    while heap:
        pops += 1
        if pops > MAXPOP:
            return None
        f, _, k = heapq.heappop(heap)
        l, x, y, d = k
        gc = g[k]
        if f - h(x, y) > gc + 1e-6:
            continue
        if (l, x, y) in tset:
            path = [(l, x, y)]
            while k in par:
                k = par[k]
                path.append(k[:3])
            return path[::-1]
        idx = y * NX + x
        okl = okb[l]
        pl = penl[l]
        for di, (dx, dy) in enumerate(DIRS):
            nx_, ny_ = x + dx, y + dy
            if nx_ < 0 or ny_ < 0 or nx_ >= NX or ny_ >= NY:
                continue
            ni = ny_ * NX + nx_
            if not okl[ni]:
                continue
            c = COST[di] * (3.0 if l == 1 else 1.0) + (TURN if (d != 8 and d != di) else 0.0) + pl[ni]
            nk = (l, nx_, ny_, di)
            ng = gc + c
            if ng < g.get(nk, 1e18):
                g[nk] = ng
                par[nk] = k
                heapq.heappush(heap, (ng + h(nx_, ny_), ctr, nk))
                ctr += 1
        if allow_via and okvb[idx]:
            for l2 in SIG:
                if l2 == l or not okb[l2][idx]:
                    continue
                nk = (l2, x, y, 8)
                ng = gc + VIA_COST + vpl[idx]
                if ng < g.get(nk, 1e18):
                    g[nk] = ng
                    par[nk] = k
                    heapq.heappush(heap, (ng + h(x, y), ctr, nk))
                    ctr += 1
    return None


def route_net_pf(net):
    for _ in range(200):
        conn = next_connection(net)
        if conn is None:
            return True
        src, tgt, plane = conn
        if plane:
            path, ve = search(net, src, tgt, goal_via="b")
        else:
            path, ve = search_pf(net, src, tgt), None
            while path is None and wclass(net) > 0.1:      # neck down power tracks, as route_net does
                NECK[net] = 0.15 if wclass(net) > 0.15 else 0.1
                path = search_pf(net, src, tgt)
            if net in NECK:
                W_USED[net] = NECK.pop(net)
        if path is None:
            return False
        pa, pb = endpoints(path, src, tgt)
        commit(net, path, ve, pa, pb if not ve else None, width=W_USED.get(net))
        W_USED.pop(net, None)
    return False


def pf_main():
    global CL, HIST, PRES, GA, GBASE
    T = time.time()
    GF.__init__()
    rebuild_fixed_from_board()                # fixed: pads, RF / crystal / plane fan-out, U4 stubs (adopt mode)
    for t in list(board.GetTracks()):
        if adoptable(t):
            ROUTED[t.GetNetname()].append(t)
    GA = rebuild()
    GBASE = GF.copy()
    PROTECT.update(RF_NETS | NO_VIA | (set() if os.environ.get("PF_PLANES") else PLANE))
    CL = Claims()
    HIST = np.zeros((3, NY, NX), np.float32)
    nets = sorted({n for n in NETCODE if n and not n.startswith("unconnected") and n not in PROTECT
                   and len([o for o in items_of(n) if o.GetClass() == "PAD"]) >= 2}, key=hpwl)
    if os.environ.get("PF_BOX"):              # negotiate only open nets + nets with a pad in this box (mm)
        x0, y0, x1, y1 = map(float, os.environ["PF_BOX"].split(","))
        def inbox(n):
            return any(o.GetClass() == "PAD" and x0 <= tomm(o.GetPosition().x) <= x1 and y0 <= tomm(o.GetPosition().y) <= y1
                       for o in items_of(n))
        nets = [n for n in nets if len(groups_of(n)) > 1 or inbox(n)]
    for n in list(ROUTED):                    # copper of nets not negotiated here is a fixed obstacle
        if n not in nets:
            for o in ROUTED[n]:
                stamp_obj(GF, o)
    GBASE = GF.copy()
    GA = rebuild()
    open0 = sum(len(groups_of(n)) > 1 for n in nets)
    for n in nets:
        claim_net(n, +1)
    print("PF: %d nets, start %.0fs" % (len(nets), time.time() - T), flush=True)
    ck = os.path.join(os.path.dirname(BOARD), "route_checkpoint.kicad_pcb")
    for it in range(14):
        todo = []
        for n in nets:
            bad = conflicted(n)
            if bad or len(groups_of(n)) > 1:
                todo.append(n)
                for (l, x, y) in bad:
                    HIST[l, max(0, y - 2):y + 3, max(0, x - 2):x + 3] += 0.5
        print("PF iter %d: %d nets to (re)route, pres %.1f (%.0fs)" % (it, len(todo), PRES, time.time() - T), flush=True)
        if not todo:
            break
        for n in todo:
            claim_net(n, -1)
            rip(n)
            if n in PLANE:
                GA = rebuild()                    # plane fan-out uses the strict search against current copper
            ok = route_net_pf(n)
            claim_net(n, +1)
            if not ok:
                print("   unroutable even with sharing: %s" % n, flush=True)
        pcbnew.SaveBoard(ck, board, True)
        PRES *= 1.8
    for t in board.GetTracks():
        t.SetLocked(True)
    left = [n for n in nets if conflicted(n) or len(groups_of(n)) > 1]
    overlap = [n for n in nets if conflicted(n)]
    # only a legal result (no shared copper) that leaves fewer nets open replaces the board
    out = BOARD if not overlap and len(left) < open0 else os.path.join(os.path.dirname(BOARD), "route_pf_result.kicad_pcb")
    pcbnew.SaveBoard(out, board, True)
    print("saved to", out, "(open before: %d)" % open0, flush=True)
    print("PF DONE %.0fs; nets with overlap or open: %d %s" % (time.time() - T, len(left), left), flush=True)
    os._exit(0)


if __name__ == "__main__":
    pf_main() if "--pf" in sys.argv else main()
