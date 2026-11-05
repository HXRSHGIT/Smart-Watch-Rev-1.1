# HealthOS Band main board: KiCad schematic

Done by Harsh Thakur.

KiCad 9 project, hierarchical. Open `smartwatch.kicad_pro`.

The sheets are drawn the way a person draws them: real wires between parts, left-to-right signal flow, frames with headings, blue designer notes, one ground symbol per group. Net labels are used only where a wire cannot reach: the I2C pair at the second chip on the sensors sheet, and on the root page the second receiver of the SPI bus (memory) and of the I2C bus (power), 10 labels. Bus test points sit on the sheets that own the bus. The rules are in `STYLE_GUIDE.md`; the datasheet review is in `REVIEW.md`. Each sheet is a script in `tools/sheets/`. Supply rails are power symbols, so they connect by name across sheets.

## Sheets

| Sheet | File | Contents | State |
|---|---|---|---|
| Root | `smartwatch.kicad_sch` | sheet blocks and the signals between them | done |
| Charging input | `input_protection.kicad_sch` | two pogo pads, OCVPB21-13F6, RLIM, COUT, FLAG pull-up | done |
| LED supply | `led_supply.kicad_sch` | TPS61240 5 V boost, 0 Ohm links to VLED (boost or VSYS) | done |
| MCU | `mcu.kicad_sch` | nRF54L15 (3 units), decoupling, DC/DC, crystals, reset, debug | done |
| RF | `rf.kicad_sch` | Nordic match network, antenna tee, Johanson antenna | done |
| Optical | `optical.kicad_sch` | MAX86141, SFH 7016, 2 x VEMD8080 | done |
| Sensors | `sensors.kicad_sch` | BMI270, MAX30208, I2C pull-ups | done |
| Test | `test.kicad_sch` | Tag-Connect SWD pads, test points | done |
| Power | `power.kicad_sch` | nPM1300 (QFN32), L6, caps, battery connector, NTC, ship-mode button | done |
| Memory | `memory.kicad_sch` | MX25R3235F (8-land USON), CS# pull-up, SPI test points | done |

## Rebuild and check

```
python tools/gen_footprints.py     # custom footprints -> libs/smartwatch.pretty
python tools/build.py              # symbols and sheets
python tools/check.py              # ERC + netlist vs expected + pin table + footprint pads
python tools/lint.py               # wire crossings and net labels per sheet
python tools/pinmap.py             # PIN_MAP.md and BOM.csv
python tools/dev.py mcu A3 110     # preview one sheet as build/dev/mcu.png
```

`check.py` needs `kicad-cli` (KiCad 9). It prints `ALL CHECKS PASSED` or the list of differences.

## What the check covers

1. KiCad ERC on the whole hierarchy: zero messages.
2. Every pin of the nRF54L15, nPM1300, MX25R3235F, MAX86141, SFH 7016, VEMD8080, BMI270, MAX30208, TPS61240, OCVPB21, antenna, battery connector, button and programming pads is on the net the requirements document says. The expected table is typed separately from the build script.
3. Every two-pin part by reference (both nets; the pin order of a passive does not matter, so the check follows each chain of parts from the nets it already knows), 61 of them. Internal nets are compared by connectivity, not by name, because wired nets carry no label.
4. The nRF54L15 symbol has the same 49 pin numbers and names as the datasheet pin table (`data/nrf54l15_qfn48_pins.csv`).
5. Every footprint pad matches the symbol pins (stock and custom footprints).
6. No net has a single pin.

## nRF54L15 pin plan

| Pins | Use |
|---|---|
| P2.01 SCK, P2.02 MOSI, P2.04 MISO | SPI bus (SPIM00, dedicated pins) to MAX86141 and the flash |
| P2.05 | chip select, MAX86141 |
| P2.00 | chip select, flash |
| P0.04 SCL, P0.03 SDA | I2C (TWIM30) to BMI270, MAX30208 and the nPM1300 (0x6B) |
| P0.00, P0.01, P0.02 | MAX86141 INT, BMI270 INT1, BMI270 INT2 |
| P2.03 | MAX30208 alarm (GPIO0) |
| P1.08 | nPM1300 interrupt (GPIO1) |
| P2.06 | OCVPB21 FLAG |
| P2.08 | LED boost enable |
| P2.09, P2.10 | MAX86141 GPIO1, GPIO2 |
| P2.07 | SWO (trace output to the test pads) |
| P1.00, P1.01 | 32.768 kHz crystal |
| P1.02, P1.03 | NFC pins, unused |
| P1.04 to P1.07, P1.09 to P1.14 | unused (errata 100 on power-on shorts) |

## Known open items (also in `../REQUIREMENTS_FROM_DATASHEETS.md` section 12)

- nPM1300 and flash datasheets are not saved yet, so those two sheets and the power budget are not built.
- Footprints marked CHECK: MAX30208 (pads scaled from a drawing), OCVPB21 (A1 orientation versus the package marking), VEMD8080 (pad numbering versus the reference board), pogo pad (placeholder diameter), Johanson pads (from the datasheet mounting drawing).
- Tag-Connect TC2030 pin order is assumed (1 VTREF, 2 SWDIO, 3 nRESET, 4 SWDCLK, 5 GND, 6 SWO) and must be confirmed against the cable drawing.
- Passive part numbers are not chosen yet; values and ratings come from the datasheets.
