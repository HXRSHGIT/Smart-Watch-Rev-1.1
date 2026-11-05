"""Preview one drawn sheet:  python dev.py sensors [A4|A3]  ->  build/dev/<name>.png  (and prints ERC findings)."""
import importlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import parts
from draw import Drawing
from kigen import Lib, Registry, uid

PRJ = Path(__file__).resolve().parent.parent
CLI = r"C:/Users/TempAdmin/AppData/Local/Programs/KiCad/9.0/bin/kicad-cli.exe"


def make_lib():
    lib = Lib()
    for n in ("C_Small", "R_Small", "L_Small", "FerriteBead_Small", "Crystal_Small", "Crystal_GND24", "NetTie_2"):
        lib.add_stock("Device", n)
    lib.add_stock("Connector", "TestPoint")
    lib.add_stock("Connector_Generic", "Conn_01x01")
    lib.add_stock("power", "PWR_FLAG")
    lib.add_stock("Switch", "SW_SPST")
    for fn in parts.ALL:
        lib.add_custom("smartwatch", fn())
    return lib


if __name__ == "__main__":
    name = sys.argv[1]
    paper = sys.argv[2] if len(sys.argv) > 2 else "A4"
    out = PRJ / "build" / "dev"
    out.mkdir(parents=True, exist_ok=True)
    lib, reg = make_lib(), Registry()
    d = Drawing(lib, reg, uid(), None, name, paper=paper)
    importlib.import_module(f"sheets.{name}").draw(d)
    f = out / f"{name}.kicad_sch"
    f.write_text(d.render(), encoding="utf-8")
    subprocess.run([CLI, "sch", "erc", "--format", "json", "--severity-all", "-o", str(out / "erc.json"), str(f)],
                   capture_output=True)
    erc = json.load(open(out / "erc.json"))
    for s in erc["sheets"]:
        for v in s["violations"]:
            if v["type"] not in ("power_pin_not_driven", "label_dangling"):
                print(v["severity"], v["type"], "|", v["description"][:70], "|",
                      [i["description"][:60] for i in v["items"]][:2])
    subprocess.run([CLI, "sch", "export", "pdf", "-o", str(out / f"{name}.pdf"), str(f)], capture_output=True)
    import pymupdf
    doc = pymupdf.open(out / f"{name}.pdf")
    doc[0].get_pixmap(dpi=int(sys.argv[3]) if len(sys.argv) > 3 else 130).save(out / f"{name}.png")
    print("wrote", out / f"{name}.png", "| labels:", d.labels, "| wires:", len(d.segs))
