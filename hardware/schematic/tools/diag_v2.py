"""Why does route_v2 fail a net? Uses route_v2's own fixed grid (leftover-pass setup, In2 allowed).
For each open group pair: free exit cells around every pad per width class, and a flood (vias allowed)
from group 0 telling whether the other groups are reachable at 0.1 mm, and which nets wall the region.
Usage: python diag_v2.py NET [NET ...]
Done by Harsh Thakur."""
import collections
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
want = sys.argv[1:]
sys.argv = [sys.argv[0], "--in2", "--adopt"]
spec = importlib.util.spec_from_file_location("rv", os.path.join(HERE, "route_v2.py"))
rv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rv)
import numpy as np
from collections import deque

rv.GF.__init__()
rv.rebuild_fixed_from_board()
names = {c: n for n, c in rv.NETCODE.items()}
for net in want:
    code = rv.NETCODE[net]
    core = rv.own_core(net)
    for w in rv.WCLS:
        ok = (rv.GF.t[w] == 0) | (rv.GF.t[w] == code) | core
        okv = ((rv.GF.vb == 0) | (rv.GF.vb == code)).all(axis=0) & ~rv.NOV_B
        gs = rv.groups_of(net)
        cells = [set() for _ in gs]
        for gi, g in enumerate(gs):
            for o in g:
                if o.GetClass() != "PAD":
                    continue
                b = o.GetBoundingBox()
                for l in rv.pad_layers(o):
                    for y in range(rv.cx(rv.tomm(b.GetTop())), rv.cx(rv.tomm(b.GetBottom())) + 1):
                        for x in range(rv.cx(rv.tomm(b.GetLeft())), rv.cx(rv.tomm(b.GetRight())) + 1):
                            if ok[l, y, x]:
                                cells[gi].add((l, x, y))
        seen = set(cells[0])
        dq = deque(seen)
        wall = collections.Counter()
        while dq:
            l, x, y = dq.popleft()
            for dx, dy in rv.DIRS:
                nx_, ny_ = x + dx, y + dy
                if not (0 <= nx_ < rv.NX and 0 <= ny_ < rv.NY):
                    continue
                k = (l, nx_, ny_)
                if k in seen:
                    continue
                if ok[l, ny_, nx_]:
                    seen.add(k)
                    dq.append(k)
                else:
                    wall[names.get(int(rv.GF.t[w][l, ny_, nx_]), str(int(rv.GF.t[w][l, ny_, nx_])))] += 1
            if okv[y, x]:
                for l2 in rv.SIG:
                    k = (l2, x, y)
                    if k not in seen and ok[l2, y, x]:
                        seen.add(k)
                        dq.append(k)
        reach = [gi for gi in range(1, len(gs)) if cells[gi] & seen]
        print("%s w=%.2f groups=%d pad cells=%s reachable from g0: %s  region=%d cells" %
              (net, w, len(gs), [len(c) for c in cells], reach, len(seen)), flush=True)
        if len(reach) < len(gs) - 1:
            print("   wall:", wall.most_common(8), flush=True)
            for gi, g in enumerate(gs):
                print("   g%d:" % gi, [(o.GetParentFootprint().GetReference() + "." + o.GetNumber()) for o in g if o.GetClass() == "PAD"], flush=True)
os._exit(0)
