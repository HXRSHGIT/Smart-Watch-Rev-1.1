"""Why does a net not route? Flood from one group over all layers (vias allowed) and report whether the
other group is reachable and which nets / parts form the wall around the reachable area.
Done by Harsh Thakur."""
import importlib.util, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
want = sys.argv[1:]
sys.argv = [sys.argv[0]]
spec = importlib.util.spec_from_file_location("ro", os.path.join(HERE, "route_own.py"))
ro = importlib.util.module_from_spec(spec); spec.loader.exec_module(ro)
import numpy as np
from collections import deque
CAP = 2500000
for net in (want or ro.unrouted_nets()):
    if net in ro.PLANE or net not in ro.NETCODE: continue
    wclass = 0.2 if net in ro.POWER else 0.1
    code = ro.NETCODE[net]; ot = ro.G.t[wclass]
    gs = ro.groups_of(net)
    if len(gs) < 2: continue
    core = np.zeros((3, ro.NY, ro.NX), bool)
    for o in ro.items_of(net):
        if o.GetClass() == "PAD" and ro.has_copper(o):
            b = o.GetBoundingBox()
            for l in ro.pad_layers(o):
                core[l, ro.cy(ro.tomm(b.GetTop())):ro.cy(ro.tomm(b.GetBottom())) + 1, ro.cx(ro.tomm(b.GetLeft())):ro.cx(ro.tomm(b.GetRight())) + 1] = True
    okt = (ot == 0) | (ot == code) | core
    okv = ((ro.G.v == 0) | (ro.G.v == code)).all(axis=0) & ~ro.G.nov
    gs.sort(key=lambda g: len(g))
    A, B = gs[0], max(gs[1:], key=lambda g: len(g))
    src = [t for t in ro.terminals(A) if t[3].GetClass() == "PAD"] or ro.terminals(A)
    tg = {(t[0], t[1], t[2]) for t in ro.terminals(B)}
    seen = set(); dq = deque()
    for l, x, y, o in src[:1]:
        seen.add((l, x, y)); dq.append((l, x, y))
    hit = False
    while dq and len(seen) < CAP:
        l, x, y = dq.popleft()
        if (l, x, y) in tg: hit = True; break
        for dx, dy in ro.DIRS:
            n = (l, x + dx, y + dy)
            if n in seen or not (0 <= n[1] < ro.NX and 0 <= n[2] < ro.NY): continue
            if okt[l, n[2], n[1]]:
                seen.add(n); dq.append(n)
        if okv[y, x]:
            for l2 in range(3):
                n = (l2, x, y)
                if l2 != l and n not in seen and okt[l2, y, x]:
                    seen.add(n); dq.append(n)
    wall = collections.Counter()
    if not hit:
        for (l, x, y) in list(seen)[:400000]:
            for dx, dy in ro.DIRS[:4]:
                xx, yy = x + dx, y + dy
                if 0 <= xx < ro.NX and 0 <= yy < ro.NY and not okt[l, yy, xx]:
                    v = int(ot[l, yy, xx]); wall[ro.NETNAME.get(v, "other/-1" if v == -1 else "no-net")] += 1
    a = src[0][3]
    print("%-26s from %s.%s: %s reachable=%d  wall: %s" % (net[-26:], a.GetParentFootprint().GetReference(), a.GetNumber(),
          "CONNECTS (A* limit?)" if hit else "BLOCKED", len(seen), wall.most_common(4)), flush=True)
