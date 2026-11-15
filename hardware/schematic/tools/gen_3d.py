"""Simple 3D bodies (boxes) for footprints that have no model in KiCad's library. python gen_3d.py -> ../libs/3dshapes/*.wrl
Sizes are the package outline of each datasheet (length x width x height, mm); they only show size and height, not the real shape.
The VRML is drawn in mm and used with a scale of 1/2.54 (KiCad reads VRML in 0.1 inch units).
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "libs" / "3dshapes"
OUT.mkdir(parents=True, exist_ok=True)
# name: (x, y, height, (r, g, b)); source of the size
BODIES = {
    "nRF54L15_QFN48_6x6": (6.0, 6.0, 0.85, (0.12, 0.12, 0.12)),            # nRF54L15 DS v1.0 table 83: D 6.0, A 0.85
    "MAX86141_WLP20": (2.048, 1.848, 0.5, (0.15, 0.15, 0.2)),               # DS: 2.048 x 1.848 mm; height not read, 0.5 mm assumed
    "MAX30208_TLGA10": (2.0, 2.0, 0.75, (0.12, 0.12, 0.12)),                # ADI: 2 x 2 x 0.75 mm
    "MX25R3235F_USON8": (4.0, 3.0, 0.6, (0.12, 0.12, 0.12)),                # DS rev 1.6 p.82: 4 x 3 x 0.6 (A 0.55)
    "OCVPB21_WLCSP13": (2.10, 1.32, 0.605, (0.2, 0.2, 0.25)),               # DS13107 sect 3.1: 2.1 x 1.32, 605 um
    "SFH7016": (1.85, 1.65, 0.6, (0.9, 0.9, 0.85)),                         # SFH 7016 v1.5 p.13: 1.85 x 1.65 x 0.6
    "VEMD8080": (4.8, 2.5, 0.48, (0.1, 0.1, 0.15)),                         # Vishay 84565 p.4: 4.8 x 2.5 x 0.48
    "Johanson_2450AT18A0100001E": (3.2, 1.6, 1.3, (0.75, 0.65, 0.45)),      # Johanson 36S0021A: 3.2 x 1.6 x 1.3
    "Crystal_2016": (2.0, 1.6, 0.45, (0.7, 0.7, 0.72)),                     # NDK NX2016SA: 2.0 x 1.6 x 0.45
    "Crystal_2012": (2.05, 1.2, 0.6, (0.7, 0.7, 0.72)),                     # Seiko SC-20S: 2.05 x 1.2 x 0.6 max
}


def wrl(x, y, h, c):
    x, y = x / 2, y / 2
    pts = f"{-x} {-y} 0, {x} {-y} 0, {x} {y} 0, {-x} {y} 0, {-x} {-y} {h}, {x} {-y} {h}, {x} {y} {h}, {-x} {y} {h}"
    faces = "0,3,2,1,-1, 4,5,6,7,-1, 0,1,5,4,-1, 1,2,6,5,-1, 2,3,7,6,-1, 3,0,4,7,-1"
    return (f"#VRML V2.0 utf8\nShape {{ appearance Appearance {{ material Material {{ diffuseColor {c[0]} {c[1]} {c[2]} }} }}\n"
            f"geometry IndexedFaceSet {{ coord Coordinate {{ point [ {pts} ] }} coordIndex [ {faces} ] }} }}\n")


for n, (x, y, h, c) in BODIES.items():
    (OUT / f"{n}.wrl").write_text(wrl(x, y, h, c), encoding="ascii")
print("3D bodies written:", len(BODIES))
