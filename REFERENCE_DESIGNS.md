# Reference design review

Done by Harsh Thakur.

## Which designs

The request named "Max Ref Des 15 or 13". Those two do not exist as heart-rate designs: MAXREFDES15 is a 4-20 mA current-loop board. The designs listed on the MAX86141 product page are:

| Design | What it is | Used here |
|---|---|---|
| **MAXREFDES103#** Health Sensor Band | Wrist band with a MAX86141 sensor board, MAX32664C sensor hub, MAX32630 micro board. Full design files downloaded (schematic, BOM, layout, Allegro board, ODB++, STEP). | **Main reference** for the optical sheet |
| **MAXREFDES101#** Health Sensor Platform 2.0 | Earlier platform on the same AFE. User guide downloaded. Design zip not downloaded. | Cross-check only |
| MAX86140EVSYS | Evaluation system for the single-channel MAX86140. Fab files exist. | Not downloaded |
| MAX-HEALTH-BAND | Evaluation band. | Not used |

If a different pair of numbers was meant, tell me and I will review those too.

## MAXREFDES103 sensor board: what it contains

Board name `max86141_spo2_1mm_apps_p3`, schematic dated 2019-09-03 (BOM variant "do_not_purchase", an evaluation design).

| Block | Parts |
|---|---|
| AFE | MAX86141 (WLP20) |
| Emitters | 2 x OSRAM SFH 7013 (a three-colour part, red / green / IR) plus one single green LED, selected through a MAX4740 analog switch |
| Detectors | 2 x Vishay VEMD8080 |
| Motion | Kionix KX122 accelerometer (not our part) |
| Supervisor | MAX32664 sensor hub with a 32.768 kHz crystal (not our part) |

### Decoupling and values it uses (BOM)

| Net | Value | Part |
|---|---|---|
| 1.8 V supply | 22 uF x2 (C1, C2), 0402 | Murata GRM155R60J226ME11 (flagged "not recommended", 52-week lead time) |
| 1.8 V local | 1 uF 0201 (C8), 10 uF 0402 (C7) | GRM033R61A105ME15, GRM155R61A106ME44 |
| LED supply (VLED) | 22 uF 0402 x5 (C3, C4, C5, C10, C11) | same 22 uF family |
| MAX86141 interrupt and GPIO1 pull-ups | 100 kOhm to 1.8 V | R12, R23 |
| I2C pull-ups (sensor hub side) | 3.3 kOhm | Panasonic ERJ-1GEF3301C |
| Series jumpers | 0 Ohm 0201 | in the connector, I/O and LED lines, so the board can be reconfigured |

### What we reuse

- The pin-to-net wiring of the MAX86141 (checked ball by ball against the datasheet, see `REQUIREMENTS_FROM_DATASHEETS.md`).
- The photodiode ground handling: PD_GND is a separate net, joined to the board ground at a single point (the schematic carries that note, and datasheet Rev 5 repeats it in the layout guidelines).
- The 100 kOhm pull-ups on the open-drain INT and GPIO lines.
- 0 Ohm links in the LED and photodiode lines for bring-up.

### What we change, and why

| Reference design | Our design | Reason |
|---|---|---|
| SFH 7013 plus a separate green LED | One SFH 7016 (green 530 nm, red 655 nm, IR 940 nm in one package) | Client brief names the SFH 7016. Three colours, one footprint. |
| MAX4740 LED switch | None | We drive one LED package; the MAX86141 has three LED drivers, one per colour. |
| KX122 accelerometer, MAX32664 hub | BMI270 and the nRF54L15 | Client brief. |
| 22 uF 0402 at 6.3 V X5R on the supply | Re-select, see `REQUIREMENTS_FROM_DATASHEETS.md` | Part is marked not recommended, and the same family is used on VLED at 5 V where a 6.3 V part derates heavily. |

### One conflict found, not yet closed

The reference schematic puts the VEMD8080 anode on pin 4, while the Vishay datasheet (Rev. 1.1, 2023) puts it on pin 5 and shows pins 1-4 and 6-8 as cathodes. The ODB++ netlist of the reference board agrees with its schematic: the anode net (PD_GND) lands on the fourth pin (index 3) of each photodiode, the cathode net on the other seven. My working explanation is that the reference footprint numbers the pads in a different order from Vishay's drawing, so both could be the same physical pad. **I have not confirmed that.** Rule until it is closed: our footprint is drawn from Vishay's package drawing with Vishay's numbering (anode = pin 5, pin 1 at the marked corner), and the footprint is compared with the reference board's pad geometry (ODB++ layers) before the layout is released. If they disagree, ask Vishay.

## Other optical parts looked at (not used)

MAXM86161A (single-photodiode module) and ADPD4100 (up to eight detectors, ECG and bioimpedance capable) were compared earlier and are not used. The MAX86141 set matches the client brief and gives two detectors for motion handling.

## Sources

- ADI MAX86141 product page (reference designs list), MAXREFDES103 design files zip, UG-7145 and UG-6780 user guides.
- Vishay VEMD8080 datasheet Rev. 1.1; MAX86141 datasheet Rev. 5 (7/23).
