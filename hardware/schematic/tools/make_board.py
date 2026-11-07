"""Make smartwatch.kicad_pcb from the schematic: footprints, nets and symbol links exactly as KiCad's own netlist has them.

Run with KiCad's Python (it has pcbnew):
  "%LOCALAPPDATA%/Programs/KiCad/9.0/bin/python.exe" tools/make_board.py [out.kicad_pcb]
Footprints are laid out in a loose grid so nothing overlaps; placement is done afterwards.
"""
import os, re, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)                                  # hardware/schematic
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PRJ, "build", "smartwatch.kicad_pcb")
CLI = os.path.join(os.path.dirname(sys.executable), "kicad-cli.exe")
KB = os.path.dirname(os.path.dirname(sys.executable))        # .../KiCad/9.0
VARS = {"KIPRJMOD": PRJ, "KICAD9_FOOTPRINT_DIR": os.path.join(KB, "share", "kicad", "footprints")}


def lib_table(path):
    if not os.path.exists(path):
        return {}
    txt = open(path, encoding="utf-8").read()
    libs = {}
    for name, uri in re.findall(r'\(lib \(name "([^"]+)"\)\(type [^)]*\)\(uri "([^"]+)"\)', txt):
        libs[name] = re.sub(r"\$\{(\w+)\}", lambda m: VARS.get(m.group(1), m.group(0)), uri)
    return libs


libs = lib_table(os.path.join(os.environ.get("APPDATA", ""), "kicad", "9.0", "fp-lib-table"))
libs.update(lib_table(os.path.join(PRJ, "fp-lib-table")))   # project libraries win
for nick in ("Capacitor_SMD", "Resistor_SMD"):               # global table may only point at the template
    libs.setdefault(nick, os.path.join(VARS["KICAD9_FOOTPRINT_DIR"], nick + ".pretty"))

xml = os.path.join(tempfile.gettempdir(), "smartwatch_netlist.xml")
subprocess.run([CLI, "sch", "export", "netlist", "--format", "kicadxml", "--output", xml,
                os.path.join(PRJ, "smartwatch.kicad_sch")], check=True, capture_output=True)
root = ET.parse(xml).getroot()

board = pcbnew.BOARD()
fps = {}
for i, c in enumerate(root.findall("./components/comp")):
    ref, value, fpid = c.get("ref"), c.findtext("value", ""), c.findtext("footprint", "")
    nick, name = fpid.split(":", 1)
    # an unknown library is a hard error: a silent skip would give a board with missing parts
    fp = pcbnew.FootprintLoad(libs[nick] if nick in libs else os.path.join(VARS["KICAD9_FOOTPRINT_DIR"], nick + ".pretty"), name)
    assert fp is not None, f"{ref}: footprint {fpid} not found"
    fp.SetFPID(pcbnew.LIB_ID(nick, name))
    fp.SetReference(ref)
    fp.SetValue(value)
    sp = c.find("sheetpath").get("tstamps", "/")
    fp.SetPath(pcbnew.KIID_PATH(sp + c.findtext("tstamps", "").split(",")[0]))
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(5 + (i % 12) * 7), pcbnew.FromMM(5 + (i // 12) * 7)))
    board.Add(fp)
    fps[ref] = fp

nets = board.GetNetInfo()
for n in root.findall("./nets/net"):
    item = pcbnew.NETINFO_ITEM(board, n.get("name"))
    board.Add(item)
    for node in n.findall("node"):
        pad = fps[node.get("ref")].FindPadByNumber(node.get("pin"))
        assert pad is not None, f"{node.get('ref')} has no pad {node.get('pin')}"
        pad.SetNet(item)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
pcbnew.SaveBoard(OUT, board)
print(f"{OUT}: {len(fps)} footprints, {len(root.findall('./nets/net'))} nets")
