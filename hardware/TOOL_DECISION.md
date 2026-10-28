# Schematic tool: KiCad 9 or Altium

Done by Harsh Thakur.

**Decision: KiCad 9 for the schematic and the Iteration 1 board.** Revisit at layout if the PCB maker's HDI or flex rules need Altium.

## Why KiCad here

| Question | KiCad 9.0.8 (installed) | Altium (AD26 is installed) |
|---|---|---|
| Can every step be checked without opening the GUI? | Yes. `kicad-cli` runs ERC, exports the netlist and the BOM from the command line. Each sheet is checked the moment it is written. | Not reliably. The `.SchDoc` format is binary, and an edit can leave a file that hangs on open. |
| Can the client's engineer open the files? | Free, no licence. | Needs a licence. |
| Can changes be reviewed in git? | Yes. `.kicad_sch` and `.kicad_sym` are text, so a diff shows exactly which pin or value changed. | No. Binary diffs. |
| Is vendor CAD available? | Nordic's nRF54L15 reference circuit exists as a KiCad block (CERN-OHL-P licence). Ultra Librarian / SnapEDA provide KiCad symbols and footprints for the ADI, ST and Vishay parts. | Nordic ships its nPM1300 and nRF54L15 reference layouts as Altium files. ADI's MAXREFDES103 also ships Allegro and ODB++. |
| HDI microvias and 0.3 / 0.4 mm pitch parts | Supported (blind, buried and micro vias, per-layer rules). | Stronger tooling. |
| Rigid-flex | No native rigid-flex stackup. A rigid board plus a separate flex tail works. | Native. |
| Existing tooling here | KiCad 9 is on the PATH. | A large set of scripts exists for the XBattery BMU project, built around that company's library rule. |

## What would change the decision

- The PCB maker requires a rigid-flex stackup in one file, or quotes HDI rules KiCad cannot express. Then the layout moves to Altium and the verified schematic is carried over.
- The client asks for Altium files. The part list, values and net names in this folder carry over either way.

## What I did not check

- Whether Altium can import the finished KiCad project cleanly. Test it when the schematic is done, before layout starts.
- Licence terms of the company Altium seat for a separate client project. If it is yours to use, Altium also works.

Sources: `kicad-cli version` = 9.0.8 on this PC. Nordic KiCad library and licence: github.com/hlord2000/nordic-lib-kicad. nRF54L15 datasheet v1.0 section 10.3 (Altium reference files from nordicsemi.com).
