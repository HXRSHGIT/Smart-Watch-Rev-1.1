"""Shared helpers for the drawn sheets."""
import math

U = 1.27          # grid unit, mm

FP = {
    "C": {"0201": "Capacitor_SMD:C_0201_0603Metric", "0402": "Capacitor_SMD:C_0402_1005Metric",
          "0603": "Capacitor_SMD:C_0603_1608Metric"},
    "R": {"0201": "Resistor_SMD:R_0201_0603Metric", "0402": "Resistor_SMD:R_0402_1005Metric"},
    "L": {"0201": "Inductor_SMD:L_0201_0603Metric", "0402": "Inductor_SMD:L_0402_1005Metric",
          "0603": "Inductor_SMD:L_0603_1608Metric", "0805": "Inductor_SMD:L_0805_2012Metric"},
}
XTAL4 = "Crystal:Crystal_SMD_2016-4Pin_2.0x1.6mm"
XTAL2 = "Crystal:Crystal_SMD_2012-2Pin_2.0x1.2mm"
TP_FP = "TestPoint:TestPoint_Pad_D1.0mm"


def P(a, b):
    """Grid units to mm."""
    return (a * U, b * U)


def part(d, kind, ref, value, pkg, x, y, spec="", src="", rot=0, dnp=False, mpn="", tside="R"):
    """Two-pin passive at grid position (x, y) in grid units. Pins: vertical parts have pin 1 up, horizontal
    (rot 90) have pin 1 left."""
    sym = {"C": "Device:C_Small", "R": "Device:R_Small", "L": "Device:L_Small", "FB": "Device:FerriteBead_Small"}[kind]
    fp = FP["L" if kind == "FB" else kind][pkg]
    props = {"Spec": spec, "Source": src}
    if mpn:
        props["MPN"] = mpn
    return d.put(sym, x * U, y * U, rot, ref=ref, value=value, footprint=fp, props=props, dnp=dnp, tside=tside)


def note(d, text, x, y, w_mm, min_lines=2):
    """Blue note box; height follows the text length."""
    chars = max(20, int(w_mm / 1.1))
    lines = max(min_lines, sum(max(1, math.ceil(len(par) / chars)) for par in text.split("\n")))
    d.note(text, x, y, w_mm, lines * 2.0 + 2.2)
    return lines * 2.0 + 2.2
