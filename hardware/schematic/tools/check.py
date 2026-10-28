"""Independent check of the generated schematic: python check.py

1. Runs KiCad ERC (kicad-cli) and lists what remains.
2. Exports the netlist and compares it with EXPECTED, which is typed from
   hardware/REQUIREMENTS_FROM_DATASHEETS.md and does not use build.py.
3. Compares the nRF54L15 symbol with the pin table extracted from the datasheet (data/nrf54l15_qfn48_pins.csv).
4. Compares stock footprint pad names with symbol pin numbers.
Exit code 1 if anything unexpected is found.
"""
import csv
import collections
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRJ = HERE.parent
CLI = r"C:/Users/TempAdmin/AppData/Local/Programs/KiCad/9.0/bin/kicad-cli.exe"
FPDIR = Path(r"C:/Users/TempAdmin/AppData/Local/Programs/KiCad/9.0/share/kicad/footprints")
(PRJ / "build").mkdir(exist_ok=True)
problems = []


def run(*args):
    subprocess.run([CLI, *args], capture_output=True, text=True, check=False)


# ------------------------------------------------------------------ expected, from the requirements document
def grp(**kw):
    return kw


EXPECTED_PINS = {
    "U1": {"+1V8": "47 48 10 22 36", "GND": "44 49", "DCC": "46", "DECD": "45", "DECA": "43 33", "VSS_PA": "32",
           "XC1": "34", "XC2": "35", "XL1": "1", "XL2": "2", "RF_ANT": "31", "SWDIO": "25", "SWDCLK": "26",
           "NRESET_MCU": "30", "PPG_INT": "23", "IMU_INT1": "24", "IMU_INT2": "27", "I2C_SDA": "28", "I2C_SCL": "29",
           "PMIC_IRQ": "9", "CS_FLASH": "11", "SPI_SCK": "12", "SPI_MOSI": "13", "TEMP_INT": "14", "SPI_MISO": "15",
           "CS_PPG": "16", "CHG_FLAG": "17", "SWO": "18", "LED_BOOST_EN": "19", "PPG_GPIO1": "20", "PPG_GPIO2": "21",
           "NC": "3 4 5 6 7 8 37 38 39 40 41 42"},
    "U2": {"VLED": "A1", "GND": "D3 C4 C3", "+1V8": "D2 C2", "VREF": "B5", "LED1_DRV": "D1", "LED2_DRV": "C1",
           "LED3_DRV": "B1", "PD1_IN": "D5", "PD2_IN": "D4", "PD_GND": "C5", "CS_PPG": "A5", "SPI_SCK": "A2",
           "SPI_MOSI": "A4", "SPI_MISO": "A3", "PPG_INT": "B2", "PPG_GPIO1": "B3", "PPG_GPIO2": "B4"},
    "D1": {"VLED": "2 5", "LED_G": "3", "LED_R": "4", "LED_IR": "1", "NC": "6"},
    "PD1": {"PD_GND": "5", "PD1_IN": "1 2 3 4 6 7 8"},
    "PD2": {"PD_GND": "5", "PD2_IN": "1 2 3 4 6 7 8"},
    "U3": {"+1V8": "8 5 12 2 3", "GND": "7 6 1", "I2C_SCL": "13", "I2C_SDA": "14", "IMU_INT1": "4", "IMU_INT2": "9",
           "NC": "10 11"},
    "U4": {"+1V8": "1 2 3", "GND": "4 5 6 7", "I2C_SDA": "8", "I2C_SCL": "9", "TEMP_INT": "10"},
    "U5": {"VSYS": "6", "LED_BOOST_EN": "4", "SW": "5", "GND": "1 7", "VLED_BOOST": "2 3"},
    "U6": {"POGO_A": "D1", "POGO_B": "D3", "RLIM": "E1", "CHG_FLAG": "E3", "VBUS_PROT": "B2", "GND": "A3 C3 E2",
           "NC": "C2 A2 B3 A1 B1"},
    "AE1": {"ANT_FEED": "1", "NC": "2"},
    "J3": {"+1V8": "1", "SWDIO": "2", "NRESET": "3", "SWDCLK": "4", "GND": "5", "SWO": "6"},
    "J1": {"POGO_A": "1"}, "J2": {"POGO_B": "1"},
    "X2": {"XC1": "1", "XC2": "3", "GND": "2 4"}, "X1": {"XL1": "1", "XL2": "2"},
}

# (value, net, net) for every two-pin part; counted, so the auto-numbered ones need no fixed reference.
PASSIVES = [
    ("2.2uF", "DECD", "GND"), ("2.2uF", "DECA", "GND"), ("10uF", "+1V8", "GND"), ("100nF", "+1V8", "GND"),
    ("100nF", "+1V8", "GND"), ("100nF", "+1V8", "GND"), ("100nF", "+1V8", "GND"), ("2.2nF", "DECA", "GND"),
    ("10nF", "DECA", "GND"), ("3.9pF", "NRESET_MCU", "GND"), ("1k", "NRESET_MCU", "NRESET"), ("4.7uH", "DCC", "DECD"),
    ("120R@100MHz", "DECD", "DECA"), ("NetTie", "VSS_PA", "GND"),
    ("2.7nH", "RF_ANT", "RF_A"), ("1.5pF", "RF_A", "VSS_PA"), ("3.5nH", "RF_A", "RF_B"), ("2.0pF", "RF_B", "GND_BOT"),
    ("3.5nH", "RF_B", "RF_C"), ("0.3pF", "RF_C", "GND"), ("NetTie", "GND_BOT", "GND"),
    ("0R", "RF_C", "ANT_A"), ("TBD", "ANT_A", "GND"), ("0R", "ANT_A", "ANT_FEED"),
    ("22uF", "+1V8", "GND"), ("100nF", "+1V8", "GND"), ("1uF", "VREF", "GND"), ("10uF", "VLED", "GND"),
    ("100k", "+1V8", "PPG_INT"), ("100k", "+1V8", "PPG_GPIO1"),
    ("0R", "LED_G", "LED1_DRV"), ("0R", "LED_IR", "LED2_DRV"), ("0R", "LED_R", "LED3_DRV"), ("NetTie", "PD_GND", "GND"),
    ("100nF", "+1V8", "GND"), ("100nF", "+1V8", "GND"), ("100nF", "+1V8", "GND"),
    ("4.7k", "+1V8", "I2C_SDA"), ("4.7k", "+1V8", "I2C_SCL"),
    ("1.0uH", "VSYS", "SW"), ("2.2uF", "VSYS", "GND"), ("10uF", "VLED_BOOST", "GND"), ("100k", "LED_BOOST_EN", "GND"),
    ("0R", "VLED_BOOST", "VLED"), ("0R", "VSYS", "VLED"),
    ("180R", "RLIM", "GND"), ("10uF", "VBUS_PROT", "GND"), ("100k", "+1V8", "CHG_FLAG"),
]
TEST_POINTS = ["+1V8", "VSYS", "VLED", "GND", "GND", "I2C_SDA", "I2C_SCL", "SPI_SCK", "SPI_MOSI", "SPI_MISO", "PPG_INT"]
KNOWN_ERC = {("error", "label_dangling"): 4}   # PMIC_IRQ and CS_FLASH: other end is on a sheet whose datasheet is pending


def norm(name):
    return name.rsplit("/", 1)[-1] if name else name


# ------------------------------------------------------------------ 1. ERC
run("sch", "erc", "--format", "json", "--severity-all", "-o", str(PRJ / "build/erc.json"), str(PRJ / "smartwatch.kicad_sch"))
erc = json.load(open(PRJ / "build/erc.json"))
counts = collections.Counter()
for sh in erc["sheets"]:
    for v in sh["violations"]:
        counts[(v["severity"], v["type"])] += 1
for k, n in counts.items():
    if KNOWN_ERC.get(k) != n:
        problems.append(f"ERC {k}: {n} (expected {KNOWN_ERC.get(k, 0)})")
print("ERC:", dict(counts))

# ------------------------------------------------------------------ 2. netlist
run("sch", "export", "netlist", "--format", "kicadxml", "-o", str(PRJ / "build/smartwatch.xml"), str(PRJ / "smartwatch.kicad_sch"))
root = ET.parse(PRJ / "build/smartwatch.xml").getroot()
comp = {c.get("ref"): c for c in root.iter("comp")}
pin_net = {}
net_nodes = collections.defaultdict(list)
for net in root.iter("net"):
    nm = net.get("name")
    for nd in net.iter("node"):
        pin_net[(nd.get("ref"), nd.get("pin"))] = nm
        net_nodes[nm].append((nd.get("ref"), nd.get("pin")))

for ref, groups in EXPECTED_PINS.items():
    if ref not in comp:
        problems.append(f"missing part {ref}")
        continue
    seen = set()
    for net, pins in groups.items():
        for p in pins.split():
            seen.add(p)
            got = pin_net.get((ref, p))
            if net == "NC":
                if got is not None and not got.startswith("unconnected-"):
                    problems.append(f"{ref}.{p} should be unconnected, is on {got}")
            elif got is None or norm(got) != net:
                problems.append(f"{ref}.{p} expected {net}, netlist has {got}")
print("pin check done for", len(EXPECTED_PINS), "parts")

# every pin of the checked ICs is covered by the expected table
for ref in ("U1", "U2", "U3", "U4", "U5", "U6", "D1", "PD1", "PD2", "AE1", "J3"):
    c = comp[ref]
    lib = c.find("libsource").get("part")
    # pins of the symbol come from the netlist nodes plus unconnected nets; compare counts instead
    got = {p for (r, p) in pin_net if r == ref}
    want = {p for pins in EXPECTED_PINS[ref].values() for p in pins.split()}
    if got - want:
        problems.append(f"{ref}: pins in netlist but not in expected table: {sorted(got - want)}")

# passives
have = collections.Counter()
tps = []
for ref, c in comp.items():
    if re.match(r"^(C|R|L|FB|NT)\d+$", ref):
        val = c.find("value").text or ""
        nets = [norm(pin_net.get((ref, p), "?")) for p in ("1", "2")]
        have[(val, *sorted(nets))] += 1
    elif ref.startswith("TP"):
        tps.append(norm(pin_net.get((ref, "1"), "?")))
want = collections.Counter((v, *sorted((a, b))) for v, a, b in PASSIVES)
for k in set(have) | set(want):
    if have[k] != want[k]:
        problems.append(f"passive {k}: netlist {have[k]}, expected {want[k]}")
if sorted(tps) != sorted(TEST_POINTS):
    problems.append(f"test points differ: {sorted(tps)} vs {sorted(TEST_POINTS)}")
print("passives:", sum(have.values()), "in netlist,", sum(want.values()), "expected")

# floating nets
KNOWN_SINGLE = {"CS_FLASH", "PMIC_IRQ"}     # other end on the power and memory sheets (datasheets pending)
for nm, nodes in net_nodes.items():
    if len(nodes) < 2 and not nm.startswith("unconnected-") and norm(nm) not in KNOWN_SINGLE:
        problems.append(f"net {nm} has a single pin: {nodes}")

# ------------------------------------------------------------------ 3. nRF54L15 pin table
rows = list(csv.DictReader(open(PRJ / "data/nrf54l15_qfn48_pins.csv", encoding="utf-8")))
sys.path.insert(0, str(HERE))
from kigen import parse, find
tree = parse((PRJ / "libs/smartwatch.kicad_sym").read_text(encoding="utf-8"))
nrf = [s for s in find(tree, "symbol") if s[1] == "nRF54L15-QFAA"][0]
sym_pins = {}
for sub in find(nrf, "symbol"):
    for p in find(sub, "pin"):
        sym_pins[find(p, "number")[0][1]] = find(p, "name")[0][1]
for r in rows:
    pin = r["pin"]
    ds_name = r["name"].split(" | ")[0].strip()
    if pin not in sym_pins:
        problems.append(f"nRF54L15 pin {pin} ({ds_name}) missing from symbol")
    elif not sym_pins[pin].startswith(ds_name):
        problems.append(f"nRF54L15 pin {pin}: datasheet name {ds_name!r}, symbol name {sym_pins[pin]!r}")
extra = set(sym_pins) - {r["pin"] for r in rows}
if extra:
    problems.append(f"nRF54L15 symbol has pins not in the datasheet table: {sorted(extra)}")
print("nRF54L15 symbol:", len(sym_pins), "pins vs datasheet table:", len(rows))

# ------------------------------------------------------------------ 4. stock footprint pads vs symbol pins
def pads(path):
    t = Path(path).read_text(encoding="utf-8")
    return {m.group(1) for m in re.finditer(r'\(pad "([^"]+)"', t)}


CUSTOM = PRJ / "libs/smartwatch.pretty"
for ref, fp in (("U1", "Package_DFN_QFN.pretty/QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm"),
                ("U3", "Package_LGA.pretty/Bosch_LGA-14_3x2.5mm_P0.5mm"),
                ("U5", "Package_SON.pretty/WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm"),
                ("X2", "Crystal.pretty/Crystal_SMD_2016-4Pin_2.0x1.6mm"), ("X1", "Crystal.pretty/Crystal_SMD_2012-2Pin_2.0x1.2mm"),
                ("J3", "Connector.pretty/Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical"),
                ("U2", "@MAX86141_WLP-20_2.048x1.848mm_P0.4mm"), ("U4", "@MAX30208_TLGA-10_2x2mm"),
                ("U6", "@OCVPB21-13F6_WLCSP-13_P0.4mm"), ("D1", "@SFH7016_1.85x1.65mm"), ("PD1", "@VEMD8080_4.8x2.5mm"),
                ("PD2", "@VEMD8080_4.8x2.5mm"), ("AE1", "@Johanson_2450AT18A0100001E_1206"), ("J1", "@Pogo_Pad_D2.6mm")):
    path = CUSTOM / (fp[1:] + ".kicad_mod") if fp.startswith("@") else FPDIR / (fp + ".kicad_mod")
    have_pads = pads(path)
    sym_p = {p for (r, p) in pin_net if r == ref}
    if sym_p - have_pads:
        problems.append(f"{ref}: symbol pins without a footprint pad: {sorted(sym_p - have_pads)}")
    if have_pads - sym_p:
        print(f"note {ref}: footprint pads not in symbol: {sorted(have_pads - sym_p)}")
    used = comp[ref].find("footprint").text or ""
    if used.split(":")[-1] != Path(fp.lstrip("@")).name:
        problems.append(f"{ref}: schematic footprint {used!r} differs from the checked file {Path(fp.lstrip(chr(64))).name!r}")

print()
if problems:
    print("PROBLEMS:")
    for p in problems:
        print(" -", p)
    sys.exit(1)
print("ALL CHECKS PASSED")
