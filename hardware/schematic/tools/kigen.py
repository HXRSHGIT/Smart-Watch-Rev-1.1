"""kigen: small KiCad 9 symbol-library and schematic writer for the Smart Watch board.

Why a generator: every pin name, pin number and net below comes from a table that was
read from a datasheet, so a sheet can be rebuilt and re-checked (ERC + netlist) in seconds.

Conventions
- Parts are placed unrotated or rotated by 90/180/270, never mirrored.
- Connections are made by a label or power symbol whose anchor sits exactly on the pin end.
- Stock symbols are copied from the installed KiCad 9 libraries; chip symbols are generated.
"""
import re
import uuid
from pathlib import Path

KICAD_SHARE = Path(r"C:/Users/TempAdmin/AppData/Local/Programs/KiCad/9.0/share/kicad")
PROJECT = "smartwatch"
FONT = "(effects (font (size 1.27 1.27)))"
HIDE = "(effects (font (size 1.27 1.27)) (hide yes))"


def uid():
    return str(uuid.uuid4())


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


# ----------------------------------------------------------------------------- s-expression reading
_TOKEN = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+')


def parse(text):
    tok = _TOKEN.findall(text)
    pos = 0

    def rd():
        nonlocal pos
        t = tok[pos]
        pos += 1
        if t == "(":
            out = []
            while tok[pos] != ")":
                out.append(rd())
            pos += 1
            return out
        if t.startswith('"'):
            return t[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        return t

    return rd()


def find(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def block_at(text, start):
    """Return the balanced '(...)' text starting at index start (respects quotes)."""
    depth, i, n = 0, start, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i += 1
            while text[i] != '"':
                i += 2 if text[i] == "\\" else 1
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    raise ValueError("unbalanced")


def stock_symbol(lib, name):
    """Text of (symbol "name" ...) from an installed KiCad symbol library, renamed lib:name."""
    path = KICAD_SHARE / "symbols" / f"{lib}.kicad_sym"
    text = path.read_text(encoding="utf-8")
    m = re.search(r'\n\t\(symbol "' + re.escape(name) + r'"\n', text)
    if not m:
        raise KeyError(f"{lib}:{name} not in {path}")
    blk = block_at(text, m.start() + 1)
    if "(extends" in blk:
        raise ValueError(f"{lib}:{name} extends another symbol; pick a base symbol")
    return blk.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)


# ----------------------------------------------------------------------------- chip symbol builder
class Unit:
    """One drawn unit of a chip symbol: pins as (number, name, type) in order; None = blank slot."""

    def __init__(self, title, left=(), right=(), top=(), bottom=(), width=20.32):
        self.title, self.left, self.right, self.top, self.bottom, self.width = title, left, right, top, bottom, width


def chip_symbol(libname, name, ref, units, footprint="", datasheet="~", description="", keywords=""):
    """Build a (symbol ...) block for a custom chip. Returns the text for the library file."""
    L = 2.54
    out = [f'\t(symbol {q(name)}\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n'
           f'\t\t(property "Reference" {q(ref)} (at 0 0 0) {FONT})\n'
           f'\t\t(property "Value" {q(name)} (at 0 -2.54 0) {FONT})\n'
           f'\t\t(property "Footprint" {q(footprint)} (at 0 0 0) {HIDE})\n'
           f'\t\t(property "Datasheet" {q(datasheet)} (at 0 0 0) {HIDE})\n'
           f'\t\t(property "Description" {q(description)} (at 0 0 0) {HIDE})\n'
           f'\t\t(property "ki_keywords" {q(keywords)} (at 0 0 0) {HIDE})\n']
    for u, unit in enumerate(units, start=1):
        slots = max(len(unit.left), len(unit.right))
        h = max(slots, 2) * 2.54 + 5.08
        h = round(h / 2.54) * 2.54
        w = unit.width
        pins = [f'\t\t(symbol {q(f"{name}_{u}_1")}\n']
        pins.append(f'\t\t\t(rectangle (start {-w/2:.2f} {h/2:.2f}) (end {w/2:.2f} {-h/2:.2f})\n'
                    f'\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background)))\n')
        if unit.title:
            pins.append(f'\t\t\t(text {q(unit.title)} (at 0 {h/2 - 1.27:.2f} 0) (effects (font (size 1.27 1.27) bold)))\n')

        def pin(num, pname, ptype, x, y, ang):
            pins.append(f'\t\t\t(pin {ptype} line (at {x:.2f} {y:.2f} {ang}) (length {L})\n'
                        f'\t\t\t\t(name {q(pname)} {FONT})\n\t\t\t\t(number {q(num)} {FONT}))\n')

        for i, p in enumerate(unit.left):
            if p:
                pin(p[0], p[1], p[2], -w / 2 - L, h / 2 - 2.54 * (i + 2), 0)
        for i, p in enumerate(unit.right):
            if p:
                pin(p[0], p[1], p[2], w / 2 + L, h / 2 - 2.54 * (i + 2), 180)
        for i, p in enumerate(unit.top):
            if p:
                pin(p[0], p[1], p[2], -w / 2 + 2.54 * (i + 1), h / 2 + L, 270)
        for i, p in enumerate(unit.bottom):
            if p:
                pin(p[0], p[1], p[2], -w / 2 + 2.54 * (i + 1), -h / 2 - L, 90)
        pins.append("\t\t)\n")
        out.extend(pins)
    out.append("\t\t(embedded_fonts no)\n\t)\n")
    return "".join(out)


def write_symbol_lib(path, blocks):
    text = ('(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "kigen")\n\t(generator_version "9.0")\n'
            + "".join(blocks) + ")\n")
    Path(path).write_text(text, encoding="utf-8")


# ----------------------------------------------------------------------------- pin geometry
class Lib:
    """Symbols embedded in sheets. libid is 'lib:name'."""

    def __init__(self):
        self.text = {}
        self._pins = {}

    def add_stock(self, lib, name):
        self.text[f"{lib}:{name}"] = stock_symbol(lib, name)

    def add_custom(self, libname, block):
        name = parse(block)[1]
        self.text[f"{libname}:{name}"] = block.replace(f"(symbol {q(name)}", f"(symbol {q(libname + ':' + name)}", 1)

    def body(self, libid, unit):
        """(x1, y1, x2, y2) of the first rectangle of this unit (library coordinates), or None."""
        for sub in find(parse(self.text[libid]), "symbol"):
            m = re.search(r"_(\d+)_(\d+)$", sub[1])
            if m and int(m.group(1)) in (unit, 0):
                for r in find(sub, "rectangle"):
                    s, e = find(r, "start")[0], find(r, "end")[0]
                    return float(s[1]), float(s[2]), float(e[1]), float(e[2])
        return None

    def pins(self, libid):
        """{(unit, number): (x, y, angle, name, type)} in library coordinates."""
        if libid in self._pins:
            return self._pins[libid]
        tree = parse(self.text[libid])
        res = {}
        for sub in find(tree, "symbol"):
            m = re.search(r"_(\d+)_(\d+)$", sub[1])
            if not m:
                continue
            unit = int(m.group(1))
            for p in find(sub, "pin"):
                at = find(p, "at")[0]
                res[(unit, find(p, "number")[0][1])] = (float(at[1]), float(at[2]), int(float(at[3])),
                                                         find(p, "name")[0][1], p[1])
        self._pins[libid] = res
        return res


def xform(dx, dy, rot):
    """Library offset (y up) -> sheet offset (y down) for a placement rotation in degrees (CCW on screen)."""
    x, y = dx, -dy
    return {0: (x, y), 90: (y, -x), 180: (-x, -y), 270: (-y, x)}[rot]


def snap(v):
    return round(v + 0.0, 4)


def grid(v, step=1.27):
    """Snap to the KiCad connection grid (50 mil)."""
    return snap(round(v / step) * step)


# ----------------------------------------------------------------------------- sheet writer
class Registry:
    """Reference designators shared by all sheets."""

    def __init__(self):
        self.used = set()
        self.next = {}

    def take(self, prefix, explicit=None):
        if explicit:
            assert explicit not in self.used, f"duplicate reference {explicit}"
            self.used.add(explicit)
            return explicit
        n = self.next.get(prefix, 1)
        while f"{prefix}{n}" in self.used:
            n += 1
        self.next[prefix] = n + 1
        self.used.add(f"{prefix}{n}")
        return f"{prefix}{n}"


class Sheet:
    def __init__(self, lib, reg, root_uuid, sheet_uuid, title, paper="A3", rev="0.1"):
        self.lib, self.reg = lib, reg
        self.path = f"/{root_uuid}" + (f"/{sheet_uuid}" if sheet_uuid else "")
        self.uuid = root_uuid if not sheet_uuid else uid()
        self.title, self.paper, self.rev = title, paper, rev
        self.items, self.used_libs = [], set()
        self.placed = []          # (ref, libid, unit, {pin: net})
        self.ports = []           # (name, x, y) hierarchical labels, for sheet-pin generation
        self.sheet_blocks = []

    # -- primitives
    def _prop(self, name, value, x, y, rot=0, hide=False, just=None):
        j = f" (justify {just})" if just else ""
        h = " (hide yes)" if hide else ""
        return f'\t\t(property {q(name)} {q(value)} (at {snap(x)} {snap(y)} {rot}) (effects (font (size 1.27 1.27)){j}{h}))\n'

    def label(self, name, x, y, ang=0):
        just = "left bottom" if ang in (0, 90) else "right bottom"
        self.items.append(f'\t(label {q(name)} (at {snap(x)} {snap(y)} {ang}) (effects (font (size 1.27 1.27)) (justify {just})) (uuid {q(uid())}))\n')

    def global_label(self, name, x, y, ang=0, shape="passive"):
        just = "left" if ang in (0, 90) else "right"
        self.items.append(f'\t(global_label {q(name)} (shape {shape}) (at {snap(x)} {snap(y)} {ang}) (fields_autoplaced yes) '
                          f'(effects (font (size 1.27 1.27)) (justify {just})) (uuid {q(uid())})\n'
                          f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at 0 0 0) {HIDE}))\n')

    def hlabel(self, name, x, y, ang=0, shape="bidirectional"):
        if name in self.ports:            # one sheet-interface label per name; the rest are local labels
            self.label(name, x, y, ang)
            return
        just = "left" if ang in (0, 90) else "right"
        self.items.append(f'\t(hierarchical_label {q(name)} (shape {shape}) (at {snap(x)} {snap(y)} {ang}) '
                          f'(effects (font (size 1.27 1.27)) (justify {just})) (uuid {q(uid())}))\n')
        self.ports.append(name)

    def noconn(self, x, y):
        self.items.append(f'\t(no_connect (at {snap(x)} {snap(y)}) (uuid {q(uid())}))\n')

    def wire(self, x1, y1, x2, y2):
        self.items.append(f'\t(wire (pts (xy {snap(x1)} {snap(y1)}) (xy {snap(x2)} {snap(y2)})) '
                          f'(stroke (width 0) (type default)) (uuid {q(uid())}))\n')

    def text(self, s, x, y, size=1.27, bold=False):
        b = " bold" if bold else ""
        self.items.append(f'\t(text {q(s)} (exclude_from_sim no) (at {snap(x)} {snap(y)} 0) '
                          f'(effects (font (size {size} {size}){b}) (justify left bottom)) (uuid {q(uid())}))\n')

    # -- parts
    def part(self, libid, x, y, rot=0, ref=None, value="", footprint="", unit=1, nets=None, nc=(),
             props=None, prefix=None, dnp=False, again=False):
        """Place a symbol. nets maps pin number -> net text. A leading '=' marks a power rail drawn as a
        power symbol ('=GND', '=+1V8'); any other text becomes a local label. nc lists pins to flag no-connect."""
        nets = nets or {}
        x, y = grid(x), grid(y)
        props = dict(props or {})
        tree = parse(self.lib.text[libid])
        sym_name = libid.split(":", 1)[1]
        if prefix is None:
            r = [p for p in find(tree, "property") if p[1] == "Reference"][0][2]
            prefix = r
        refdes = ref if again else self.reg.take(prefix, ref)
        pins = self.lib.pins(libid)
        self.used_libs.add(libid)
        lines = [f'\t(symbol (lib_id {q(libid)}) (at {snap(x)} {snap(y)} {rot}) (unit {unit}) (exclude_from_sim no) '
                 f'(in_bom yes) (on_board yes) (dnp {"yes" if dnp else "no"}) (uuid {q(uid())})\n']
        body = self.lib.body(libid, unit)
        counter = (360 - rot) % 360             # property angles are relative to the symbol: undo the rotation
        if body:                                # chip: text sits above the body outline
            top = y - max(body[1], body[3])
            lines.append(self._prop("Reference", refdes, x + body[0], top - 1.0, counter, just="left bottom"))
            lines.append(self._prop("Value", value or sym_name, x + body[0], top - 3.5, counter, just="left bottom"))
        elif rot in (90, 270):                  # horizontal two-pin part: text above and below
            lines.append(self._prop("Reference", refdes, x, y - 2.2, counter, just="bottom"))
            lines.append(self._prop("Value", value or sym_name, x, y + 2.2, counter, just="top"))
        else:
            lines.append(self._prop("Reference", refdes, x + 2.54, y - 0.6, 0, just="left bottom"))
            lines.append(self._prop("Value", value or sym_name, x + 2.54, y + 0.6, 0, just="left top"))
        lines.append(self._prop("Footprint", footprint, x, y, 0, hide=True))
        lines.append(self._prop("Datasheet", props.pop("Datasheet", "~"), x, y, 0, hide=True))
        for k, v in props.items():
            lines.append(self._prop(k, v, x, y, 0, hide=True))
        mine = sorted(n for (u, n) in pins if u == unit or u == 0)
        for n in mine:
            lines.append(f'\t\t(pin {q(n)} (uuid {q(uid())}))\n')
        lines.append(f'\t\t(instances (project {q(PROJECT)} (path {q(self.path)} (reference {q(refdes)}) (unit {unit}))))\n\t)\n')
        self.items.append("".join(lines))
        self.placed.append((refdes, libid, unit, dict(nets)))
        # connections
        for n, net in nets.items():
            px, py, ang, _, _ = pins.get((unit, n)) or pins[(0, n)]
            dx, dy = xform(px, py, rot)
            ox, oy = xform(-_cos(ang), -_sin(ang), rot)      # outward direction on the sheet
            self._attach(net, x + dx, y + dy, ox, oy)
        for n in nc:
            px, py, *_ = pins.get((unit, n)) or pins[(0, n)]
            dx, dy = xform(px, py, rot)
            self.noconn(x + dx, y + dy)
        return refdes

    def _attach(self, net, px, py, ox, oy):
        if net.startswith("="):
            self.power(net[1:], px, py)
            return
        ang = {(1, 0): 0, (0, -1): 90, (-1, 0): 180, (0, 1): 270}[(round(ox), round(oy))]
        if net.startswith("hl:"):
            self.hlabel(net[3:], px, py, ang)
        elif net.startswith("gl:"):
            self.global_label(net[3:], px, py, ang)
        else:
            self.label(net, px, py, ang)

    def power(self, name, x, y):
        libid = f"power:{name}"
        if libid not in self.lib.text:
            self.lib.add_stock("power", name)
        self.used_libs.add(libid)
        ref = self.reg.take("#PWR")
        self.items.append(
            f'\t(symbol (lib_id {q(libid)}) (at {snap(x)} {snap(y)} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) '
            f'(dnp no) (uuid {q(uid())})\n'
            f'\t\t(property "Reference" {q(ref)} (at {snap(x)} {snap(y)} 0) {HIDE})\n'
            f'\t\t(property "Value" {q(name)} (at {snap(x)} {snap(y + (3.5 if name == "GND" else -3.5))} 0) {FONT})\n'
            f'\t\t(property "Footprint" "" (at {snap(x)} {snap(y)} 0) {HIDE})\n'
            f'\t\t(property "Datasheet" "" (at {snap(x)} {snap(y)} 0) {HIDE})\n'
            f'\t\t(pin "1" (uuid {q(uid())}))\n'
            f'\t\t(instances (project {q(PROJECT)} (path {q(self.path)} (reference {q(ref)}) (unit 1))))\n\t)\n')

    def sheet_block(self, name, file, x, y, w, h, left, right, page, block_uuid):
        """Root-level hierarchical sheet. left/right are lists of pin names. A label of the same name is
        placed at each pin end so sheets connect by name. Returns {pin name: (x, y)}."""
        pins, ends = [], {}
        x, y = grid(x), grid(y)
        for side, names in (("L", left), ("R", right)):
            for i, n in enumerate(names):
                py = y + 2.54 * (i + 1)
                px, ang = (x, 180) if side == "L" else (x + w, 0)
                just = "left" if side == "L" else "right"        # names sit inside the box
                pins.append(f'\t\t(pin {q(n)} bidirectional (at {snap(px)} {snap(py)} {ang}) '
                            f'(effects (font (size 1.27 1.27)) (justify {just})) (uuid {q(uid())}))\n')
                ends[n] = (px, py)
                self.label(n, px, py, ang)
        self.items.append(
            f'\t(sheet (at {snap(x)} {snap(y)}) (size {w} {h}) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)\n'
            f'\t\t(stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0)) (uuid {q(block_uuid)})\n'
            f'\t\t(property "Sheetname" {q(name)} (at {snap(x)} {snap(y - 0.7)} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))\n'
            f'\t\t(property "Sheetfile" {q(file)} (at {snap(x)} {snap(y + h + 0.7)} 0) (effects (font (size 1.27 1.27)) (justify left top)))\n'
            + "".join(pins) +
            f'\t\t(instances (project {q(PROJECT)} (path {q(self.path)} (page {q(str(page))}))))\n\t)\n')
        return ends

    # -- output
    def render(self):
        libs = "".join("\t\t" + self.lib.text[i].lstrip() + "\n" for i in sorted(self.used_libs))
        head = (f'(kicad_sch\n\t(version 20250114)\n\t(generator "eeschema")\n\t(generator_version "9.0")\n'
                f'\t(uuid {q(self.uuid)})\n\t(paper {q(self.paper)})\n'
                f'\t(title_block (title {q(self.title)}) (rev {q(self.rev)}) (company "Done by Harsh Thakur"))\n'
                f'\t(lib_symbols\n{libs}\t)\n')
        tail = '\t(sheet_instances (path "/" (page "1")))\n\t(embedded_fonts no)\n)\n'
        return head + "".join(self.items) + tail


def _cos(a):
    return {0: 1, 90: 0, 180: -1, 270: 0}[a]


def _sin(a):
    return {0: 0, 90: 1, 180: 0, 270: -1}[a]
