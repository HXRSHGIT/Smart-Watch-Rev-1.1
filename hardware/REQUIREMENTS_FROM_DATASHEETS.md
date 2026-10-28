# What each part needs to work (from the datasheets)

Done by Harsh Thakur.

Every value below is read from the datasheet named in `DATASHEET_INDEX.md`. "Page" means the printed page number of that document. Where the datasheet leaves a choice to the designer, the choice is marked **Choice** and the reason is given. Anything not yet verified is in section 12.

Supply rails used in this design: `VBAT` (cell, 3.0 to 4.2 V), `VSYS` (nPM1300 system output), `VDD_1V8` (processor and sensor rail), `VLED` (LED supply), `GND`.

---

## 1. nRF54L15, QFN48 package (QFAA), datasheet v1.0

| Item | Value | Where |
|---|---|---|
| Supply | VDD 1.7 to 3.6 V. Pins 10, 22, 36, 47, 48 all to `VDD_1V8`. | pin table 79 |
| Ground | Pin 44 and the exposed pad (pin 49). Pin 32 (VSS_PA) goes **only** to pin 49. | Table 79 notes, Fig. 180 |
| Reset | Pin 30 nRESET, internal pull-up. Series 1 kOhm to the reset net, 3.9 pF to ground on the chip side. | Fig. 180 |
| Debug | Pin 25 SWDIO, pin 26 SWDCLK | Table 79 |
| 32 MHz crystal | Pins 34 (XC1) and 35 (XC2). No external load capacitors. | Fig. 180 |
| 32.768 kHz crystal | Pins 1 (P1.00/XL1) and 2 (P1.01/XL2). No external load capacitors. Optional in Nordic's drawing. **Choice: fitted**, because the battery model assumes the crystal (140 uA vs 2.3 mA for holding a Bluetooth connection in sleep). | Fig. 180, section 11.9 |
| NFC | Pins 3, 4 (P1.02, P1.03) are NFC pins from reset. Not used here. | Table 79 |
| GPIO | 31 pins: P0.00 to P0.04, P1.00 to P1.14, P2.00 to P2.10 (two P1 pins carry the 32 kHz crystal, two are NFC pins) | Table 79 |

### External components (Nordic circuit configuration 1, Table 87 and Figure 180)

| Ref | Value | Type / rating | Package | Connects to |
|---|---|---|---|---|
| C3 | 10 uF | X6S, 20 %, 6.3 V | 0402 | VDD (pins 47/48) to GND |
| C10 | 100 nF | X7R, 10 % | 0201 | VDD (pins 47/48) to GND |
| C4, C7, C8 | 100 nF | X7R, 10 % | 0201 | VDD pins 10, 22, 36, one each, to GND |
| L1 | 4.7 uH | 120 mA, 20 %, 650 mOhm | 0603 | DCC (pin 46) to DECD (pin 45) |
| C1 | 2.2 uF | X6T, 20 %, 2.5 V | 0201 | DECD (pin 45) to GND |
| FB1 | 120 Ohm at 100 MHz | 200 mA, 500 mOhm max | 0201 | DECD net to DECA net |
| C2 | 2.2 uF | X6T, 20 %, 2.5 V | 0201 | DECA (43) / DECRF (33) net to GND |
| C12 | 10 nF | X7R, 6.3 V | 0201 | DECA net to GND |
| C5 | 2.2 nF | X7R, 10 %, 10 V | 0201 | DECA net to GND |
| X2 | 32 MHz | 2.0 x 1.6 mm, CL 8 pF, total tolerance 40 ppm | XTAL 2016 | XC1 / XC2 |
| X1 | 32.768 kHz | 2.0 x 1.2 mm, CL 9 pF, total tolerance 20 ppm | XTAL 2012 | XL1 / XL2 |
| L2 | 2.7 nH | 600 mA, 0.1 nH, 120 mOhm | 0201 | ANT (pin 31) to node A |
| C6 | 1.5 pF | NP0, 0.05 pF, 25 V | 0201 | node A to **VSS_PA (pin 32) in the top layer only** |
| L3 | 3.5 nH | 500 mA, 0.1 nH, 170 mOhm | 0201 | node A to node B |
| C9 | 2.0 pF | NP0, 0.05 pF, 25 V | 0201 | node B to a ground that is **isolated from all ground layers except the bottom one** |
| L4 | 3.5 nH | same as L3 | 0201 | node B to node C |
| C11 | 0.3 pF | C0G, 0.1 pF, 50 V | 0201 | node C to GND. Node C is the RF output. |
| C13 | 3.9 pF | C0G, 0.25 pF, 50 V | 0201 | RESET pin to GND |
| R1 | 1 kOhm | 1 %, 0.05 W | 0201 | RESET pin to the NRESET net |

Nordic's own manufacturer part numbers: L2 = Murata LQP03HQ2N7B02, L3 and L4 = LQP03HQ3N5B02, C6 = GJM0335C1E1R5WB01, C9 = GJM0335C1E2R0WB01. Nordic notes "the antenna filtering components are subject to change". Place the matching network as close to the IC as possible and follow the reference layout.

Crystal limits (section 11.9): HFXO 32 MHz, tolerance 40 ppm for Bluetooth, CL 6 to 9 pF, drive level 100 uW max. LFXO 32.768 kHz, tolerance 500 ppm for Bluetooth, CL 6 to 9 pF, drive level 0.5 uW max.

The community KiCad block of this circuit (checked against Figure 180) differs from Nordic's drawing in several values: C1 shown as 10 uF, C6 shown as 2.2 uF, C12 as 0.3 pF, C13 as 3.9 pF, and a different cap-to-pin mapping. **Nordic's drawing is used, not the community block.**

### Pin rules that affect the pin map

| Rule | Source |
|---|---|
| SPI clock (SCK) and I2C clock (SCL) must use a "clock pin" (marked Yes in the table): pins 4 (P1.03), 5 (P1.04), 9 (P1.08), 12 (P2.01), 17 (P2.06), 28 (P0.03), 29 (P0.04), 39 (P1.11), 40 (P1.12). Data pins of that peripheral must be close to the clock pin. | Section 10.1.2, Table 77 |
| SPIM20/21 and TWIM20 to 22 use P1. SPIM00 uses dedicated pins on P2 (SCK = P2.01, SDO = P2.02, SDI = P2.04, CSN = P2.05, DCX = P2.00). TWIM30 / SPIM30 are in the low-power domain on P0. | Block diagram, Table 76, Table 79 |
| Avoid P1.04, P1.05, P1.06, P1.07, P1.11, P1.12, P1.13, P1.14 for anything a stray short could harm: at power-on they might be shorted together, and P1.04, 06, 07, 09, 10, 11, 12 might be shorted to ground for 1 us after power-on reset. | Errata [100] |
| After power-on reset all GPIO may be outputs or have pull-ups or pull-downs for 10 us. Any input that must not be driven at start (enables, resets) needs an external pull. | Errata [103] |
| TWIM stops responding if it is disabled during clock stretching: handled in firmware. | Errata [105] |
| Wake-on-pin raises current unless latched detect mode is used: firmware. | Errata [114] |
| P1.08 is not in any of the power-on errata lists. | Errata [100], [103] |

---

## 2. MAX86141, WLP20, datasheet Rev 5

| Ball | Name | Connect to |
|---|---|---|
| A1 | VLED | `VLED` (3.1 to 5.5 V). 10 uF to PGND. |
| A2 | SCLK | SPI clock from the processor |
| A3 | SDO | SPI MISO to the processor |
| A4 | SDI | SPI MOSI from the processor |
| A5 | CSB | chip select, active low |
| B1 | LED3_DRV | LED cathode, driver 3 |
| B2 | INT | open-drain interrupt, needs a pull-up to `VDD_1V8` |
| B3 | GPIO1 | open-drain GPIO, may be left open if unused |
| B4 | GPIO2 | open-drain GPIO, may be left open if unused |
| B5 | VREF | 1.0 uF to ground. Nominal 1.21 V, so a 6.3 V part is enough. |
| C1 | LED2_DRV | LED cathode, driver 2 |
| C2 | VDD_DIG | `VDD_1V8`, shorted to VDD_ANA at the board |
| C3 | GND_DIG | ground |
| C4 | GND_ANA | ground |
| C5 | PD_GND | photodiode anode node. Join to board ground at **one point only**. |
| D1 | LED1_DRV | LED cathode, driver 1 |
| D2 | VDD_ANA | `VDD_1V8`. 0.1 uF at the ball plus the 22 uF. |
| D3 | PGND | ground |
| D4 | PD2_IN | photodiode 2 cathode (MAX86141 only) |
| D5 | PD1_IN | photodiode 1 cathode |

| Limit | Value |
|---|---|
| VDD_ANA, VDD_DIG | 1.7 to 2.0 V (abs. max 2.2 V). Must be within 0.3 V of each other. |
| VLED | 3.1 to 5.5 V (abs. max 6.0 V) |
| Digital pins SCLK, SDI, SDO, CSB, INT, GPIO1/2 | abs. max 6.0 V, so they tolerate 3.3 V and 5 V levels. Input high 1.4 V min, low 0.4 V max. |
| SPI timing | clock period 125 ns minimum (the printed frequency cell reads 4, I treat 4 MHz as the safe design limit). |
| LED drive | up to 124 mA full scale per driver (range set in software) |

### External components (datasheet pin table, layout guidelines p. 49; reference design)

| Where | Value | Source |
|---|---|---|
| VDD_ANA + VDD_DIG (shorted) | **22 uF 0402** and **0.1 uF** to ground (effective about 10 uF after derating) | Layout guidelines p. 49 |
| VREF | 1.0 uF ceramic to ground | Pin table, p. 49 |
| VLED | 10 uF to PGND | Pin table |
| INT, GPIO1 pull-ups | 100 kOhm to `VDD_1V8` | reference design R12, R23 |
| Ground | GND_ANA, GND_DIG and PGND shorted at the edge of the ball array, one via to the plane. Individual vias for each decoupling cap. | Layout guidelines |
| Photodiode node | PD_IN fully shielded by PD_GND on the top layer, no other traces in the PD_GND area, PD_GND attached to board ground at one point | Layout guidelines |
| Photodiode capacitance | VEMD8080 is 47 pF, so PDBIAS setting 0x1 (0 to 65 pF) | Table 16 |

**Choice (LED channel order):** LED1_DRV = green, LED2_DRV = infrared, LED3_DRV = red, copying the reference design's channel table so that ADI's reference firmware needs no remapping.

---

## 3. SFH 7016 (LED1), Version 1.5

| Pin | Function | Connect to |
|---|---|---|
| 1 | Cathode, infrared 940 nm | MAX86141 LED2_DRV (C1) |
| 2 | Anode, green / red / IR (common) | `VLED` |
| 3 | Cathode, green 530 nm | MAX86141 LED1_DRV (D1) |
| 4 | Cathode, red 655 nm | MAX86141 LED3_DRV (B1) |
| 5 | Anode, common | `VLED` |
| 6 | NC | not connected |

Footprint: 1.85 x 1.65 x 0.6 mm, pad pitch from the datasheet "Recommended solder pad" drawing (p. 14). Forward voltage at 20 mA (typical / max): green 2.4 / 2.8 V, red 1.9 / 2.2 V, IR 1.3 / 1.5 V. Absolute maximum DC current: green 30 mA, red 40 mA, IR 60 mA (pulsed values are higher; see `research/optical-ppg/PPG_FRONTEND.md`).

## 4. VEMD8080 (PD1, PD2), Rev 1.1

| Pin | Function | Connect to |
|---|---|---|
| 5 | Anode | `PD_GND` |
| 1, 2, 3, 4, 6, 7, 8 | Cathode (seven pads in parallel) | `PD1_IN` for PD1, `PD2_IN` for PD2 |

Pin 1 is at the marked corner, numbering runs around the package (Vishay drawing 6.550-5354.01-4). See the open conflict about the pin numbering in `REFERENCE_DESIGNS.md`.

---

## 5. BMI270, LGA14, datasheet Rev 08

| Pin | Name | Connect to |
|---|---|---|
| 1 | SDO | **GND** (I2C address 0x68; VDDIO would give 0x69) |
| 2 | ASDx | VDDIO (datasheet: VDDIO or not connected, never ground) |
| 3 | ASCx | VDDIO (same) |
| 4 | INT1 | processor input |
| 5 | VDDIO | `VDD_1V8`, 100 nF to ground |
| 6 | GNDIO | ground |
| 7 | GND | ground |
| 8 | VDD | `VDD_1V8`, 100 nF to ground |
| 9 | INT2 | processor input |
| 10 | OCSB | not connected |
| 11 | OSDO | not connected |
| 12 | CSB | **VDDIO** (selects I2C) |
| 13 | SCx | I2C SCL |
| 14 | SDx | I2C SDA |

Supply: VDD 1.71 to 3.6 V, VDDIO 1.2 to 3.6 V. Decoupling: 100 nF at pin 5 and pin 8 (section 7.2).

## 6. MAX30208, thin LGA10, datasheet Rev 1

| Pin | Name | Connect to |
|---|---|---|
| 1, 2, 3 | VDD | `VDD_1V8`, 0.1 uF to ground, all three pins tied |
| 4, 5, 6 | GND | ground |
| 7 | GPIO1 | **ground** (address pin) |
| 8 | SDA | I2C SDA |
| 9 | SCL | I2C SCL |
| 10 | GPIO0 | processor input (temperature alarm interrupt). Reads as 0 at start-up through the internal 1 MOhm pull-down, so the address stays 0x50. |

Supply 1.7 to 3.6 V. I2C up to 400 kHz. GPIO pins are 6 V tolerant. Address with both GPIO pins low: 0x50 (write byte 0xA0). Read PCN 2204 before ordering.

## 7. TPS61240, WSON-6 (DRV), 5 V LED boost

| Pin | Name | Connect to |
|---|---|---|
| 1 | GND | ground (and the exposed thermal pad) |
| 2 | VOUT | `VLED_BOOST` (5.0 V, 2 %) |
| 3 | FB | tied directly to VOUT (fixed-output version, Figure 10) |
| 4 | EN | enable, high level 1.0 V min, so 1.8 V logic works |
| 5 | L | inductor |
| 6 | VIN | `VSYS`, with the inductor |

| Ref | Value | Source |
|---|---|---|
| L | 1.0 uH minimum. Datasheet list: TOKO MDT2012-CH1R0AN, Murata LQM21PN1R0MC0 (2.0 x 1.2 x 0.55 mm), FDK MIPS2012D1R0-X2. | Table 3 |
| CIN | 2.2 uF X5R, 6.3 V, 0402, at VIN | Table 2 |
| COUT | effective capacitance 2.7 uF or more at 5 V for 10 mV ripple, allowed range 1 to 20 uF. The datasheet example is 4.7 uF 6.3 V, which loses a lot of capacitance at 5 V. **Choice:** 10 uF 10 V X5R 0603 (derating still to be checked against the vendor curve). | 10.2.2.4 |

Input 2.3 to 5.5 V, output current up to 450 mA, valley current limit 500 mA, quiescent 30 uA. Status: TPS61240DRVR Active, production.

## 8. OCVPB21-13F6, WLCSP13, datasheet DS13107 Rev 3

| Bump | Name | Connect to |
|---|---|---|
| D1 | IN_A | pogo pad A |
| D3 | IN_B | pogo pad B (the bridge accepts either polarity) |
| B2 | OUT_5V | `VBUS_PROT` to the nPM1300 VBUS. COUT 10 uF or more, 6.3 V, low ESR. |
| E1 | RLIM | resistor to ground sets the current limit: ILIM = (318 - RLIM) / 0.447 mA. Allowed range 51 to 270 Ohm. |
| E3 | FLAG | open-drain, 100 kOhm pull-up. ST's diagram (Figure 1) pulls it up to VBAT; **Choice:** pull up to `VDD_1V8` instead so the processor input never sees more than its own supply. Absolute maximum on FLAG is 7 V, sink 4 mA. |
| C2 | RECTIF | rectified-bridge output pin. ST's application diagram (Figure 1) shows no component on it, so it is left open. |
| A3, C3, E2 | GND_DATA, GND_ESD, GND_BRIDGE | ground |
| A1, A2, B1, B3 | USB_DP, USB_IND, USB_DM, USB_INC | not used (two-pad pogo has no data lines). Unused inputs have a 100 kOhm pull-down inside. |

Limits: input 4.25 to 5.55 V, transient up to 13.2 V; **operating temperature -30 to +65 degC**; quiescent 0.4 to 1.5 mA while powered; overvoltage disconnects above 5.5 V. **Choice:** RLIM = 180 Ohm gives about 310 mA, enough for a 250 mAh cell at 1C plus the system load (revisit when the cell is chosen).

## 9. Antenna: Johanson 2450AT18A0100001E

| Pin | Function |
|---|---|
| 1 | Feed |
| 2 | NC, must be soldered for mechanical anchoring |

3.2 x 1.6 x 1.3 mm (EIA 1206), corner mount, 50 Ohm, return loss 9.5 dB min on Johanson's board, peak gain 1.5 dBi, efficiency 74 %. Matching values depend on our board; the datasheet says to leave footprints for a series-shunt-series network (Johanson's board uses 2.7 nH, 1.0 pF, 3.9 nH). **Choice:** three 0402 footprints in a tee, populated with 0 Ohm / DNP / 0 Ohm at first, tuned on the worn band.

---

## 10. Resulting external parts count (so far)

| Block | Capacitors | Resistors | Inductors / ferrites | Crystals |
|---|---|---|---|---|
| nRF54L15 | 13 (C1 to C13) | 1 (R1) | 5 (L1 to L4, FB1) | 2 |
| MAX86141 | 4 (22 uF, 0.1 uF, 1 uF, 10 uF) | 2 (INT, GPIO1 pull-ups) | 0 | 0 |
| BMI270 | 2 (VDD, VDDIO) | 0 | 0 | 0 |
| MAX30208 | 1 | 0 | 0 | 0 |
| LED boost (TPS61240) | 2 (CIN, COUT) | 0 | 1 | 0 |
| OCVPB21 | 1 (COUT) | 2 (RLIM, RFLAG) | 0 | 0 |
| Antenna match | 1 shunt (left empty at first) | 2 series (0 Ohm at first) | 0 | 0 |
| **Total so far** | **24** | **7** | **6** | **2** |

Not counted yet: nPM1300 and its inductors and capacitors, the flash, the I2C pull-ups, the optical 0 Ohm links, test points, battery and pogo connections (see section 12).

## 11. Decisions made from the datasheets

1. Everything digital runs at 1.8 V. All parts accept it (MAX86141 1.7-2.0 V, BMI270 1.71 V, MAX30208 1.7 V, nRF54L15 1.7 V). No level shifters.
2. LED supply `VLED` has two sources: the 5.0 V boost, and a link to `VSYS`, so both can be tested. Only one is fitted.
3. The 32.768 kHz crystal is fitted.
4. Photodiode ground `PD_GND` is its own net with a single tie point to the ground plane.

## 12. Open items

| # | Item | Blocks |
|---|---|---|
| 1 | nPM1300 product specification PDF (pins, inductors, capacitors, charge settings, I2C address, NTC, ship mode). Not yet saved. | power sheet |
| 2 | MX25R3235F datasheet PDF (pins, package, supply decoupling) | memory sheet |
| 3 | Battery cell, battery connector and the cell's thermistor type | power sheet |
| 4 | Passive part numbers: choose one MPN per value, get the series datasheet, check DC-bias derating | all sheets |
| 5 | VEMD8080 pad numbering vs the reference footprint (`REFERENCE_DESIGNS.md`): our footprint follows Vishay's drawing | optical footprint |
| 6 | MAX86141 SCLK maximum: confirm the printed value in the electrical table (4 MHz or 8 MHz) | firmware only |
| 7 | MAX86141 footprint: pads (0.21 mm round, 0.4 mm pitch) come from the MAXREFDES103 fab data. Confirm with ADI Application Note 1891 and package outline 21-100134. | footprint |
| 8 | OCVPB21 operating range is -30 to +65 degC: confirm against the band's required range. Also confirm the A1 corner against the package marking. | client, footprint |
| 9 | Display, haptic driver, pressure sensor and NFC reader are not in the selected-parts list and are not on these sheets | scope |
| 10 | MAX30208 land pattern 90-100101: the footprint pads are scaled from the pin drawing and must be replaced | footprint |
| 11 | Tag-Connect TC2030 pin order (assumed 1 VTREF, 2 SWDIO, 3 nRESET, 4 SWDCLK, 5 GND, 6 SWO): confirm against the cable drawing | test sheet |
| 12 | Pogo pad diameter (2.6 mm is a placeholder) and pad spacing: dock contact vendor | footprint |
| 13 | Crystal part numbers (32 MHz 2016 CL 8 pF, 32.768 kHz 2012 CL 9 pF) | BOM |

## 13. GPIO allocation (nRF54L15)

| Signal | Pin | Why this pin |
|---|---|---|
| SPI SCK | P2.01 (pin 12) | SPIM00 dedicated clock pin; data pins P2.02, P2.04 sit next to it (datasheet 10.1.2) |
| SPI MOSI / MISO | P2.02 (13) / P2.04 (15) | SPIM00 SDO / SDI |
| CS MAX86141 / CS flash | P2.05 (16) / P2.00 (11) | SPIM00 CSN / DCX pins used as plain GPIO |
| I2C SCL / SDA | P0.04 (29) / P0.03 (28) | TWIM30 in the low-power domain; P0.04 is a clock pin |
| PPG INT, IMU INT1, IMU INT2 | P0.00, P0.01, P0.02 | low-power domain inputs for wake-up |
| TEMP alarm, charger FLAG | P2.03, P2.06 | plain inputs |
| LED boost enable | P2.08 | plain output, 100 kOhm pull-down on the board (errata 103) |
| PPG GPIO1, GPIO2 | P2.09, P2.10 | spare lines to the MAX86141 |
| PMIC interrupt | P1.08 | the only P1 pin that is not in any power-on errata list |
| SWO | P2.07 | trace output pin, to the programming pads |
| Not used | P1.02-P1.07, P1.09-P1.14 | NFC pins and errata 100 pins |
