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
    "U7": {"VBUS_PROT": "21", "GND": "23 24 16 28 29 30 31 6 33", "VBAT": "19", "NTC": "18", "VSET1": "17", "SHPHLD": "15",
           "I2C_SCL": "14", "I2C_SDA": "13", "+1V8": "12 1", "VBUSOUT": "22", "VSYS": "20 4 32", "SW1": "3", "PVSS1": "2",
           "PMIC_IRQ": "8", "NC": "5 7 9 10 11 25 26 27"},
    "U8": {"+1V8": "8", "GND": "4", "CS_FLASH": "1", "SPI_SCK": "6", "SPI_MOSI": "5", "SPI_MISO": "2", "NC": "3 7"},
    "J4": {"VBAT": "1", "NTC": "2", "GND": "3"},
    "J1": {"POGO_A": "1"}, "J2": {"POGO_B": "1"},
    "X2": {"XC1": "1", "XC2": "3", "GND": "2 4"}, "X1": {"XL1": "1", "XL2": "2"},
}

# Every two-pin part by reference: (net on pin 1, net on pin 2). Typed from the datasheet network figures, not from build.py.
EXPECTED_2PIN = {
    # processor (nRF54L15 Fig 180 / Table 87)
    "C3": ("+1V8", "GND"), "C10": ("+1V8", "GND"), "C4": ("+1V8", "GND"), "C7": ("+1V8", "GND"), "C8": ("+1V8", "GND"),
    "L1": ("DCC", "DECD"), "C1": ("DECD", "GND"), "FB1": ("DECD", "DECA"),
    "C2": ("DECA", "GND"), "C12": ("DECA", "GND"), "C5": ("DECA", "GND"),
    "R1": ("NRESET_MCU", "NRESET"), "C13": ("NRESET_MCU", "GND"), "NT1": ("VSS_PA", "GND"),
    # RF
    "L2": ("RF_ANT", "RF_A"), "C6": ("RF_A", "VSS_PA"), "L3": ("RF_A", "RF_B"), "C9": ("RF_B", "GND_BOT"),
    "NT2": ("GND_BOT", "GND"), "L4": ("RF_B", "RF_C"), "C11": ("RF_C", "GND"),
    "R2": ("RF_C", "ANT_A"), "C14": ("ANT_A", "GND"), "R3": ("ANT_A", "ANT_FEED"),
    # optical
    "C15": ("+1V8", "GND"), "C16": ("+1V8", "GND"), "C17": ("VREF", "GND"), "C18": ("VLED", "GND"),
    "R4": ("+1V8", "PPG_INT"), "R5": ("+1V8", "PPG_GPIO1"),
    "R6": ("LED_G", "LED1_DRV"), "R7": ("LED_IR", "LED2_DRV"), "R8": ("LED_R", "LED3_DRV"), "NT3": ("PD_GND", "GND"),
    # sensors
    "C19": ("+1V8", "GND"), "C20": ("+1V8", "GND"), "C21": ("+1V8", "GND"),
    "R9": ("+1V8", "I2C_SCL"), "R10": ("+1V8", "I2C_SDA"),
    # LED supply
    "L5": ("VSYS", "SW"), "C22": ("VSYS", "GND"), "C23": ("VLED_BOOST", "GND"), "R11": ("LED_BOOST_EN", "GND"),
    "R12": ("VLED_BOOST", "VLED"), "R13": ("VSYS", "VLED"),
    # charging input
    "R14": ("RLIM", "GND"), "C24": ("VBUS_PROT", "GND"), "R15": ("+1V8", "CHG_FLAG"),
    # power (nPM1300 PS v1.3, reference circuitry configuration 2)
    "C25": ("VBUS_PROT", "GND"), "C26": ("VBUSOUT", "GND"), "C27": ("VSYS", "PVSS1"), "C28": ("VSYS", "GND"),
    "C29": ("+1V8", "PVSS1"), "C30": ("VBAT", "GND"), "C31": ("+1V8", "GND"), "L6": ("SW1", "+1V8"),
    "R16": ("VSET1", "GND"), "R17": ("NTC", "GND"), "NT4": ("PVSS1", "GND"), "SW1": ("SHPHLD", "GND"),
    # memory (MX25R3235F rev 1.6)
    "C32": ("+1V8", "GND"), "R18": ("+1V8", "CS_FLASH"),
}
EXPECTED_VALUES = {"R12": "0R", "R13": "0R", "R11": "100k", "R14": "180R", "C14": "TBD", "L5": "1.0uH", "C6": "1.5pF",
                   "C9": "2.0pF", "C11": "0.3pF", "L2": "2.7nH", "L3": "3.5nH", "L4": "3.5nH", "C3": "10uF", "C13": "3.9pF",
                   "R16": "47k", "L6": "2.2uH", "C25": "1uF", "C26": "1uF", "C27": "10uF", "C28": "10uF", "C29": "10uF", "C30": "2.2uF",
                   "C31": "100nF", "R17": "10k", "R18": "100k", "C32": "100nF"}
EXPECTED_TP = {"TP1": "+1V8", "TP2": "VSYS", "TP3": "VLED", "TP4": "GND", "TP5": "GND", "TP6": "I2C_SDA", "TP7": "I2C_SCL",
               "TP8": "SPI_SCK", "TP9": "SPI_MOSI", "TP10": "SPI_MISO", "TP11": "PPG_INT"}
KNOWN_ERC = {}


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

want_net = {}                       # (ref, pin) -> expected net name; NC pins are listed apart
nc_pins = set()
for ref, groups in EXPECTED_PINS.items():
    if ref not in comp:
        problems.append(f"missing part {ref}")
        continue
    for net, pins in groups.items():
        for p in pins.split():
            (nc_pins.add((ref, p)) if net == "NC" else want_net.__setitem__((ref, p), net))
pending = {r: v for r, v in EXPECTED_2PIN.items() if r in comp}
for r in EXPECTED_2PIN:
    if r not in comp:
        problems.append(f"missing part {r}")
for ref, net in EXPECTED_TP.items():
    if ref not in comp:
        problems.append(f"missing part {ref}")
        continue
    want_net[(ref, "1")] = net
for ref, val in EXPECTED_VALUES.items():
    if ref in comp and (comp[ref].find("value").text or "") != val:
        problems.append(f"{ref}: value {comp[ref].find('value').text!r}, expected {val!r}")

# Two-pin parts have no pin order that matters: pick the orientation that agrees with nets already known, chain by chain.
name_net = {}
for k, v in want_net.items():
    name_net.setdefault(v, set()).add(pin_net.get(k))
name_net = {n: next(iter(a)) for n, a in name_net.items() if len(a) == 1}     # split nets are reported below
progress = True
while pending and progress:
    progress = False
    for ref, (n1, n2) in list(pending.items()):
        a1, a2 = pin_net.get((ref, "1")), pin_net.get((ref, "2"))
        ok = [o for o in (((n1, a1), (n2, a2)), ((n1, a2), (n2, a1)))
              if all(name_net.get(n, a) == a for n, a in o)]
        known = any(n in name_net for n in (n1, n2))
        if not ok:
            problems.append(f"{ref}: nets {a1} / {a2} do not match the expected {n1} / {n2}")
            del pending[ref]
            progress = True
        elif known and len(ok) == 1 or len(ok) == 2 and all(n in name_net for n in (n1, n2)):
            (m1, b1), (m2, b2) = ok[0]
            name_net[m1], name_net[m2] = b1, b2
            want_net[(ref, "1" if b1 == a1 else "2")], want_net[(ref, "2" if b1 == a1 else "1")] = m1, m2
            del pending[ref]
            progress = True
for ref in pending:
    problems.append(f"{ref}: could not tell which expected nets it joins (unknown on both sides)")

# 2a. every pin of every part is accounted for, in both directions
for (ref, p) in sorted(pin_net):
    if ref.startswith("#"):
        continue
    if (ref, p) not in want_net and (ref, p) not in nc_pins and not pin_net[(ref, p)].startswith("unconnected-"):
        problems.append(f"{ref}.{p} is connected to {pin_net[(ref, p)]} but is not in the expected tables")
for (ref, p), net in want_net.items():
    if (ref, p) not in pin_net:
        problems.append(f"{ref}.{p} should be on {net} but is not connected to anything")
for (ref, p) in nc_pins:
    got = pin_net.get((ref, p))
    if got is not None and not got.startswith("unconnected-"):
        problems.append(f"{ref}.{p} should be unconnected, is on {got}")

# 2b. connectivity: pins that share an expected net share an actual net; different expected nets never merge
by_name = collections.defaultdict(list)
for k, v in want_net.items():
    by_name[v].append(k)
actual_of = {}
for name, pins in by_name.items():
    nets = {pin_net.get(k) for k in pins}
    if len(nets) != 1:
        problems.append(f"net {name} is split: " + "; ".join(f"{k[0]}.{k[1]} on {pin_net.get(k)}" for k in pins))
    else:
        actual_of[name] = nets.pop()
back = collections.defaultdict(list)
for name, a in actual_of.items():
    back[a].append(name)
for a, names in back.items():
    if len(names) > 1:
        problems.append(f"nets {names} are merged into {a}")
print("pin check:", len(want_net), "pins on", len(by_name), "nets;", len(nc_pins), "unconnected by design")

# floating nets: a net with one pin is a mistake
KNOWN_SINGLE = set()
for nm, nodes in net_nodes.items():
    nodes = [n for n in nodes if not n[0].startswith("#")]
    if len(nodes) < 2 and not nm.startswith("unconnected-") and norm(nm) not in KNOWN_SINGLE:
        problems.append(f"net {nm} has a single pin: {nodes}")

# ------------------------------------------------------------------ 3. nRF54L15 pin table
ALIAS = {"49": "VSS_EP"}     # datasheet calls the exposed pad VSS (exposed pad)
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
    elif not sym_pins[pin].startswith(ds_name) and sym_pins[pin] != ALIAS.get(pin):
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
                ("U7", "Package_DFN_QFN.pretty/QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm"), ("U8", "@MX25R3235F_USON-8_4x3mm_P0.8mm"),
                ("J4", "Connector_JST.pretty/JST_SH_SM03B-SRSS-TB_1x03-1MP_P1.00mm_Horizontal"),
                ("SW1", "Button_Switch_SMD.pretty/SW_SPST_B3U-1000P"),
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
