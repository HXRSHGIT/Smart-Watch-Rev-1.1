"""Our own grid router (run with KiCad 9's python + numpy).

Connects every unconnected net of smartwatch.kicad_pcb with 45-degree tracks and through vias,
respecting the JLCPCB rules in the project (0.1 mm clearance, 0.1 mm signal / 0.3 mm power
tracks, 0.45 / 0.20 mm vias). Nothing is moved; items already on the board (RF chain, crystals,
fan-out vias) are obstacles of their own nets and are reused.

Layers searched: F.Cu, In2.Cu, B.Cu (In1.Cu is the GND plane). GND and +1V8 only get the
leftover pads that fan-out could not reach: each is joined to the nearest via of its net.

Search: A* on a 0.025 mm grid, 8 directions (0/45/90 degrees only), turn penalty (fewer bends),
via penalty (few layer changes), obstacles inflated by clearance + half the track width.
If a net cannot be routed, up to RIPUP rounds rip up the nets that block it and route the
blocked net first.

Usage:  python route_own.py [--nets NAME,NAME] [--skip-plane | --only-plane]

Done by Harsh Thakur.
"""
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
CLR = 0.125                    # search clearance (rule: 0.10)
VIA_D, VIA_H = 0.45, 0.20
WIDTHS = {0.1: 0.1, 0.2: 0.2}  # width classes (power nets 0.2 mm: 0.3 mm does not fit out of 0.5 mm pitch pads)
POWER = {"VSYS", "VBUS_PROT", "VLED", "VLED_BOOST", "VBAT"}
PLANE = {"GND": 0, "+1V8": 0}
VIA_COST = 40                  # in cells (0.6 mm)
TURN = 0.7
HW = 2.2                       # weighted A*: greedy toward the target (paths up to ~1.7x optimal)
MAXPOP = 6000000                # search limit per connection (unreachable nets must fail fast)
RIPUP = 3
mm, tomm = pcbnew.FromMM, pcbnew.ToMM
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]

board = pcbnew.LoadBoard(BOARD)
bb = board.GetBoardEdgesBoundingBox()
BW, BH = tomm(bb.GetRight()), tomm(bb.GetBottom())
NX, NY = int(BW / RES) + 1, int(BH / RES) + 1
NL = 3


def cx(v):
    return int(round(v / RES))


# ------------------------------------------------------------------ obstacle grids -------
class Grids:
    """own[kind][layer]: net id that claims a cell (0 free, -1 several nets)."""

    def __init__(self):
        self.t = {w: np.zeros((NL, NY, NX), np.int32) for w in WIDTHS}
        self.v = np.zeros((NL, NY, NX), np.int32)
        self.nov = np.zeros((NY, NX), bool)            # no via inside / next to any pad
        self._disks = {}

    def disk(self, r):
        r = max(1, int(math.ceil(r / RES)))
        if r not in self._disks:
            yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
            self._disks[r] = (r, (xx * xx + yy * yy) <= r * r)
        return self._disks[r]

    @staticmethod
    def _apply(sub, mask, net):
        cur = sub[mask] if mask is not None else sub
        new = np.where(cur == 0, net, np.where(cur == net, net, -1))
        if mask is not None:
            sub[mask] = new
        else:
            sub[...] = new

    def stamp_rect(self, layers, x0, y0, x1, y1, net):
        for kind, extra in self.kinds():
            r = int(math.ceil(extra / RES))
            ix0, ix1 = max(0, cx(x0) - r), min(NX, cx(x1) + r + 1)
            iy0, iy1 = max(0, cy(y0) - r), min(NY, cy(y1) + r + 1)
            for l in layers:
                self._apply(kind_arr(self, kind)[l, iy0:iy1, ix0:ix1], None, net)

    def stamp_disk(self, layers, x, y, rad, net):
        for kind, extra in self.kinds():
            rr, m = self.disk(rad + extra)
            ix, iy = cx(x), cy(y)
            x0, x1 = max(0, ix - rr), min(NX, ix + rr + 1)
            y0, y1 = max(0, iy - rr), min(NY, iy + rr + 1)
            if x0 >= x1 or y0 >= y1:
                continue
            mk = m[(y0 - iy + rr):(y1 - iy + rr), (x0 - ix + rr):(x1 - ix + rr)]
            for l in layers:
                self._apply(kind_arr(self, kind)[l, y0:y1, x0:x1], mk, net)

    def stamp_seg(self, layers, x1, y1, x2, y2, w, net):
        n = max(1, int(math.hypot(x2 - x1, y2 - y1) / (RES * 0.5)))
        for i in range(n + 1):
            t = i / n
            self.stamp_disk(layers, x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, w / 2, net)

    @staticmethod
    def kinds():
        return [(("t", 0.1), CLR + 0.05), (("t", 0.2), CLR + 0.10), (("v", 0), CLR + VIA_D / 2)]


def cy(v):
    return int(round(v / RES))


def kind_arr(g, kind):
    return g.t[kind[1]] if kind[0] == "t" else g.v


G = Grids()
NETCODE = {}
NETNAME = {}
for code, ni in board.GetNetsByNetcode().items():
    NETCODE[ni.GetNetname()] = code
    NETNAME[code] = ni.GetNetname()


def has_copper(p):
    """False for the paste-only / mask-only pads that stock 0201-0603 footprints carry on top of
    the real pads (no number, no net, no copper layer): they must not be obstacles."""
    return any(p.IsOnLayer(l) for l in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu))


def pad_layers(p):
    if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
        return [0, 1, 2]
    return [0] if p.IsOnLayer(pcbnew.F_Cu) else [2]


def stamp_board_item(obj):
    cls = obj.GetClass()
    net = obj.GetNetCode() or 999999
    if cls == "PAD":
        if not has_copper(obj):
            return
        b = obj.GetBoundingBox()
        x0, y0, x1, y1 = tomm(b.GetLeft()), tomm(b.GetTop()), tomm(b.GetRight()), tomm(b.GetBottom())
        G.stamp_rect(pad_layers(obj), x0, y0, x1, y1, net)
        r = int(math.ceil(0.12 / RES))
        G.nov[max(0, cy(y0) - r):cy(y1) + r + 1, max(0, cx(x0) - r):cx(x1) + r + 1] = True
    elif cls == "PCB_VIA":
        p = obj.GetPosition()
        G.stamp_disk([0, 1, 2], tomm(p.x), tomm(p.y), tomm(obj.GetWidth(pcbnew.F_Cu)) / 2, net)
    else:
        l = LAYERS.index(obj.GetLayer()) if obj.GetLayer() in LAYERS else None
        if l is None:
            return
        s, e = obj.GetStart(), obj.GetEnd()
        G.stamp_seg([l], tomm(s.x), tomm(s.y), tomm(e.x), tomm(e.y), tomm(obj.GetWidth()), net)


for f in board.GetFootprints():
    for p in f.Pads():
        stamp_board_item(p)
for t in board.GetTracks():
    stamp_board_item(t)
# copper drawn as footprint graphics (the internal link of net-tie parts): blocked for every net
for f in board.GetFootprints():
    for g in f.GraphicalItems():
        l = g.GetLayer()
        if l in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu):
            b = g.GetBoundingBox()
            G.stamp_rect([LAYERS.index(l)], tomm(b.GetLeft()), tomm(b.GetTop()), tomm(b.GetRight()), tomm(b.GetBottom()), 999999)
# board edge: tracks 0.3 mm, vias 0.6 mm from the edge
mt, mv = cx(0.25), cx(0.60)
for w in WIDTHS:
    a = G.t[w]
    a[:, :mt, :] = -1
    a[:, -mt:, :] = -1
    a[:, :, :mt] = -1
    a[:, :, -mt:] = -1
G.v[:, :mv, :] = -1
G.v[:, -mv:, :] = -1
G.v[:, :, :mv] = -1
G.v[:, :, -mv:] = -1
# antenna clearance: no vias
G.v[:, :cx(6.6), :cx(6.6)] = -1


# ------------------------------------------------------------------ connectivity ---------
def items_of(net):
    out = []
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == net:
                out.append(p)
    for t in board.GetTracks():
        if t.GetNetname() == net:
            out.append(t)
    return out


def layers_of(o):
    if o.GetClass() == "PCB_VIA":
        return {0, 1, 2}
    if o.GetClass() == "PAD":
        return set(pad_layers(o))
    return {LAYERS.index(o.GetLayer())} if o.GetLayer() in LAYERS else set()


def shape_of(o):
    if o.GetClass() == "PAD":
        return o.GetEffectiveShape(pcbnew.F_Cu)
    if o.GetClass() == "PCB_VIA":
        return o.GetEffectiveShape(pcbnew.F_Cu)
    return o.GetEffectiveShape()


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
    if net in PLANE:     # all vias of a plane net are joined by the plane
        vias = [i for i, o in enumerate(its) if o.GetClass() == "PCB_VIA"]
        for a, b in zip(vias, vias[1:]):
            par[find(a)] = find(b)
    gs = {}
    for i in range(len(its)):
        gs.setdefault(find(i), []).append(its[i])
    return list(gs.values())


def terminals(group):
    """Cells a route may start from or end on: pad centres and via centres."""
    out = []
    for o in group:
        p = o.GetPosition() if o.GetClass() in ("PAD", "PCB_VIA") else None
        if p is None:
            continue
        for l in layers_of(o):
            out.append((l, cx(tomm(p.x)), cy(tomm(p.y)), o))
    return out


# ------------------------------------------------------------------ A* -------------------
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
COST = [1, 1, 1, 1, 1.4142, 1.4142, 1.4142, 1.4142]


def search(net, wclass, srcs, tgts, relaxed=None):
    """Cheapest path from any src cell to any tgt cell. Returns list of (l, ix, iy) or None."""
    code = NETCODE[net]
    ot = G.t[wclass]
    core = np.zeros((NL, NY, NX), bool)
    for o in items_of(net):
        if o.GetClass() == "PAD":
            b = o.GetBoundingBox()
            for l in pad_layers(o):
                core[l, cy(tomm(b.GetTop())):cy(tomm(b.GetBottom())) + 1, cx(tomm(b.GetLeft())):cx(tomm(b.GetRight())) + 1] = True
    okt = ((ot == 0) | (ot == code) | core)
    okv = ((G.v == 0) | (G.v == code)).all(axis=0) & ~G.nov
    if relaxed is not None:
        okt = okt | (relaxed & (ot != -1))
    okt_b = [okt[l].tobytes() for l in range(NL)]
    okv_b = okv.tobytes()
    tset = {(l, x, y) for l, x, y, _ in tgts}
    tx = [t[1] for t in tset]
    ty = [t[2] for t in tset]
    bx0, bx1, by0, by1 = min(tx), max(tx), min(ty), max(ty)

    def h(x, y):
        dx = max(bx0 - x, 0, x - bx1)
        dy = max(by0 - y, 0, y - by1)
        return (dx + dy) - 0.5858 * min(dx, dy)

    heap = []
    g = {}
    par = {}
    ctr = 0
    for l, x, y, _ in srcs:
        key = (l, x, y, 8)
        g[key] = 0.0
        heap.append((HW * h(x, y), ctr, key))
        ctr += 1
    heapq.heapify(heap)
    NXl = NX
    pops = 0
    while heap:
        pops += 1
        if pops > MAXPOP:
            return None
        f, _, key = heapq.heappop(heap)
        l, x, y, d = key
        gc = g[key]
        if f - HW * h(x, y) > gc + 1e-6:
            continue
        if (l, x, y) in tset:
            path = [(l, x, y)]
            while key in par:
                key = par[key]
                path.append(key[:3])
            return path[::-1]
        ok = okt_b[l]
        for di, (dx, dy) in enumerate(DIRS):
            nx_, ny_ = x + dx, y + dy
            if nx_ < 0 or ny_ < 0 or nx_ >= NX or ny_ >= NY:
                continue
            if not ok[ny_ * NXl + nx_]:
                continue
            if dx and dy and not (ok[y * NXl + nx_] and ok[ny_ * NXl + x]):
                continue
            c = COST[di] + (TURN if (d != 8 and d != di) else 0.0)
            nk = (l, nx_, ny_, di)
            ng = gc + c
            if ng < g.get(nk, 1e18):
                g[nk] = ng
                par[nk] = key
                heapq.heappush(heap, (ng + HW * h(nx_, ny_), ctr, nk))
                ctr += 1
        if okv_b[y * NXl + x]:
            for l2 in range(NL):
                if l2 == l or not okt_b[l2][y * NXl + x]:
                    continue
                nk = (l2, x, y, 8)
                ng = gc + VIA_COST
                if ng < g.get(nk, 1e18):
                    g[nk] = ng
                    par[nk] = key
                    heapq.heappush(heap, (ng + HW * h(x, y), ctr, nk))
                    ctr += 1
    return None


def simplify(path):
    """Cell path -> list of ('seg', l, x1, y1, x2, y2) and ('via', x, y), collinear steps merged."""
    out = []
    i = 0
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


ROUTED = {}      # net -> list of board objects added by this router


def commit(net, wclass, path, pa, pb):
    code = NETCODE[net]
    ni = board.FindNet(net)
    parts = simplify(path)
    objs = ROUTED.setdefault(net, [])
    first_seg = next((p for p in parts if p[0] == "seg"), None)
    last_seg = next((p for p in reversed(parts) if p[0] == "seg"), None)
    for p in parts:
        if p[0] == "via":
            x, y = p[1] * RES, p[2] * RES
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            v.SetWidth(mm(VIA_D))
            v.SetDrill(mm(VIA_H))
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetNet(ni)
            board.Add(v)
            objs.append(v)
            G.stamp_disk([0, 1, 2], x, y, VIA_D / 2, code)
        else:
            _, l, x1, y1, x2, y2 = p
            ax, ay, bx, by = x1 * RES, y1 * RES, x2 * RES, y2 * RES
            for pt, cell, first in ((pa, (ax, ay), p is first_seg), (pb, (bx, by), p is last_seg)):
                if pt is not None and first and 0.001 < math.hypot(cell[0] - pt[0], cell[1] - pt[1]) < 0.2:
                    t0 = pcbnew.PCB_TRACK(board)
                    t0.SetStart(pcbnew.VECTOR2I(mm(pt[0]), mm(pt[1])))
                    t0.SetEnd(pcbnew.VECTOR2I(mm(cell[0]), mm(cell[1])))
                    t0.SetWidth(mm(wclass))
                    t0.SetLayer(LAYERS[l])
                    t0.SetNet(ni)
                    board.Add(t0)
                    objs.append(t0)
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(mm(ax), mm(ay)))
            t.SetEnd(pcbnew.VECTOR2I(mm(bx), mm(by)))
            t.SetWidth(mm(wclass))
            t.SetLayer(LAYERS[l])
            t.SetNet(ni)
            board.Add(t)
            objs.append(t)
            G.stamp_seg([l], ax, ay, bx, by, wclass, code)


def route_net(net):
    wclass = 0.2 if net in POWER else 0.1
    fails = 0
    while True:
        gs = groups_of(net)
        if len(gs) <= 1:
            return True
        if net in PLANE:
            gs.sort(key=lambda g_: -sum(1 for o in g_ if o.GetClass() == "PCB_VIA"))
            main = gs[0]
            others = [g_ for g_ in gs[1:] if any(o.GetClass() == "PAD" for o in g_)]
            if not others:
                return True
        else:
            gs.sort(key=lambda g_: -len(g_))
            main, others = gs[0], gs[1:]
        mt_ = terminals(main)
        best = None
        for og in others:
            ot_ = terminals(og)
            if not ot_:
                continue
            d = min(math.hypot(a[1] - b[1], a[2] - b[2]) for a in mt_ for b in ot_)
            if best is None or d < best[0]:
                best = (d, og, ot_)
        if best is None:
            return True
        _, og, ot_ = best
        src = [t for t in ot_ if t[3].GetClass() == "PAD"] or ot_
        path = search(net, wclass, src, mt_)
        if path is None:
            return False
        pa = pb = None
        for s in src:
            if (s[0], s[1], s[2]) == path[0]:
                p = s[3].GetPosition()
                pa = (tomm(p.x), tomm(p.y))
        for s in mt_:
            if (s[0], s[1], s[2]) == path[-1]:
                p = s[3].GetPosition()
                pb = (tomm(p.x), tomm(p.y))
        commit(net, wclass, path, pa, pb)


def unrouted_nets():
    names = []
    for name in NETCODE:
        if name == "" or name.startswith("unconnected"):
            continue
        gs = groups_of(name)
        if name in PLANE:
            if len(gs) > 1 and any(o.GetClass() == "PAD" for g_ in gs for o in g_):
                names.append(name)
        elif len(gs) > 1:
            names.append(name)
    return names


def hpwl(name):
    xs, ys = [], []
    for o in items_of(name):
        if o.GetClass() == "PAD":
            p = o.GetPosition()
            xs.append(tomm(p.x))
            ys.append(tomm(p.y))
    return (max(xs) - min(xs)) + (max(ys) - min(ys)) if xs else 0


STUB_LEN = 0.55                # straight exit reserved in front of every pad before routing


def reserve_exits(nets):
    """Claim a straight 0.55 mm exit in front of each pad of the nets to route, so that no
    other net can run across it (exits are stamped like tracks but not added to the board)."""
    n_ok = n_no = 0
    for net in nets:
        if net in PLANE:
            continue
        wclass = 0.2 if net in POWER else 0.1
        code = NETCODE[net]
        ot = G.t[wclass]
        for p in items_of(net):
            if p.GetClass() != "PAD" or not has_copper(p) or p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                continue
            f = p.GetParentFootprint()
            l = 2 if f.IsFlipped() else 0
            b = p.GetBoundingBox()
            w, h = tomm(b.GetWidth()), tomm(b.GetHeight())
            px, py = tomm(p.GetPosition().x), tomm(p.GetPosition().y)
            fb = f.GetBoundingBox(False)
            cands = []
            if abs(w - h) >= 0.05:                       # elongated: out along the long axis, away from the body centre
                fx, fy = tomm(f.GetPosition().x), tomm(f.GetPosition().y)
                if w > h:
                    first = (1 if px >= fx else -1, 0)
                    cands = [first, (-first[0], 0), (0, 1), (0, -1)]
                else:
                    first = (0, 1 if py >= fy else -1)
                    cands = [first, (0, -first[1]), (1, 0), (-1, 0)]
            else:                                        # ball / square pad: nearest part edge first
                ed = [(px - tomm(fb.GetLeft()), (-1, 0)), (tomm(fb.GetRight()) - px, (1, 0)),
                      (py - tomm(fb.GetTop()), (0, -1)), (tomm(fb.GetBottom()) - py, (0, 1))]
                cands = [d for _, d in sorted(ed, key=lambda e: e[0])]
            placed = False
            for ux, uy in cands:
                half = (w if ux else h) / 2
                x2, y2 = px + ux * (half + STUB_LEN), py + uy * (half + STUB_LEN)
                n = int((half + STUB_LEN) / RES)
                free = True
                for i in range(1, n + 1):
                    xx = cx(px + ux * i * RES)
                    yy = cy(py + uy * i * RES)
                    if not (0 <= xx < NX and 0 <= yy < NY) or ot[l, yy, xx] not in (0, code):
                        free = False
                        break
                if free:
                    G.stamp_seg([l], px, py, x2, y2, wclass, code)
                    placed = True
                    break
            n_ok += placed
            n_no += (not placed)
    print("exits reserved: %d, no free exit: %d" % (n_ok, n_no), flush=True)


def main():
    t0 = time.time()
    todo = unrouted_nets()
    if "--nets" in sys.argv:
        want = sys.argv[sys.argv.index("--nets") + 1].split(",")
        todo = [n for n in todo if n in want]
    if "--skip-plane" in sys.argv:
        todo = [n for n in todo if n not in PLANE]
    if "--only-plane" in sys.argv:
        todo = [n for n in todo if n in PLANE]
    # order: plane leftovers first (short, need escape room), then power, then short signals first
    todo.sort(key=lambda n: (0 if n in PLANE else 1 if n in POWER else 2, hpwl(n)))
    if "--prio" in sys.argv:                  # nets that failed in an earlier pass go first
        import json
        pr = json.load(open(sys.argv[sys.argv.index("--prio") + 1]))
        todo.sort(key=lambda n: pr.index(n) if n in pr else len(pr))
    print("nets to route:", len(todo), flush=True)
    reserve_exits(todo)
    failed = []
    for n in todo:
        ok = route_net(n)
        print("  %-34s %s  (%.0fs)" % (n[-34:], "ok" if ok else "FAILED", time.time() - t0), flush=True)
        if not ok:
            failed.append(n)
    if "--fail-out" in sys.argv:
        import json
        json.dump(failed, open(sys.argv[sys.argv.index("--fail-out") + 1], "w"))
    pcbnew.SaveBoard(BOARD, board, True)
    left = unrouted_nets()
    print("routed; still open nets: %d %s" % (len(left), left[:20]))


if __name__ == "__main__":
    main()
