"""Write PIN_MAP.md and BOM.csv from the exported netlist.  python pinmap.py  (run check.py first)"""
import collections
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

PRJ = Path(__file__).resolve().parent.parent
root = ET.parse(PRJ / "build/smartwatch.xml").getroot()
comp = {c.get("ref"): c for c in root.iter("comp")}
nets = {}
for net in root.iter("net"):
    nets[net.get("name")] = [(n.get("ref"), n.get("pin"), n.get("pinfunction") or "") for n in net.iter("node")]
where = {(r, p): nm for nm, nodes in nets.items() for (r, p, _) in nodes}


def short(n):
    return n.rsplit("/", 1)[-1]


def pin_key(p):
    return (0, int(p), "") if p.isdigit() else (1, 0, p)


out = ["# Pin map\n", "\nProduced by `tools/pinmap.py` from the KiCad netlist. Do not edit by hand.\n"]
for ref in ("U1", "U2", "U3", "U4", "U5", "U6", "D1", "PD1", "PD2", "AE1", "J1", "J2", "J3"):
    c = comp[ref]
    out.append(f"\n## {ref}  {c.find('value').text}  ({(c.find('footprint').text or '').split(':')[-1]})\n")
    out.append("\n| Pin | Name | Net | Also connected to |\n|---|---|---|---|\n")
    pins = sorted({p for (r, p) in where if r == ref}, key=pin_key)
    for p in pins:
        nm = where[(ref, p)]
        nodes = nets[nm]
        fn = next(f for (r, pp, f) in nodes if r == ref and pp == p)
        others = [f"{r}.{pp}" for (r, pp, _) in nodes if (r, pp) != (ref, p) and not r.startswith("#")]
        net = "(not connected)" if nm.startswith("unconnected-") else short(nm)
        out.append(f"| {p} | {fn} | {net} | {', '.join(others[:10])}{' ...' if len(others) > 10 else ''} |\n")
(PRJ / "PIN_MAP.md").write_text("".join(out), encoding="utf-8")

rows = []
for ref, c in comp.items():
    if ref.startswith("#"):
        continue
    props = {p.get("name"): p.text for p in c.iter("field")}
    rows.append([ref, c.find("value").text, (c.find("footprint").text or ""), props.get("Spec", ""), props.get("MPN", ""),
                 props.get("Source", ""), "DNP" if (props.get("Spec", "").find("DNP") >= 0 or (c.find("value").text or "") == "TBD") else ""])


def keyf(r):
    import re
    m = re.match(r"([A-Za-z]+)(\d+)", r[0])
    return (m.group(1), int(m.group(2)))


rows.sort(key=keyf)
with open(PRJ / "BOM.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Reference", "Value", "Footprint", "Spec", "MPN", "Source", "Note"])
    w.writerows(rows)
print("PIN_MAP.md and BOM.csv written:", len(rows), "parts")
