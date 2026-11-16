# JLCPCB design rules for iteration 1

Done by Harsh Thakur.

Decision (2026-11-13): the board is made at JLCPCB and designed to what JLCPCB states it can do. The numbers below are from JLCPCB's own pages, read on 2026-11-13: [PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [BGA design guidelines](https://jlcpcb.com/help/article/bga-design-guidelines---pcb-layout-recommendations-for-bga-packages), [via-in-pad guide](https://jlcpcb.com/help/article/via-in-pad-pofv-guide), [HDI capabilities FAQ](https://jlcpcb.com/help/article/hdi-pcb-capabilities-faq). Where JLCPCB's pages disagree or are silent, this file says so.

## 1. Process

| Item | Choice | Why |
|---|---|---|
| Layers | 4, rigid FR-4 | Enough for 92 parts on 34 x 23 mm. JLCPCB's automatic via-in-pad process starts at 6 layers, but plain via-in-pad needs a 0.30 mm pad (see 4), which does not fit our 0.21 mm pads, so 6 layers would add cost for nothing. |
| Thickness | 0.8 mm (+/- 0.1 mm) | Pod budget 0.6 to 0.8 mm. JLCPCB lists 0.4 / 0.6 / 0.8 / 1.0 mm for FR-4; whether 0.8 mm is offered for every layer count was not stated: check on the order page. |
| Finish | ENIG | JLCPCB: 0.2 to 0.25 mm BGA pads require ENIG. Also flat for the WLP parts. |
| Outline | 34 x 23 mm rectangle | First-spin engineering board (see `tools/make_board.py`). |
| Impedance | 50 ohm RF line, +/- 10 % | JLCPCB tolerance (capabilities page). Stack-up and width: see section 1a. |

### 1a. Stack-up for the 50 ohm line (read from jlcpcb.com/impedance on 2026-11-15)

JLCPCB lists 0.8 mm, 1 oz outer, 0.5 oz inner, 4-layer impedance stack-ups: JLC04081H-7628 (prepreg 0.2104 mm), **JLC04081H-3313 (prepreg 0.0994 mm, core 0.50 mm)**, JLC04081H-2116B (0.1164 mm) and JLC04081H-1080 (0.0764 mm). Prepreg dielectric constants on the same page: 7628 4.4, 3313 4.1, 2116 4.16, 1080 3.91.

Chosen: **JLC04081H-3313** (JLCPCB's calculator, set to 4 layers, 0.8 mm, 1 oz outer, 0.5 oz inner, 50 ohm single ended on L1 over L2, lists it as "Standard / recommend", finished thickness 0.80 +/- 0.10 mm; the "Special" stack-ups are not standard). Reason for 3313 over 7628, the other standard one: the 0.0994 mm prepreg gives a narrow line (about 0.17 mm against about 0.36 mm), so the 0.2 mm wide QFN pin 31 and the 0201 pads of the pi network (0.40 mm wide) need no wide stub, and the copper pour next to the line only has to be kept back a few tenths of a millimetre.

Width, my calculation (Hammerstad-Jensen microstrip formula from the JLCPCB prepreg values above, 35 um copper, no solder mask): 7628 0.36 mm, 3313 0.17 mm, 2116B 0.20 mm, 1080 0.13 mm. The solder mask lowers the impedance by a few ohms, so the true width is a little smaller. **This number is not from JLCPCB: their calculator opened, listed the stack-ups, but its Trace Width column stayed empty in this session.** The routing script keeps the RF width in one constant, so replacing it with JLCPCB's number is a one-line change. The width has to be confirmed (calculator in another browser, or JLCPCB support) before the order is paid.

## 2. Rules (enforced in `smartwatch.kicad_pro`, written by `tools/jlc_rules.py`)

| Rule | JLCPCB value | In KiCad |
|---|---|---|
| Track width and spacing, multilayer, 1 oz | 0.09 / 0.09 mm (3 mil acceptable in BGA fan-outs) | min track 0.09, min clearance 0.09; default class 0.1 / 0.1 |
| Pad to track | 0.1 mm (0.09 mm locally for BGA pads) | default class 0.1 |
| SMD pad to pad, different nets | 0.15 mm | not a KiCad rule (see 3) |
| Solder mask bridge | 0.10 mm (green) | mask min width 0.1 |
| BGA pad | 0.2 mm minimum, ENIG | footprints: MAX86141 0.21, OCVPB21 0.20 |
| Via | 0.15 mm hole / 0.25 mm copper minimum | min via 0.25, min hole 0.15; default via 0.45 / 0.20 (smaller than 0.45 mm copper on a 0.2 mm hole costs extra) |
| Via hole to track | 0.2 mm | hole clearance 0.2 |
| Hole to hole | not read from the page | 0.25 mm (KiCad default, conservative) |
| Copper to board edge | 0.2 mm | 0.2 |
| Pad to silkscreen | 0.15 mm | silk clearance 0.15 |
| Silkscreen text | height 1.0 mm, line 0.15 mm | text 1.0 / 0.15 |
| Power net class | not a fab rule | 0.3 mm tracks on VSYS, VBUS_PROT, +1V8, VLED, VLED_BOOST, VBAT |

## 3. Verified

- `tools/check.py` fails if `smartwatch.kicad_pro` does not hold these rules, and fails if `smartwatch.kicad_pcb` differs from the schematic.
- DRC against these rules (2026-11-13, after the footprint fixes): 0 violations of any kind, 230 unconnected (nothing is routed yet). The body outlines of PD1, PD2, U8 and AE1 are no longer drawn on the silkscreen layer, so they do not run over pads.
- Pad to pad 0.15 mm: a sweep with KiCad's default 0.2 mm clearance flagged only pad pairs at 0.18 and 0.19 mm, so the smallest gap in any footprint is 0.18 mm. This is a derived result: a custom `.kicad_dru` rule had no effect in `kicad-cli`, so none is shipped.

## 4. Fit of the fine-pitch parts

| Part | Geometry | Result |
|---|---|---|
| MAX86141 (WLP-20, 5 x 4) | 0.21 mm round pads, 0.4 mm pitch, pad gap 0.19 mm | 14 outer balls escape on the surface. C3, C4 (ground) join D3, and C2 joins D2 (same 1.8 V net), so those three leave through the outer row. **B2 INT, B3 GPIO1, B4 GPIO2 cannot escape and are left open (option A, section 5)**: a 0.09 mm trace plus two 0.09 mm clearances needs 0.27 mm, the gap is 0.19 mm, and a full ball array leaves no diagonal exit. |
| OCVPB21 (WLCSP-13) | 0.20 mm round pads, 0.4 mm pitch | Fits. B2 (OUT_5V) is enclosed by four unused balls, but the C1 ball position is empty, so a trace leaves through the diagonal gap between B1 and C2 (0.366 mm wide, a 0.09 mm trace plus clearances needs 0.27 mm). |
| nRF54L15 (QFN-48), BMI270, MAX30208, flash | standard pitch 0.4 to 0.8 mm, escape on the surface | Fits. JLCPCB lists a 0.25 x 0.25 mm minimum SMD pad; QFN pads at 0.4 mm pitch are narrower, so confirm with the free JLCDFM check when Gerbers exist. |

## 5. MAX86141 INT, GPIO1, GPIO2: decided 2026-11-13, option A (applied in the schematic)

JLCPCB's two ways to put a via inside a pad do not fit a 0.21 mm pad on the plain process: filled via-in-pad needs a pad of the drill plus 0.15 mm (0.30 mm for the 0.15 mm mechanical minimum, 0.35 mm recommended), and the laser microvia (HDI) needs 0.25 mm for its 0.1 mm via.

| Option | What it means | Cost |
|---|---|---|
| **A. Leave INT, GPIO1, GPIO2 unconnected (chosen)** | The firmware polls the Interrupt Status 1 register (0x00, MAX86141 rev 5 datasheet page 58) and reads the FIFO over SPI; the A_FULL and DATA_RDY flags are in that register whether or not the INT pin is wired. Everything else fits the plain 4-layer process. Done: B2, B3, B4 are no-connects; the PPG_INT, PPG_GPIO1, PPG_GPIO2 nets, R4, R5 and TP11 are removed; nRF54L15 pins 20, 21 and 23 are no-connects. Time stamping without INT: `research/sensors/TIME_SYNC.md` section 3.6. | Cheapest and certain. No data-ready interrupt, so the nRF54L15 cannot sleep until the sensor is ready. |
| B. Keep INT with HDI (1st order, laser via) | Enlarge ball B2 to a 0.25 mm pad with a 0.1 mm laser via; GPIO1 and GPIO2 stay unused. | Higher price and longer lead time. Enlarging B2 to 0.25 mm leaves a 0.17 mm gap to its 0.21 mm neighbours (JLCPCB's pad-to-pad limit is 0.15 mm). |
| C. Ask JLCPCB in writing whether a 0.1 mm filled via-in-pad is possible in a 0.25 mm pad on a plain multilayer board | Their capability page allows 0.1 mm drills below 1 mm thickness with ENIG, but the via-in-pad guide only lists 0.1 mm for laser. | Free, but an answer is not guaranteed. |

## 6. Not decided or not checked

- Board thickness 0.8 mm for 4 layers: JLCPCB's impedance page lists four 0.8 mm 4-layer stack-ups (section 1a), so it is offered with impedance control; confirm ENIG with it on the order page.
- Hole-to-hole minimum: not on the capabilities page; 0.25 mm kept (conservative); the free JLCDFM check is the proof.
- Routing: not started. Antenna keep-out and first placement are done, see `PLACEMENT_RULES.md`.
- A free JLCDFM check of the Gerber files is the cheapest proof that the finished layout fits their rules.
