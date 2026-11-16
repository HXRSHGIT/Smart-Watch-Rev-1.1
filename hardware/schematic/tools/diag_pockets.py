"""For every unconnected net, report how much free routing space each pad can reach (KiCad python).
A pad whose reachable area is tiny is boxed in by its neighbours (placement), not by routing order.
Done by Harsh Thakur."""
import importlib.util, os, sys
from collections import deque
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0]]
spec = importlib.util.spec_from_file_location("ro", os.path.join(HERE, "route_own.py"))
ro = importlib.util.module_from_spec(spec); spec.loader.exec_module(ro)
import numpy as np
CAP = 60000
def pocket(net, wclass, term):
    code = ro.NETCODE[net]; ot = ro.G.t[wclass]
    core = np.zeros((3, ro.NY, ro.NX), bool)
    for o in ro.items_of(net):
        if o.GetClass() == "PAD":
            b = o.GetBoundingBox()
            for l in ro.pad_layers(o):
                core[l, ro.cy(ro.tomm(b.GetTop())):ro.cy(ro.tomm(b.GetBottom())) + 1, ro.cx(ro.tomm(b.GetLeft())):ro.cx(ro.tomm(b.GetRight())) + 1] = True
    ok = ((ot == 0) | (ot == code) | core)
    l, x, y, o = term
    if not ok[l, y, x]:
        return 0, set()
    seen = {(x, y)}; dq = deque([(x, y)]); blockers = set()
    while dq and len(seen) < CAP:
        a, b = dq.popleft()
        for dx, dy in ro.DIRS:
            n = (a + dx, b + dy)
            if n in seen or not (0 <= n[0] < ro.NX and 0 <= n[1] < ro.NY): continue
            if ok[l, n[1], n[0]]:
                seen.add(n); dq.append(n)
    return len(seen), seen
rows = []
for net in ro.unrouted_nets():
    if net in ro.PLANE: continue
    wclass = 0.2 if net in ro.POWER else 0.1
    for g in ro.groups_of(net):
        for t in ro.terminals(g):
            if t[3].GetClass() != "PAD": continue
            n, seen = pocket(net, wclass, t)
            if t[0] == 1: continue
            f = t[3].GetParentFootprint().GetReference()
            rows.append((n, net, "%s.%s L%d" % (f, t[3].GetNumber(), t[0])))
rows.sort()
boxed = [r for r in rows if r[0] < 3000]
print("pads with < 3000 reachable cells (%.1f mm2): %d of %d" % (3000 * ro.RES * ro.RES, len(boxed), len(rows)))
for n, net, who in boxed:
    print("  %6d cells  %-28s %s" % (n, net[-28:], who))
