"""Custom footprints, drawn from datasheet drawings. python gen_footprints.py  ->  ../libs/smartwatch.pretty/

Each footprint states where its numbers came from. Where a vendor land-pattern drawing was NOT available
the footprint is marked 'CHECK' in its description and listed in hardware/REQUIREMENTS_FROM_DATASHEETS.md section 12.
All footprints are drawn for the top side; KiCad mirrors them when a part is placed on the bottom side.
"""
import uuid
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "libs" / "smartwatch.pretty"
OUT.mkdir(parents=True, exist_ok=True)


def fp(name, descr, pads, body, court, pin1=None, tags="", mask_margin=None, paste_margin=None):
    """pads: list of (number, shape, x, y, w, h). body/court: (x1, y1, x2, y2). Coordinates in mm, y down."""
    L = [f'(footprint "{name}"\n\t(version 20241229)\n\t(generator "kigen")\n\t(generator_version "9.0")\n\t(layer "F.Cu")\n'
         f'\t(descr "{descr}")\n\t(tags "{tags}")\n'
         f'\t(property "Reference" "REF**" (at 0 {court[1] - 1.0:.2f} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))\n'
         f'\t(property "Value" "{name}" (at 0 {court[3] + 1.0:.2f} 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))\n'
         f'\t(property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1.27 1.27))))\n'
         f'\t(property "Description" "{descr}" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1.27 1.27))))\n'
         f'\t(attr smd)\n']
    x1, y1, x2, y2 = body
    L.append(f'\t(fp_rect (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))\n')
    L.append(f'\t(fp_rect (start {x1 - 0.1:.2f} {y1 - 0.1:.2f}) (end {x2 + 0.1:.2f} {y2 + 0.1:.2f}) (stroke (width 0.12) (type solid)) (fill no) (layer "F.SilkS"))\n')
    cx1, cy1, cx2, cy2 = court
    L.append(f'\t(fp_rect (start {cx1} {cy1}) (end {cx2} {cy2}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))\n')
    if pin1:
        px, py = pin1
        L.append(f'\t(fp_circle (center {px} {py}) (end {px + 0.12:.2f} {py}) (stroke (width 0.12) (type solid)) (fill yes) (layer "F.SilkS"))\n')
    extra = ""
    if mask_margin is not None:
        extra += f" (solder_mask_margin {mask_margin})"
    if paste_margin is not None:
        extra += f" (solder_paste_margin {paste_margin})"
    for num, shape, x, y, w, h in pads:
        L.append(f'\t(pad "{num}" smd {shape} (at {x:.4f} {y:.4f}) (size {w} {h}) (layers "F.Cu" "F.Mask" "F.Paste"){extra} (uuid "{uuid.uuid4()}"))\n')
    L.append("\t(embedded_fonts no)\n)\n")
    (OUT / f"{name}.kicad_mod").write_text("".join(L), encoding="utf-8")
    return name


# ---- Vishay VEMD8080: footprint drawing 6.550-5354.01-4: pads 0.54 x 0.55, columns 1.31 / 1.38 / 1.31 apart,
# rows 2.38 apart. Numbering per the pinning top view: bottom row 1-4 left to right, top row 8-5 left to right.
xs = [-2.0, -0.69, 0.69, 2.0]
pads = [(i + 1, "rect", xs[i], 1.19, 0.54, 0.55) for i in range(4)] + [(8 - i, "rect", xs[i], -1.19, 0.54, 0.55) for i in range(4)]
fp("VEMD8080_4.8x2.5mm", "Vishay VEMD8080 photodiode, pad 5 anode (top right), others cathode. Vishay footprint drawing 6.550-5354.01-4.",
   pads, (-2.4, -1.25, 2.4, 1.25), (-2.7, -1.8, 2.7, 1.8), pin1=(-2.7, 1.5), tags="photodiode vishay")

# ---- ams OSRAM SFH 7016, recommended solder pad p.14: six 0.4 x 0.4 pads, 0.25 gap, rows 0.75 apart (inner gap).
# Numbering from the package drawing (top view): top row 5 3 1, bottom row 6 4 2.
cols = [-0.65, 0.0, 0.65]
pads = [(5, "rect", cols[0], -0.575, 0.4, 0.4), (3, "rect", cols[1], -0.575, 0.4, 0.4), (1, "rect", cols[2], -0.575, 0.4, 0.4),
        (6, "rect", cols[0], 0.575, 0.4, 0.4), (4, "rect", cols[1], 0.575, 0.4, 0.4), (2, "rect", cols[2], 0.575, 0.4, 0.4)]
fp("SFH7016_1.85x1.65mm", "ams OSRAM SFH 7016 RGB-IR emitter. Pads from datasheet v1.5 p.14. Pin 1 IR cathode, 2 and 5 anode, 3 green, 4 red, 6 NC.",
   pads, (-0.925, -0.825, 0.925, 0.825), (-1.25, -1.15, 1.25, 1.15), pin1=(1.25, -1.0), tags="led emitter osram")

# ---- ADI MAX86141 WLP-20, 5 x 4 at 0.4 mm. Pad centres and diameter (0.21 mm) read from the MAXREFDES103 sensor board
# ODB++ package BGA20C40P5X4_204X184X50B27M; ball numbering per datasheet Rev 5 pin configuration (top view, A row at top).
pads = []
for ri, row in enumerate("ABCD"):
    for col in range(1, 6):
        pads.append((f"{row}{col}", "circle", (col - 3) * 0.4, (ri - 1.5) * 0.4, 0.21, 0.21))
fp("MAX86141_WLP-20_2.048x1.848mm_P0.4mm", "ADI MAX86141 WLP-20 (5x4, 0.4 mm). Pad diameter and positions from the MAXREFDES103 fab data; confirm with ADI app note 1891.",
   pads, (-1.024, -0.924, 1.024, 0.924), (-1.3, -1.2, 1.3, 1.2), pin1=(-1.2, -1.05), tags="wlp afe adi", mask_margin=0.03)

# ---- ST OCVPB21-13F6 WLCSP-13, 0.4 mm pitch, pad 0.2 mm, mask opening 0.275 mm, stencil 0.25 mm (DS13107 section 4.1/4.2).
# Columns A..E left to right in the top view, rows 1..3 top to bottom.
present = "A1 A2 A3 B1 B2 B3 C2 C3 D1 D3 E1 E2 E3".split()
pads = [(n, "circle", ("ABCDE".index(n[0]) - 2) * 0.4, (int(n[1]) - 2) * 0.4, 0.2, 0.2) for n in present]
fp("OCVPB21-13F6_WLCSP-13_P0.4mm", "ST OCVPB21-13F6 WLCSP-13, 1.32 x 2.10 mm. Pads per DS13107 Rev 3 section 4.1. Orientation of A1 to the package marking: CHECK.",
   pads, (-1.05, -0.66, 1.05, 0.66), (-1.3, -0.9, 1.3, 0.9), pin1=(-1.15, -0.8), tags="wlcsp esd st",
   mask_margin=0.0375, paste_margin=0.025)

# ---- ADI MAX30208 thin LGA-10 2 x 2 mm. CHECK: pad sizes scaled from the pin-configuration drawing (top view, p.5);
# the vendor land pattern 90-100101 was not available.
pads = [(1, "rect", -0.6, -0.64, 0.5, 0.4), (2, "rect", -0.6, 0.0, 0.5, 0.4), (3, "rect", -0.6, 0.64, 0.5, 0.4),
        (6, "rect", 0.6, -0.64, 0.5, 0.4), (5, "rect", 0.6, 0.0, 0.5, 0.4), (4, "rect", 0.6, 0.64, 0.5, 0.4),
        (7, "rect", 0.0, -0.75, 0.2, 0.3), (8, "rect", 0.0, -0.25, 0.2, 0.3), (9, "rect", 0.0, 0.25, 0.2, 0.3),
        (10, "rect", 0.0, 0.75, 0.2, 0.3)]
fp("MAX30208_TLGA-10_2x2mm", "ADI MAX30208 thin LGA-10 2x2 mm. CHECK: pads scaled from the datasheet pin drawing, replace with land pattern 90-100101.",
   pads, (-1.0, -1.0, 1.0, 1.0), (-1.3, -1.3, 1.3, 1.3), pin1=(-1.15, -1.15), tags="lga temperature adi")

# ---- Johanson 2450AT18A0100001E, EIA 1206: overall pad pattern 4.2 mm, inner gap 2.6 mm, pad height 1.6 mm (DS p.3).
fp("Johanson_2450AT18A0100001E_1206", "Johanson 2.45 GHz chip antenna 3.2x1.6x1.3. Pad 1 feed, pad 2 NC but must be soldered. Pads from DS 36S0021A p.3. Keep copper clear around the body.",
   [(1, "rect", -1.7, 0.0, 0.8, 1.6), (2, "rect", 1.7, 0.0, 0.8, 1.6)], (-1.6, -0.8, 1.6, 0.8), (-2.3, -1.1, 2.3, 1.1),
   pin1=(-2.5, -1.0), tags="antenna ble")

# ---- Pogo charging pad: PLACEHOLDER diameter until the dock contact vendor is chosen.
fp("Pogo_Pad_D2.6mm", "Charging contact pad, 2.6 mm round. PLACEHOLDER size, set with the dock contact vendor (research/power-battery/POGO_CHARGING.md).",
   [(1, "circle", 0.0, 0.0, 2.6, 2.6)], (-1.3, -1.3, 1.3, 1.3), (-1.6, -1.6, 1.6, 1.6), tags="pogo charging")
# ---- Macronix MX25R3235F 8-land USON 4 x 3 x 0.6 mm, 0.8 mm pitch (datasheet rev 1.6 section 19-4): lead width 0.30, lead length 0.60.
# Land 0.35 x 0.90 mm, 0.2 mm outside the body. Pin 1 bottom left in the top view, counter-clockwise: 1-4 along the bottom, 5-8 along the top.
# The two exposed metal pads under the body are left without a pad (datasheet: float or ground, no vias or traces under them).
xs = [-1.2, -0.4, 0.4, 1.2]
pads = [(i + 1, "rect", xs[i], 1.3, 0.35, 0.9) for i in range(4)] + [(8 - i, "rect", xs[i], -1.3, 0.35, 0.9) for i in range(4)]
fp("MX25R3235F_USON-8_4x3mm_P0.8mm", "Macronix MX25R3235F 8-land USON 4x3 mm, 0.8 mm pitch. Land size 0.35 x 0.9 mm CHECK against Macronix land pattern. No pad for the exposed metal under the body: keep copper and vias away.",
   pads, (-2.0, -1.5, 2.0, 1.5), (-2.3, -1.9, 2.3, 1.9), pin1=(-2.2, 1.0), tags="flash nor macronix")

print("footprints written:", len(list(OUT.glob("*.kicad_mod"))))
