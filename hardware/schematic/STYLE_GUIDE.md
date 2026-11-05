# Schematic drawing rules

Done by Harsh Thakur.

These rules come from the 1500 V BMU schematics (Altium) and the instructions given while drawing them. Every sheet in this project follows them. `tools/lint.py` checks the ones that can be checked by a program.

## Connections
1. **Draw wires.** Two pins that belong together are joined by a wire. A net label is used only for (a) a power rail, drawn as a power symbol, (b) a sheet port, and (c) a point a wire cannot reach without crossing other wires. Each sheet should have only a handful of labels.
2. **No floating parts.** Every resistor, capacitor and inductor is wired into the circuit. No symbol is left unconnected to "be tied by name".
3. **One ground symbol per group.** The ground ends of a group of capacitors are joined by one wire and one ground symbol. No double or triple ground symbols where one is enough.
4. **Junction dot at every T.** No two wires cross without being the same net. A wire never runs through a pin it does not belong to.
5. **Unused pins** carry a no-connect cross. Pins that must be tied (address, mode, enable) are wired to the rail they need, not left to a label.

## Flow and placement
6. **Left to right.** Inputs and ports enter on the left, signals pass through the parts, outputs and ports leave on the right.
7. **Supply row above the signal row.** Power paths (input, regulator, filter, rail) are drawn as their own row above the signal path.
8. **Power pins up, ground pins down** on every chip symbol. Signal pins left and right.
9. **Decoupling next to its pin.** Capacitors sit beside the supply pin they serve, on a short drawn rail, closest-value (smallest) nearest the pin.
10. **Repeated channels** are drawn once, then copied side by side in a grid.

## Structure and text
11. **Title line** at the top left: block name, requirement or source, one short description.
12. **Frames** with a heading around each function block, and a sub-heading under each stage (for example "ISOLATED SUPPLY", "TRANSCEIVER").
13. **Barriers** (isolation, mains side, a different ground) are marked with a dashed line and a caption on each side.
14. **Notes** in blue boxes: what the circuit does in two or three lines, which capacitors decouple which pin and "keep close to the pin", layout rules (creepage, copper, keep-outs), and open items. A numbered NOTES block at the bottom for sheet-wide notes.
15. **Sheet size follows the content.** If it is crowded, make the sheet larger. Nothing sits outside the border or on the title block.

## Sheet interface
16. **Supply inputs are sheet ports** (for example `VSYS`), so the main sheet decides where each supply comes from.
17. Port names are short, in capitals, and the same on both sides.

## Process
18. **Change the existing sheet in place.** No "v2" copies.
19. **Prove nothing changed.** After any redraw, the exported netlist is compared with the expected connections (`tools/check.py`).
20. **Electrically right before neat.** Every value and pin comes from the datasheet table named in `../REQUIREMENTS_FROM_DATASHEETS.md`.
