import sys
sys.path.insert(0, '.')
import parts
from kigen import Lib, xform
lib = Lib()
for fn in parts.ALL:
    lib.add_custom("smartwatch", fn())
want = sys.argv[1:]
for libid in sorted(lib.text):
    name = libid.split(":")[1]
    if want and name not in want:
        continue
    pins = lib.pins(libid)
    print("==", libid)
    for (u, n), (x, y, a, nm, t) in sorted(pins.items(), key=lambda kv: (kv[0][0], kv[1][1] * -1, kv[1][0])):
        dx, dy = xform(x, y, 0)
        print(f"  unit{u} pin {n:>3} {nm:<22} dx={dx:7.2f} dy={dy:7.2f}")
