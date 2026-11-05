# Schematic development: task list

Tool: KiCad 9 (decision in `TOOL_DECISION.md`). Parts: the selected set in `docs/COMPONENT_SELECTION.md` as revised
(nRF54L15, nPM1300, MAX86141, SFH 7016, 2x VEMD8080, BMI270, MAX30208) plus everything each one needs to work.

Rule: no part goes on a sheet until its datasheet is in `datasheets/` (local, not committed) and listed in `DATASHEET_INDEX.md`.
Rule: no sheet is "done" until ERC is clean and its nets match the datasheet pin tables (`schematic/tools/check.py`).

Status key: [x] done and checked, [~] partly done (what is missing is written next to it), [ ] not started.

## A. Decisions
- [x] A1 Pick the design tool: KiCad 9 (`TOOL_DECISION.md`)
- [x] A2 Review the Analog Devices reference designs: MAXREFDES103 and 101 (`REFERENCE_DESIGNS.md`). "13 or 15" do not exist as heart-rate designs.
- [x] A3 Scope for this phase: the selected core parts. Display, haptic driver, pressure sensor and NFC reader are later sheets.

## B. Datasheets (nothing is skipped, passives included)
- [x] B1 Active parts: all 12 datasheets saved (nPM1300 as text of Nordic's web specification v1.3, MX25R3235F rev 1.6)
- [x] B2 Reference circuits: nRF54L15 circuit configuration 1 (Fig. 180, Table 87), MAXREFDES103 sensor board (schematic, BOM, fab data)
- [~] B3 Boost (TPS61240), protection (OCVPB21), antenna (Johanson) done. Flash pending.
- [~] B4 Crystals: electrical limits read (HFXO, LFXO). **Exact crystal MPNs not chosen.**
- [ ] B5 Passives: one MPN per value and its series datasheet, DC-bias derating check (10 uF at 5 V, 22 uF at 1.8 V)
- [ ] B6 Connectors: battery connector, pogo contacts (dock vendor)
- [x] B7 Datasheet index with revision and source

## C. Bill of materials from the datasheets
- [x] C1 Every pin of the 8 built sheets mapped to a net: `schematic/PIN_MAP.md`
- [x] C2 External passives for the built sheets with value, rating, package and source: `schematic/BOM.csv` (74 parts)
- [ ] C3 Power budget per rail against each regulator's limit (needs the nPM1300 datasheet)
- [x] C4 Open questions list: `REQUIREMENTS_FROM_DATASHEETS.md` section 12

## D. Libraries
- [x] D1 Chip symbols from datasheet pin tables (`schematic/libs/smartwatch.kicad_sym`); nRF54L15 symbol compared with the extracted pin table
- [~] D2 Footprints: stock KiCad footprints for the standard packages (pads compared with symbol pins). Seven custom footprints drawn; **MAX30208 pads are scaled from a drawing, OCVPB21 A1 orientation and VEMD8080 numbering still to confirm.**
- [x] D3 Passives and connectors use the stock KiCad symbols

## E. Hierarchical schematic
- [x] E1 Root sheet and sheet interfaces
- [x] E2 Charging input and power (OCVPB21, nPM1300, battery connector) done
- [x] E3 LED supply (TPS61240) done
- [x] E4 MCU core (nRF54L15, DC/DC, crystals, reset, debug)
- [x] E5 RF (Nordic match network, antenna tee, antenna)
- [x] E6 Optical (MAX86141, SFH 7016, 2x VEMD8080)
- [x] E7 Motion and temperature (BMI270, MAX30208, I2C pull-ups)
- [x] E8 Memory (MX25R3235F) done
- [x] E9 Test and programming (Tag-Connect, test points)

## F. Verification
- [x] F1 ERC on the whole hierarchy: no errors except 4 "label not connected" for `PMIC_IRQ` and `CS_FLASH` (their other end is on the two pending sheets)
- [x] F2 Netlist exported and compared with an independent expected table typed from the requirements document (`schematic/tools/check.py`); the check was shown to fail on a deliberately wrong net
- [~] F3 Datasheet cross-check: done for every sheet against the datasheet text and figures, see `schematic/REVIEW.md`. Findings and open decisions are listed there, with what was NOT rechecked
- [x] F4 BOM export
- [ ] F5 Review document for the client
