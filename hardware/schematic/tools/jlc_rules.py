"""Write the JLCPCB multilayer design rules into smartwatch.kicad_pro (python tools/jlc_rules.py).

Source: jlcpcb.com/capabilities/pcb-capabilities, read 2026-11-13. The values are JLCPCB's absolute minimums, so DRC flags
only real fab violations. Run it after KiCad has written the project file once (it patches that structure, it does not
invent one). KiCad's own Python API rewrites the project file with defaults when a board is loaded from this folder, so
check the rules with kicad-cli only, and re-run this script if smartwatch.kicad_pro was reset.
"""
import json
from pathlib import Path

PRO = Path(__file__).resolve().parent.parent / "smartwatch.kicad_pro"
p = json.loads(PRO.read_text(encoding="utf-8"))

p["board"]["design_settings"]["rules"].update({
    "min_clearance": 0.09,            # multilayer track/space 0.09 mm; BGA pad to trace 0.09 mm
    "min_track_width": 0.09,
    "min_via_diameter": 0.25,         # 0.15 mm hole / 0.25 mm copper (0.1 / 0.2 only below 1 mm, ENIG, extra cost)
    "min_through_hole_diameter": 0.15,
    "min_via_annular_width": 0.1,
    "min_hole_clearance": 0.2,        # via hole to track
    "min_hole_to_hole": 0.25,
    "min_copper_edge_clearance": 0.2,
    "min_silk_clearance": 0.15,       # pad to silkscreen
    "min_text_height": 1.0,
    "min_text_thickness": 0.15,
})
ds = p["board"]["design_settings"]
ds["track_widths"] = [0.0, 0.09, 0.1, 0.15, 0.2, 0.3, 0.5]
ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.45, "drill": 0.2}, {"diameter": 0.3, "drill": 0.15}]
ds["defaults"]["solder_mask_min_width"] = 0.1      # mask bridge 0.10 mm (green)

classes = {c["name"]: c for c in p["net_settings"]["classes"]}
default = classes["Default"]
default.update({"clearance": 0.1, "track_width": 0.1, "via_diameter": 0.45, "via_drill": 0.2})
power = dict(default, name="Power", track_width=0.3, priority=0)
p["net_settings"]["classes"] = [default, power]
p["net_settings"]["netclass_patterns"] = [{"netclass": "Power", "pattern": n}
                                          for n in ("VSYS", "VBUS_PROT", "+1V8", "VLED", "VLED_BOOST", "VBAT")]
PRO.write_text(json.dumps(p, indent=2) + "\n", encoding="utf-8")
print("rules written to", PRO)
