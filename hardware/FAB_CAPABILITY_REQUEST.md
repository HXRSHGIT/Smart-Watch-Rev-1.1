# Fab capability request (draft, not sent)

Status 2026-11-13: JLCPCB was chosen and the design rules are now in `JLCPCB_DESIGN_RULES.md`. This draft stays as the background and as a question list if JLCPCB has to confirm something in writing.

Done by Harsh Thakur.

Purpose: choose the PCB fab and its design rules before routing. Nothing here has been sent to a fab. The stack-up, via and trace rules in KiCad stay provisional until a fab confirms them in writing.

## 1. What our board needs from the fab

| Need | Why | Source |
|---|---|---|
| Escape routing for the MAX86141 (WLP-20, 5 x 4 balls, 0.4 mm pitch, 0.21 mm round pads) | Pad gap is 0.4 - 0.21 = 0.19 mm. A trace plus two clearances at 3/3 mil needs 3 x 0.0762 = 0.229 mm, which does not fit. At 2/2 mil it needs 0.152 mm, which fits. Six balls (B2 to B4, C2 to C4) are interior, so they need either via-in-pad or traces between pads. | `libs/smartwatch.pretty/MAX86141_WLP-20_2.048x1.848mm_P0.4mm.kicad_mod` |
| Escape routing for the OCVPB21-13F6 (WLCSP-13, 0.4 mm pitch, 0.2 mm pads) | Same pitch, 0.2 mm gap between pads. Ball B2 (OUT_5V) is enclosed by A2, B1, B3, C2. Those four are unused in our schematic but their pads still exist, so B2 needs via-in-pad or a trace through a 0.2 mm gap. | `libs/smartwatch.pretty/OCVPB21-13F6_WLCSP-13_P0.4mm.kicad_mod` |
| Via-in-pad with filled and capped vias, or laser microvias | The pads are 0.21 mm, far smaller than the 0.35 mm pad some fabs ask for around a 0.15 mm mechanical via. | JLCPCB BGA guide (below) |
| Flat finish: ENIG | Wafer-level packages need a flat pad. | Reference board fab note |
| Finished thickness 0.6 to 0.8 mm, 4 layers (6 if the fab needs it) | Pod height budget. | mechanical plan |
| 50 ohm controlled impedance on the RF line (nRF54L15 to the Johanson antenna) | Antenna matching. | Johanson / Nordic reference |
| Small boards (about 45 x 30 mm), prototype quantities | First spin. | |

## 2. What the reference board does (MAXREFDES103 sensor board, same MAX86141)

From `reference-designs/MAXREFDES103/Sensor Board/Sensor Board - FAB/max86141_spo2_1mm_apps_p3_fab_drawing.pdf` on the `reference-library` branch (the vendor files are not on `main`):

- 4 layers: TOP 1 oz, L02_GND 0.5 oz, L03_SIG 0.5 oz, BOTTOM 1 oz. Isola 370HR or equivalent, dielectric thickness TBD. Finished thickness 0.031 in (0.79 mm) +/- 0.010 in.
- Finish: immersion gold 3 to 8 microinches over electroless nickel.
- Drill chart: 4.0 mil plated x 60, 6.0 mil plated x 43, 12.01 mil plated x 1.
- Note 20: fill and cap all 0.004 in drilled vias with non-conductive epoxy.
- Not stated in the drawing: the drilling method for the 4 mil holes, and trace/space.
- Inference, not stated: the drill chart is one table titled "TOP to BOTTOM" and the lamination diagram shows no blind or buried layers, so the 4 mil holes are probably through vias. That would be 0.1 mm holes in a 0.79 mm board (about 8:1), filled and capped inside the pads.

## 3. What public fab pages say (checked 2026-11-13; the sources disagree in places, so confirm with the fab)

| Fab | Found | Not found |
|---|---|---|
| JLCPCB | Via drill 0.15 mm and trace/space 0.09 to 0.10 mm for multilayer; general minimum via hole 0.2 mm. Via-in-pad as POFV (plated over filled via) on 6 to 20 layers, recommended via 0.15 mm or larger and pad 0.35 mm or larger. HDI: laser blind vias 0.075 to 0.150 mm, pad = via + 6 mil, minimum ring 3 mil, trace/space 3/3 mil (2.7 mil extreme). | Via-in-pad on 4 layers. ENIG on HDI. 0.8 mm HDI stack-up. HDI impedance tolerance. |
| PCBWay | HDI: trace/space 2/2 mil, laser drill 4 to 8 mil, minimum prepreg 0.06 mm and core 0.1 mm for laser blind vias. | Via-in-pad filling. Pad sizes for 0.4 mm pitch WLCSP. |

Sources: [JLCPCB BGA design guidelines](https://jlcpcb.com/help/article/bga-design-guidelines---pcb-layout-recommendations-for-bga-packages), [JLCPCB via-in-pad POFV guide](https://jlcpcb.com/help/article/via-in-pad-pofv-guide), [JLCPCB HDI capabilities FAQ](https://jlcpcb.com/help/article/hdi-pcb-capabilities-faq), [JLCPCB PCB capabilities](https://jlcpcb.com/capabilities/PCB-capabilities), [PCBWay advanced PCB capabilities](https://www.pcbway.com/advanced-pcb-capabilities.html), [PCBWay HDI](https://pcbway.com/hdi-pcb.html).

## 4. Options

| Option | Idea | Risk |
|---|---|---|
| A. JLCPCB 6-layer with POFV | Cheap, fast, assembly parts database already used. | Their 0.35 mm pad guidance does not fit 0.21 mm pads. Would need their written confirmation, or HDI. |
| B. JLCPCB HDI (laser blind vias, 3/3 mil) | Laser via 0.075 mm needs about a 0.227 mm pad, close to our 0.21 mm. | Marginal pad size. ENIG and 0.8 mm not confirmed. |
| C. PCBWay HDI (2/2 mil, laser 4 to 8 mil) | 2/2 mil lets a trace pass between the 0.21 mm pads, so interior balls may escape on the surface without via-in-pad. | Via-in-pad filling not confirmed. Cost and lead time higher. |

Suggested path: send the question list in section 5 to both JLCPCB (HDI orders get an engineering review before payment) and PCBWay, and choose from their written answers. Until then, route nothing under the two fine-pitch parts.

## 5. Questions for the fab (draft, to send only when the user approves)

1. Can you build a 4-layer (or 6-layer) board, 0.8 mm finished, ENIG, with via-in-pad (filled and capped) under 0.21 mm round pads at 0.4 mm pitch? What is the smallest pad and via you will accept in that case?
2. If laser microvias are needed: minimum laser via diameter, capture pad diameter, minimum prepreg thickness, and the stack-up you recommend for 0.8 mm.
3. Minimum trace/space on the outer layers (can a trace pass between two 0.21 mm pads with a 0.19 mm gap?), and minimum solder mask dam / mask opening style for these pads (non-solder-mask-defined).
4. Controlled impedance: 50 ohm single-ended on the top layer over layer 2, your stack-up and tolerance.
5. Panelisation and minimum board size for 45 x 30 mm, and lead time and price for 5 and 20 boards.
6. Can you drill 0.1 mm (4 mil) through a 0.8 mm 4-layer board and fill and cap it, as the MAXREFDES103 sensor board does? If yes, is that cheaper than laser HDI?
7. Can you assemble 0.4 mm pitch WLP/WLCSP parts, or do we place them ourselves?
