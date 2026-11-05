"""draw: a hand-drawing toolkit on top of kigen.Sheet.

Parts are put at chosen coordinates, wires are routed between exact pin positions, and the sheet gets frames,
notes, captions and ports, so a sheet reads like a human-drawn one (see ../STYLE_GUIDE.md).
All coordinates are millimetres on the 1.27 mm grid; y grows downward.
"""
from kigen import (Sheet, Lib, parse, find, q, uid, snap, grid, xform, PROJECT, FONT, HIDE, _cos, _sin)

BLUE = "(color 0 0 180 1)"
RED = "(color 200 0 0 1)"
PURPLE = "(color 140 0 190 1)"


def _eq(a, b):
    return abs(a - b) < 1e-3


class Part:
    """A placed symbol. p(pin) is the sheet position of that pin's connection point."""

    def __init__(self, sh, libid, ref, x, y, rot, unit):
        self.sh, self.libid, self.ref, self.x, self.y, self.rot, self.unit = sh, libid, ref, x, y, rot, unit
        self._pins = sh.lib.pins(libid)

    def p(self, pin):
        px, py, *_ = self._pins.get((self.unit, str(pin))) or self._pins[(0, str(pin))]
        dx, dy = xform(px, py, self.rot)
        return (snap(self.x + dx), snap(self.y + dy))

    def out(self, pin):
        """Unit vector pointing away from the symbol body at that pin."""
        _, _, ang, *_ = self._pins.get((self.unit, str(pin))) or self._pins[(0, str(pin))]
        ox, oy = xform(-_cos(ang), -_sin(ang), self.rot)
        return (round(ox), round(oy))


class Drawing(Sheet):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.segs = []            # wire segments (x1, y1, x2, y2)
        self.pinpts = []          # every pin connection point on the sheet
        self.labels = 0
        self.dots = set()

    # ------------------------------------------------------------------ parts
    def put(self, libid, x, y, rot=0, ref=None, value="", footprint="", unit=1, props=None, prefix=None, dnp=False, tside="R",
            again=False, ctext="TR"):
        x, y = grid(x), grid(y)
        r = super().part(libid, x, y, rot, ref=ref, value=value, footprint=footprint, unit=unit, props=props,
                         prefix=prefix, dnp=dnp, again=again, tside=tside, ctext=ctext)
        pt = Part(self, libid, r, x, y, rot, unit)
        for n in {n for (u, n) in pt._pins if u in (unit, 0)}:
            self.pinpts.append(pt.p(n))
        return pt

    # ------------------------------------------------------------------ wires
    def w(self, *pts):
        """Polyline through points. Consecutive points must share x or y. Wires are written at render time, split
        at every pin or wire end they pass (KiCad joins a pin only to a wire END)."""
        pts = [(snap(p[0]), snap(p[1])) for p in pts]
        for a, b in zip(pts, pts[1:]):
            if _eq(a[0], b[0]) and _eq(a[1], b[1]):
                continue
            assert _eq(a[0], b[0]) or _eq(a[1], b[1]), f"diagonal wire {a} -> {b}"
            self.segs.append((a[0], a[1], b[0], b[1]))

    def dot(self, x, y):
        self.dots.add((snap(x), snap(y)))

    def _autodots(self):
        """Junction dots wherever 3 or more wire ends / pins meet, or a wire end meets the middle of a wire."""
        pts = {}
        for x1, y1, x2, y2 in self.segs:
            for p in ((x1, y1), (x2, y2)):
                pts[p] = pts.get(p, 0) + 1
        for p in self.pinpts:
            pts[p] = pts.get(p, 0) + 1
        for p, n in pts.items():
            on_mid = sum(1 for x1, y1, x2, y2 in self.segs
                         if (_eq(x1, x2) and _eq(p[0], x1) and min(y1, y2) + 1e-3 < p[1] < max(y1, y2) - 1e-3)
                         or (_eq(y1, y2) and _eq(p[1], y1) and min(x1, x2) + 1e-3 < p[0] < max(x1, x2) - 1e-3))
            if n + 2 * on_mid >= 3:
                self.dots.add(p)

    # ------------------------------------------------------------------ rails, grounds, ports
    def gnd(self, x, y):
        self.power("GND", x, y)
        self.pinpts.append((snap(x), snap(y)))

    def rail(self, name, x, y, style="+3V3"):
        """Supply symbol (arrow up) named `name`."""
        if name in ("+1V8", "+3V3", "+5V"):
            self.power(name, x, y)
        else:
            self.power_named(name, x, y, style)
        self.pinpts.append((snap(x), snap(y)))

    def power_named(self, name, x, y, style="+3V3"):
        libid = f"power:{style}"
        if libid not in self.lib.text:
            self.lib.add_stock("power", style)
        self.used_libs.add(libid)
        ref = self.reg.take("#PWR")
        self.items.append(
            f'\t(symbol (lib_id {q(libid)}) (at {snap(x)} {snap(y)} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) '
            f'(dnp no) (uuid {q(uid())})\n'
            f'\t\t(property "Reference" {q(ref)} (at {snap(x)} {snap(y)} 0) {HIDE})\n'
            f'\t\t(property "Value" {q(name)} (at {snap(x)} {snap(y - 3.5)} 0) {FONT})\n'
            f'\t\t(property "Footprint" "" (at {snap(x)} {snap(y)} 0) {HIDE})\n'
            f'\t\t(property "Datasheet" "" (at {snap(x)} {snap(y)} 0) {HIDE})\n'
            f'\t\t(pin "1" (uuid {q(uid())}))\n'
            f'\t\t(instances (project {q(PROJECT)} (path {q(self.path)} (reference {q(ref)}) (unit 1))))\n\t)\n')

    def port(self, name, x, y, side, shape="bidirectional"):
        """Sheet port at (x, y). side 'L' = the port sits at the left edge and its flag points left (signal comes in
        from the left); side 'R' = right edge, flag points right."""
        ang = 180 if side == "L" else 0
        Sheet.hlabel(self, name, x, y, ang, shape)
        self.pinpts.append((snap(x), snap(y)))

    def label_net(self, name, x, y, ang=0):
        self.labels += 1
        Sheet.label(self, name, x, y, ang)

    def nc(self, x, y):
        self.noconn(x, y)

    # ------------------------------------------------------------------ text and frames
    def head(self, text, x=15.24, y=15.24):
        self._text(text, x, y, 2.0, bold=True, color=BLUE)

    def sub(self, text, x, y):
        self._text(text, x, y, 1.27, color=BLUE)

    def caption(self, text, x, y, color=PURPLE, size=1.7, bold=True):
        self._text(text, x, y, size, bold=bold, color=color)

    def _text(self, s, x, y, size, bold=False, color=""):
        b = " bold" if bold else ""
        self.items.append(f'\t(text {q(s)} (exclude_from_sim no) (at {snap(x)} {snap(y)} 0) '
                          f'(effects (font (size {size} {size}){b} {color}) (justify left bottom)) (uuid {q(uid())}))\n')

    def note(self, text, x, y, w, h):
        """Blue note box (designer note)."""
        self.items.append(
            f'\t(text_box {q(text)} (exclude_from_sim no) (at {snap(x)} {snap(y)} 0) (size {w} {h}) '
            f'(margins 0.9525 0.9525 0.9525 0.9525) (stroke (width 0.1524) (type solid) (color 200 0 0 1)) '
            f'(fill (type color) (color 160 195 245 1)) (effects (font (size 1.27 1.27)) (justify left top)) (uuid {q(uid())}))\n')

    def frame(self, x1, y1, x2, y2, heading=None, dashed=False, color="0 0 180 1"):
        stroke = "dash" if dashed else "solid"
        self.items.append(
            f'\t(rectangle (start {snap(x1)} {snap(y1)}) (end {snap(x2)} {snap(y2)}) '
            f'(stroke (width 0.1524) (type {stroke}) (color {color})) (fill (type none)) (uuid {q(uid())}))\n')
        if heading:
            self._text(heading, x1 + 2.0, y1 + 4.5, 1.9, bold=True, color=BLUE)

    def barrier(self, x, y1, y2, left=None, right=None):
        """Dashed red vertical line, with a caption each side."""
        self.items.append(
            f'\t(polyline (pts (xy {snap(x)} {snap(y1)}) (xy {snap(x)} {snap(y2)})) '
            f'(stroke (width 0.2) (type dash) (color 200 0 0 1)) (uuid {q(uid())}))\n')
        if left:
            self._text(left, x - 2.0 - 1.3 * len(left) * 0.75, y1 + 3, 1.27, color=RED)
        if right:
            self._text(right, x + 2.0, y1 + 3, 1.27, color=RED)

    # ------------------------------------------------------------------ output
    def _split(self):
        """Split each wire at pins and at the ends of other wires that fall inside it; drop duplicates."""
        cuts = set(self.pinpts)
        for x1, y1, x2, y2 in self.segs:
            cuts.add((x1, y1))
            cuts.add((x2, y2))
        out, seen = [], set()
        for x1, y1, x2, y2 in self.segs:
            inside = [p for p in cuts
                      if (_eq(x1, x2) and _eq(p[0], x1) and min(y1, y2) + 1e-3 < p[1] < max(y1, y2) - 1e-3)
                      or (_eq(y1, y2) and _eq(p[1], y1) and min(x1, x2) + 1e-3 < p[0] < max(x1, x2) - 1e-3)]
            pts = [(x1, y1)] + sorted(inside, key=lambda p: abs(p[0] - x1) + abs(p[1] - y1)) + [(x2, y2)]
            for a, b in zip(pts, pts[1:]):
                key = (min(a, b), max(a, b))
                if key not in seen:
                    seen.add(key)
                    out.append((a[0], a[1], b[0], b[1]))
        return out

    def render(self):
        self.segs = self._split()
        for x1, y1, x2, y2 in self.segs:
            Sheet.wire(self, x1, y1, x2, y2)
        self._autodots()
        for (x, y) in sorted(self.dots):
            self.items.append(f'\t(junction (at {x} {y}) (diameter 0) (color 0 0 0 0) (uuid {q(uid())}))\n')
        return Sheet.render(self)
