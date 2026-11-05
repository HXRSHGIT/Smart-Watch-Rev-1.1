"""Build the Smart Watch KiCad project: python build.py   (writes ../smartwatch.* and ../libs/*)

Every sheet is drawn by tools/sheets/<name>.py with the hand-drawing toolkit (draw.py); the style rules are in
../STYLE_GUIDE.md. Connections follow hardware/REQUIREMENTS_FROM_DATASHEETS.md; check.py re-verifies them.
"""
import csv
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import parts
from draw import Drawing
from kigen import Lib, Registry, uid, write_symbol_lib, PROJECT

OUT = Path(__file__).resolve().parent.parent

# sheet name -> (title, paper, page number)
SHEETS = {
    "input_protection": ("Charging input", "A4", 2),
    "power": ("Power nPM1300", "A3", 3),
    "led_supply": ("LED supply", "A4", 4),
    "mcu": ("Processor nRF54L15", "A3", 5),
    "memory": ("Flash memory", "A4", 6),
    "rf": ("RF match and antenna", "A4", 7),
    "optical": ("Optical sensing", "A4", 8),
    "sensors": ("Motion and temperature", "A4", 9),
    "test": ("Test and programming", "A4", 10),
}


def make_lib():
    lib = Lib()
    for n in ("C_Small", "R_Small", "L_Small", "FerriteBead_Small", "Crystal_Small", "Crystal_GND24", "NetTie_2"):
        lib.add_stock("Device", n)
    lib.add_stock("Connector", "TestPoint")
    lib.add_stock("Connector_Generic", "Conn_01x01")
    lib.add_stock("power", "PWR_FLAG")
    lib.add_stock("Switch", "SW_SPST")
    return lib


def main():
    lib, reg = make_lib(), Registry()
    sym_blocks = [fn() for fn in parts.ALL]
    for b in sym_blocks:
        lib.add_custom("smartwatch", b)
    root_id = uid()
    block = {n: uid() for n in SHEETS}
    drawn = {}
    for name, (title, paper, _) in SHEETS.items():
        d = Drawing(lib, reg, root_id, block[name], title, paper=paper)
        importlib.import_module(f"sheets.{name}").draw(d)
        drawn[name] = d
    ports = {n: sorted(set(d.ports)) for n, d in drawn.items()}

    root = Drawing(lib, reg, root_id, None, "HealthOS Band main board", paper="A3")
    ids = {"uuid": block, "pages": {n: v[2] for n, v in SHEETS.items()}}
    importlib.import_module("sheets.root").draw(root, ids)

    (OUT / "libs").mkdir(exist_ok=True)
    write_symbol_lib(OUT / "libs" / "smartwatch.kicad_sym", sym_blocks)
    (OUT / "sym-lib-table").write_text(
        '(sym_lib_table\n\t(version 7)\n\t(lib (name "smartwatch")(type "KiCad")(uri "${KIPRJMOD}/libs/smartwatch.kicad_sym")(options "")(descr "Smart Watch chip symbols"))\n)\n',
        encoding="utf-8")
    (OUT / "fp-lib-table").write_text(
        '(fp_lib_table\n\t(version 7)\n\t(lib (name "smartwatch")(type "KiCad")(uri "${KIPRJMOD}/libs/smartwatch.pretty")(options "")(descr "Smart Watch footprints"))\n)\n',
        encoding="utf-8")
    (OUT / f"{PROJECT}.kicad_pro").write_text(json.dumps({"meta": {"filename": f"{PROJECT}.kicad_pro", "version": 3}}, indent=2),
                                              encoding="utf-8")
    (OUT / f"{PROJECT}.kicad_sch").write_text(root.render(), encoding="utf-8")
    for name, d in drawn.items():
        (OUT / f"{name}.kicad_sch").write_text(d.render(), encoding="utf-8")
    json.dump(ports, open(OUT / "build" / "ports.json", "w") if (OUT / "build").exists() else open(OUT / "ports.json", "w"), indent=1)
    print("wrote", len(drawn) + 1, "sheets;", len(reg.used), "references;",
          sum(d.labels for d in drawn.values()) + root.labels, "net labels")


if __name__ == "__main__":
    main()
