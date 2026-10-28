# HealthOS Band main board: KiCad schematic

Done by Harsh Thakur.

KiCad 9 project, hierarchical. Open `smartwatch.kicad_pro`.

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
| Power stand-in | `power_stub.kicad_sch` | marks the rails the nPM1300 will drive | **replace with the power sheet** |
| Power | (not yet) | nPM1300, battery, NTC | waiting for the datasheet |
| Memory | (not yet) | MX25R3235F | waiting for the datasheet |

## Rebuild and check

```
python tools/gen_footprints.py     # custom footprints -> libs/smartwatch.pretty
python tools/build.py              # symbols and sheets
python tools/check.py              # ERC + netlist vs expected + pin table + footprint pads
python tools/pinmap.py             # PIN_MAP.md and BOM.csv
```

`check.py` needs `kicad-cli` (KiCad 9). It prints `ALL CHECKS PASSED` or the list of differences.

## What the check covers

1. KiCad ERC on the whole hierarchy. Allowed: four "label not connected" messages for `PMIC_IRQ` and `CS_FLASH`.
2. Every pin of the nRF54L15, MAX86141, SFH 7016, VEMD8080, BMI270, MAX30208, TPS61240, OCVPB21, antenna and programming pads is on the net the requirements document says. The expected table is typed separately from the build script.
3. Every two-pin part (value and both nets), 48 of them.
4. The nRF54L15 symbol has the same 49 pin numbers and names as the datasheet pin table (`data/nrf54l15_qfn48_pins.csv`).
5. Every footprint pad matches the symbol pins (stock and custom footprints).
6. No net has a single pin, except the two pending ones.

## nRF54L15 pin plan

| Pins | Use |
|---|---|
| P2.01 SCK, P2.02 MOSI, P2.04 MISO | SPI bus (SPIM00, dedicated pins) to MAX86141 and the flash |
| P2.05 | chip select, MAX86141 |
| P2.00 | chip select, flash (pending sheet) |
| P0.04 SCL, P0.03 SDA | I2C (TWIM30) to BMI270, MAX30208 and later the nPM1300 |
| P0.00, P0.01, P0.02 | MAX86141 INT, BMI270 INT1, BMI270 INT2 |
| P2.03 | MAX30208 alarm (GPIO0) |
| P1.08 | nPM1300 interrupt (pending sheet) |
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
