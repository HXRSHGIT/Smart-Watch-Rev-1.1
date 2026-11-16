"""First placement of smartwatch.kicad_pcb. Run with KiCad's Python (it has pcbnew):
  "%LOCALAPPDATA%/Programs/KiCad/9.0/bin/python.exe" tools/place_board.py [board.kicad_pcb]
Reads the board made by make_board.py, moves every footprint, adds the antenna keep-out, saves in place (settings file untouched).
Rules (hardware/PLACEMENT_RULES.md): bottom face touches the skin (optics, skin temperature, charging pads), everything else on top;
antenna in a corner with the Johanson 6.5 x 6.5 mm clearance; RF chain short; 0 / 90 degree rotations only;
each passive is put as close as possible to the pad it serves; no overlaps; 0.3 mm to the board edge.
Anything not listed in FIXED is placed automatically beside the part it connects to. Re-running starts again from whatever is on the board.
"""
import math, os, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
BOARD = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(PRJ, "smartwatch.kicad_pcb")
W, H = 40.0, 27.0            # board, mm (also BOARD_MM in make_board.py); grown from 34 x 23 on 2026-11-15 so the board routes
EDGE = 0.3                   # courtyard to board edge
GAP = 0.25                   # free space kept around every automatically placed part (routing channels)
ANT_BOX = (0.0, 0.0, 6.5, 6.5)   # Johanson 2450AT18A0100001E ground clearance, no parts or copper pour on any layer

# ref: (centre x, centre y, rotation, side); centre = centre of the footprint's courtyard. side "T" top (away from skin), "B" bottom (skin)
FIXED = {
    # antenna corner, top left. Pad 1 (feed) must face +x: rotation 180. Tee slots (R3, C14, R2) at the clearance edge.
    "AE1": (2.4, 2.5, 180, "T"), "R3": (5.9, 2.5, 180, "T"), "C14": (7.05, 4.5, 90, "T"), "R2": (8.2, 2.5, 180, "T"),
    # processor with its RF / crystal side facing the antenna (left); pi network from pin 31 leftwards
    "U1": (14.5, 11.5, 180, "T"), "L2": (10.0, 11.7, 180, "T"), "L3": (8.4, 11.7, 180, "T"), "L4": (6.8, 11.7, 180, "T"),
    "X2": (8.6, 15.6, 180, "T"), "X1": (20.5, 15.6, 0, "T"),
    # IMU next to U1's I2C / interrupt pins (top-left side), flash next to the SPI pins (top-right)
    "U3": (9.8, 6.2, 0, "T"), "U8": (21.6, 4.8, 0, "T"),
    "U5": (26.0, 5.0, 0, "T"), "U7": (31.0, 19.5, 0, "T"),
    # connectors and switch on the board edges; Tag-Connect on the top edge right above U1's SWD pins
    "J5": (34.5, 2.3, 90, "T"), "J4": (36.2, 10.5, 90, "T"), "SW1": (37.0, 24.9, 0, "T"), "J3": (15.2, 2.4, 0, "T"),
    # bottom (skin): optics and skin temperature in the middle of the back face, charging pads on the right edge
    "PD1": (13.5, 13.5, 0, "B"), "D1": (20.0, 13.5, 0, "B"), "PD2": (26.5, 13.5, 0, "B"), "U2": (20.0, 16.5, 0, "B"),
    "U4": (26.5, 17.6, 0, "B"), "U6": (33.0, 13.5, 0, "B"), "J1": (38.0, 8.3, 0, "B"), "J2": (38.0, 18.7, 0, "B"),
}
for i in range(10):          # test points on the bottom-left edge of the top face, two rows of five
    FIXED[f"TP{i + 1}"] = (2.0 + 2.35 * (i % 5), H - 1.6 - 2.5 * (i // 5), 0, "T")
THT = {"J5"}                 # occupies both faces
PASSIVE = ("C", "R", "L", "FB", "NT")
BIG_NETS = 40                # nets with more pads (ground, main rails) do not anchor anything

board = pcbnew.LoadBoard(BOARD)
fps = {f.GetReference(): f for f in board.GetFootprints()}
mm = pcbnew.FromMM
V = pcbnew.VECTOR2I


def netpads():
    nets = {}
    for ref, f in fps.items():
        for p in f.Pads():
            if p.GetNetname() and p.GetNumber():
                nets.setdefault(p.GetNetname(), []).append((ref, p))
    return nets


NETS = netpads()
GROUND = {n for n, v in NETS.items() if len(v) > BIG_NETS}


def to_side(f, side):
    if (f.GetLayer() == pcbnew.B_Cu) != (side == "B"):
        try:
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        except Exception:
            f.Flip(f.GetPosition(), True)


_shape = {}


def shape(ref, rot, side):
    """(width, height, centre offset x, y) of the footprint's bounding box (courtyard included) at this rotation and side, position at 0,0"""
    k = (ref, rot, side)
    if k not in _shape:
        f = fps[ref]
        to_side(f, side)
        f.SetPosition(V(0, 0))
        f.SetOrientationDegrees(rot)
        f.BuildCourtyardCaches()
        b = f.GetCourtyard(pcbnew.B_CrtYd if side == "B" else pcbnew.F_CrtYd).BBox()
        if b.GetWidth() == 0:                                  # no courtyard drawn: use everything but the text
            b = f.GetBoundingBox(False, False)
        _shape[k] = (pcbnew.ToMM(b.GetWidth()), pcbnew.ToMM(b.GetHeight()), pcbnew.ToMM(b.Centre().x), pcbnew.ToMM(b.Centre().y))
    return _shape[k]


def put(ref, cx, cy, rot, side):
    w, h, ox, oy = shape(ref, rot, side)
    f = fps[ref]
    f.SetOrientationDegrees(rot)                             # shape() leaves the last probed rotation behind
    f.SetPosition(V(mm(cx - ox), mm(cy - oy)))
    r = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    return r


used = {"T": [], "B": []}
owner = {}


def free(r, side, box_ok=False, edge=EDGE):
    if r[0] < edge or r[1] < edge or r[2] > W - edge or r[3] > H - edge:
        return False
    if not box_ok and r[0] < ANT_BOX[2] and r[1] < ANT_BOX[3]:
        return False
    return all(r[2] <= u[0] or u[2] <= r[0] or r[3] <= u[1] or u[3] <= r[1] for u in used[side])


def claim(ref, r, side):
    used[side].append(r)
    owner[r] = ref
    if ref in THT:
        used["B" if side == "T" else "T"].append(r)


placed = {}
for ref, (cx, cy, rot, side) in FIXED.items():
    r = put(ref, cx, cy, rot, side)
    assert free(r, side, box_ok=True, edge=-0.5 if ref == 'AE1' else EDGE), f"{ref} at {cx},{cy} overlaps or leaves the board: {r} vs {[owner[u] for u in used[side] if not (r[2] <= u[0] or u[2] <= r[0] or r[3] <= u[1] or u[3] <= r[1])]}"
    claim(ref, r, side)
    placed[ref] = side

pad_use = {}


def anchors(ref):
    """pads of already placed parts that share a small net with ref: list of (net size, anchor ref, pad)"""
    out = []
    for p in fps[ref].Pads():
        n = p.GetNetname()
        if not n or n in GROUND:
            continue
        for r2, p2 in NETS[n]:
            if r2 != ref and r2 in placed and not r2.startswith("TP"):   # test points sit anywhere on their net, they anchor nothing
                out.append((len(NETS[n]), r2, p2))
    return out


def pad_xy(p):
    return pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)


def spot(ref, tx, ty, side):
    for i in range(0, 90):
        rad = i * 0.15
        for a in range(0, 360, 15):
            cx, cy = tx + rad * math.cos(math.radians(a)), ty + rad * math.sin(math.radians(a))
            for rot in (0, 90):
                w, h, ox, oy = shape(ref, rot, side)
                r = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
                rg = (r[0] - GAP, r[1] - GAP, r[2] + GAP, r[3] + GAP)
                if free(r, side) and free(rg, side, edge=EDGE - GAP):
                    return cx, cy, rot, r
    return None


todo = [r for r in sorted(fps) if r not in placed]
while todo:
    progress = False
    for ref in list(todo):
        a = anchors(ref)
        if not a:
            continue
        # prefer an IC neighbour on the smallest net, then spread the choice over the IC's pads
        ic = [x for x in a if not x[1].startswith(PASSIVE)]
        pool = ic or a
        smallest = min(x[0] for x in pool)
        cand = [x for x in pool if x[0] == smallest]
        cand.sort(key=lambda x: pad_use.get((x[1], x[2].GetNumber()), 0))
        _, aref, apad = cand[0]
        pad_use[(aref, apad.GetNumber())] = pad_use.get((aref, apad.GetNumber()), 0) + 1
        side = placed[aref]
        tx, ty = pad_xy(apad)
        s = spot(ref, tx, ty, side)
        assert s, f"no free spot for {ref} near {aref}"
        cx, cy, rot, r = s
        put(ref, cx, cy, rot, side)
        claim(ref, r, side)
        placed[ref] = side
        todo.remove(ref)
        progress = True
    assert progress, f"parts with no placed neighbour: {todo}"

# silkscreen: references on passives are hidden (they do not fit beside 0201 parts at JLCPCB's 1.0 mm minimum text height); ICs, connectors and test points keep theirs
for ref, f in fps.items():
    f.Reference().SetVisible(not ref.startswith(PASSIVE + ("TP",)))
    if not ref.startswith(PASSIVE):                         # text just outside the courtyard, away from pads
        f.BuildCourtyardCaches()
        c = f.GetCourtyard(pcbnew.B_CrtYd if placed[ref] == "B" else pcbnew.F_CrtYd).BBox()
        top = c.GetY() if c.GetWidth() else f.GetBoundingBox(False, False).GetY()
        cx = c.Centre().x if c.GetWidth() else f.GetPosition().x
        f.Reference().SetPosition(V(cx, top - mm(0.7)))
        f.Reference().SetTextAngleDegrees(0)

# antenna keep-out: no copper pour and no vias on any copper layer; the feed track and the antenna pads are allowed
for z in list(board.Zones()):
    if z.GetZoneName() == "ANT_KEEPOUT":
        board.Remove(z)
z = pcbnew.ZONE(board)
z.SetZoneName("ANT_KEEPOUT")
z.SetIsRuleArea(True)
z.SetDoNotAllowCopperPour(True)
z.SetDoNotAllowVias(True)
z.SetDoNotAllowTracks(False)
z.SetDoNotAllowPads(False)
z.SetDoNotAllowFootprints(False)
z.SetLayerSet(pcbnew.LSET.AllCuMask())
ol = z.Outline()
ol.NewOutline()
for x, y in ((ANT_BOX[0], ANT_BOX[1]), (ANT_BOX[2], ANT_BOX[1]), (ANT_BOX[2], ANT_BOX[3]), (ANT_BOX[0], ANT_BOX[3])):
    ol.Append(mm(x), mm(y))
board.Add(z)

# board outline follows W x H
for d in board.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_RECT:
        d.SetStart(V(0, 0))
        d.SetEnd(V(mm(W), mm(H)))

# 3D bodies for footprints KiCad's library has no model for (tools/gen_3d.py)
BODY = {"Johanson_2450AT18A0100001E_1206": "Johanson_2450AT18A0100001E", "MAX30208_TLGA-10_2x2mm": "MAX30208_TLGA10",
        "MAX86141_WLP-20_2.048x1.848mm_P0.4mm": "MAX86141_WLP20", "MX25R3235F_USON-8_4x3mm_P0.8mm": "MX25R3235F_USON8",
        "OCVPB21-13F6_WLCSP-13_P0.4mm": "OCVPB21_WLCSP13", "SFH7016_1.85x1.65mm": "SFH7016", "VEMD8080_4.8x2.5mm": "VEMD8080",
        "QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm": "nRF54L15_QFN48_6x6", "Crystal_SMD_2012_SC-20S_2.05x1.2mm": "Crystal_2012", "Crystal_SMD_2016-4Pin_2.0x1.6mm": "Crystal_2016"}
for f in fps.values():
    name = BODY.get(str(f.GetFPID().GetLibItemName()))
    if name:
        f.Models().clear()
        m = pcbnew.FP_3DMODEL()
        m.m_Filename = "${KIPRJMOD}/libs/3dshapes/" + name + ".wrl"
        m.m_Scale = pcbnew.VECTOR3D(1 / 2.54, 1 / 2.54, 1 / 2.54)
        f.Models().append(m)

pcbnew.SaveBoard(BOARD, board, True)
print(f"{BOARD}: {len(placed)} footprints placed ({sum(1 for s in placed.values() if s == 'T')} top, {sum(1 for s in placed.values() if s == 'B')} bottom)")
