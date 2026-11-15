# Placement rules and first placement (iteration 1)

Done by Harsh Thakur.

Status 2026-11-13: first placement done by `hardware/schematic/tools/place_board.py` on the 34 x 23 mm board (squeezed from 45 x 30 on 2026-11-14). Nothing is routed. The file `smartwatch.kicad_pcb` holds the placement; adjust it in KiCad. Re-running the script starts the placement again and discards manual moves, so use Update PCB from Schematic (F8) in KiCad after a schematic change instead.

## 1. Decisions

| Item | Decision | Why |
|---|---|---|
| Outline | 34 x 23 mm rectangle (782 mm2, was 45 x 30), final for this spin | Smallest size the placement fits without crowding the top face; 33 x 22 did not fit. |
| Skin side | Bottom face touches the skin; the optics (PD1, D1, PD2, U2) and the skin temperature sensor U4 sit in the middle of the back face | Optics and skin temperature need skin contact; charging pads are on the right edge for the dock. |
| Edges | Every connector and switch is on an edge: J5 (top edge), J4 (right edge), SW1 and J3 (bottom corner), test points (bottom-left edge), pogo pads J1 and J2 (right edge, bottom face) | Agreed 2026-11-14. |
| Antenna | Top face, top-left corner, antenna axis perpendicular to the left edge | Away from the skin (the body detunes a 2.45 GHz antenna), at a board corner as Johanson recommends, far from the power block. |
| Antenna clearance | 6.5 x 6.5 mm at the corner, no copper pour and no vias on any layer (rule area `ANT_KEEPOUT`) | Johanson DS 36S0021A page 3, ground clearance of the evaluation board. The feed track and the antenna pads are allowed. |
| Placement method | Script, then hand adjustment in KiCad | Agreed 2026-11-13. |

## 2. Rules the script follows

1. Rotations 0 and 90 degrees only (180 where a pin side has to face a neighbour). No other angles.
2. Every passive goes beside the pad it serves: it is placed at the first free spot around the pad of the part it connects to on its smallest net (decoupling capacitors first), spread over that part's pads. Result: every resistor, capacitor and inductor sits within 4.2 mm of an IC pad on its net (median 1.7 mm over 49 passives).
3. No two courtyards overlap; 0.3 mm from every courtyard to the board edge.
4. Test points are not anchors. They sit in a row on the top edge, 2.35 mm apart.
5. Nothing is placed in the antenna clearance except the antenna and its tee slots (R3, C14, R2), which sit on the clearance edge.
6. References on passives are hidden (0201 parts are smaller than JLCPCB's 1.0 mm text); ICs, connectors and test points keep them, outside the courtyard.
7. The switching power parts (nPM1300, TPS61240 and their inductors) are at the right end, the antenna at the left end, the MAX30208 on the bottom face in the middle (about 10 mm from the power parts on the other face; confirm with the thermal test).

## 3. Where things are

| Zone | Face | Parts |
|---|---|---|
| Antenna corner | top | AE1, R3, C14, R2 (tee slots) |
| Processor | top | U1 nRF54L15 with its RF and crystal side facing the antenna, pi network L2, L3, L4 on pin 31, X2 below it, X1 on the right, decoupling around it |
| Memory and motion | top | U8 flash above the processor, U3 BMI270 on its right |
| Power | top, right | U7 nPM1300, U5 TPS61240, L5, L6 |
| Edge connectors | top | J5 (5 V header, top edge), J4 (battery, not fitted, right edge), SW1 (bottom right), J3 Tag-Connect (bottom edge), TP1 to TP10 (two rows of five, bottom-left) |
| Optics | bottom, centre | PD1, D1 (SFH 7016), PD2 in a row 6.5 mm apart, U2 MAX86141 under the LED |
| Skin temperature | bottom, centre | U4 MAX30208 beside the optics |
| Charging | bottom, right edge | J1, J2 pogo pads about 10 mm apart, U6 OCVPB21 with C24, R14, R15 beside them |

## 4. Checked

- `tools/check.py`: ALL CHECKS PASSED, 0 schematic differences (`kicad-cli pcb drc --schematic-parity`).
- DRC with the JLCPCB rules: 0 overlaps, 0 clearance or short violations. What remains is 12 silkscreen warnings (text over pads, text over text, one reference near the edge); JLCPCB removes silkscreen from pads, so they do not block an order.
- 230 unconnected items: nothing is routed yet.

## 5. Not decided or not done

- The RF chain is placed by rule, not tuned: compare with the Nordic reference layout for nRF54L15 QFN48 and the Johanson evaluation board before routing. The feed from the antenna to the pi network is about 12 mm and must be a 50 ohm controlled line (width from JLCPCB's impedance calculator).
- Pogo pads (right edge, 10.4 mm apart, 2.6 mm round) are our own dock spec for iteration 1; iteration 1 charges through J5. See `FOOTPRINT_AUDIT.md`.
- Tag-Connect needs the plug area clear: nothing tall within the cable's footprint (check the TC2030 drawing before routing).
- Heat: the nPM1300 is about 10 mm from the MAX30208 (other face) now that the board is smaller; confirm with the thermal test.

## 6. Routing rules for the next stage (general habits for small boards)

- 45 degree corners, no 90 degree corners; critical nets by hand first (RF line, crystals, power loops, the MAX86141 escape), then the autorouter for the rest.
- Layer plan: top and bottom signal, L2 solid ground, L3 power and slow signals. Through vias only, 0.45 / 0.20 mm (JLCPCB standard price).
- Ground stitching vias about every 3 to 4 mm along the RF line and around the antenna clearance (one twentieth of the wavelength in FR-4 is about 4 mm at 2.45 GHz).
- Decoupling capacitor: pad to the supply pin it serves first, then the via to ground; shortest loop wins over neat spacing.
- Connectors and the programming pads on an edge or an accessible face (done: all of them are on an edge).
- Keep the PD_GND net with its single tie point (NT3) away from switching currents; keep MAX86141 and photodiode tracks short and away from the LED supply.
