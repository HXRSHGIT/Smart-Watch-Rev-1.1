# Datasheet review of the schematic

Done by Harsh Thakur.

Every sheet was compared with the datasheet text and figures saved in `hardware/datasheets/`. "Checked" means the value or pin was read in the datasheet for this review. `tools/check.py` separately proves that the netlist equals the expected tables.

## Decisions needed (design is not wrong, but a choice is open)

| # | Where | Finding | Source | Options |
|---|---|---|---|---|
| D1 | power, mcu, optical | The nRF54L15 needs VDD of at least 1.75 V during power-on reset (VDD,POR). Buck 1 with 47 kOhm on VSET1 is 1.8 V +/-5 %, so 1.71 V at worst. MAX86141 allows 1.7 to 2.0 V. A 1.9 V rail (1.805 to 1.995 V) fits both. | nRF54L15 11.14.1; nPM1300 BUCK electrical spec; MAX86141 abs. max and recommended supply | (a) keep R16 = 47 kOhm and set BUCK1NORMVOUT = 1.9 V in the first firmware lines; (b) fit 68 kOhm (2.0 V default) and lower to 1.9 V in firmware. The net name stays +1V8. |
| D2 | power, input | nPM1300 input current limit steps are 100 mA (default) then 500 mA and up. The OCVPB21 with R14 = 180 Ohm limits at about 310 mA. | nPM1300 SYSREG; OCVPB21 section 1.2 | keep the nPM1300 at 100 mA, or set R14 = 51 Ohm (about 600 mA) to allow 500 mA |
| D3 | input | C24 is 10 uF 10 V X5R; the datasheet asks for 10 uF low ESR on OUT_5V, but a 10 V X5R part loses a lot of capacitance at 5 V. | OCVPB21 table 2 | choose a part with 10 uF or more at 5 V (for example 22 uF) |
| D4 | led_supply | VLED straight from VSYS (option A): the green LED needs about 3.7 V (2.8 V forward + 0.9 V driver headroom), so it drops out at the bottom of a 3.0 to 4.2 V cell. | SFH 7016 forward voltage; MAX86141 electrical table | use the boost (R12, default) |

## Firmware-facing findings (written into the sheet notes)

| Part | Finding | Source |
|---|---|---|
| MAX30208 | GPIO0 in INTB mode is open drain, active low. Set the mode first, then enable the processor pull-up on P2.03. An external pull-up would change the I2C address (GPIO state at each start condition sets address bits). | MAX30208 GPIO SETUP (0x20), Table 3 |
| MAX86141 | SCLK maximum 4 MHz while it is selected. The flash allows 33 MHz (read) but shares the bus. | MAX86141 electrical characteristics; MX25R3235F AC table |
| MAX86141 | VREF: datasheet 1 uF (fitted). Maxim's MAXREFDES103 board uses 10 uF. Try 10 uF if the noise floor is high. | MAX86141 pin description; MAXREFDES103 BOM item 3 |
| SFH 7016 | Continuous current green 30 mA, red 40 mA, IR 60 mA; pulse 0.75 / 0.3 / 1 A at 0.5 % duty. | SFH 7016 maximum ratings |
| nPM1300 | Never feed VSYS from outside; never supply the application from VBAT. A pack without NTC needs R17 fitted and the NTC function disabled in BCHGDISABLESET. The battery pack must carry its own protection. | nPM1300 charger, supported batteries, application |
| Johanson antenna | The eval board uses series 1.0 pF, shunt 2.7 nH, series 3.9 nH. The tee slots R2, C14, R3 follow note 4, but the shunt slot may need an inductor. | Johanson 2450AT18A0100001E datasheet page 3 |

## Per part

| Part | Checked and correct | Open |
|---|---|---|
| nRF54L15 (mcu, rf, test) | Pin table (49 pins, by script). Figure 180 / Table 87: every value and its node (C1 DECD, C2/C12/C5 on DECA, C3/C10 on VDD 47/48, C4/C7/C8 on VDD 10/22/36, L1, FB1, X1, X2, R1, C13, RF network). VSS_PA only at the exposed pad through NT1, C9 to bottom ground only through NT2. Peripheral pins: SPIM00 on P2 (SCK P2.01 clock pin, MOSI P2.02, MISO P2.04, CSN P2.05), TWIM30 on P0 (SCL P0.04 clock pin, SDA P0.03). NFC pins left open. VDD range 1.7 to 3.6 V. | D1. Not rechecked this round: crystal drive-level numbers, errata beyond 100 and 103, GPIO drive strength on the shared SPI. |
| nPM1300 (power) | QFN32 pin table, Reference Configuration 2: C1 1 uF on VBUS, C5 1 uF on VBUSOUT, C2 and C4 10 uF on PVDD/VSYS, C6 2.2 uF on VBAT, L 2.2 uH (DCR 0.4 Ohm, Isat above 350 mA), C7 10 uF, R3 47 kOhm (our R16), BUCK2 unused (VSET2 ground, VOUT2 to VSYS, SW2 open, PVSS2 ground), unused load switch pins grounded, CC1/CC2 grounded (allowed without USB-C), VDDIO on the 1.8 V rail with 100 nF, SHPHLD button, address 0x6B, default discharge limit 1 A. Absolute maximum and operating ranges. | D1, D2. QFN32 exposed pad 3.5 mm nominal vs footprint 3.45 mm. Battery connector and cell. Config 3 figure (fully unused load switches) could not be viewed, so the load switch pins follow Config 2. |
| MX25R3235F (memory) | Pin table, USON 4 x 3 mm 0.8 mm pitch, exposed metal pads (float or ground only), VCC 1.65 to 3.6 V, 100 nF at VCC, CS# pull-up, WP# and RESET# internal pull-ups, SPI mode 0 or 3, 33 / 8 MHz limits, POR and deep power-down notes. | Land pattern 0.35 x 0.9 mm drawn from the package outline. Rev 1.6 used; latest is 1.8. |
| MAX86141 (optical) | All 20 balls against the pin table. VDD_ANA and VDD_DIG tied (abs. max allows 0.3 V difference), 22 uF + 100 nF on the supply, 10 uF on VLED, 1 uF on VREF, PD_GND single-point ground (abs. max PD_GND within 0.3 V of GND_ANA), INT and GPIO open drain with pull-ups, unused GPIO2 open (allowed), input levels (VIH 1.4 V), LED channel order against MAXREFDES103. | D1, D4. MAX30208 and MAX86141 footprints marked CHECK. |
| SFH 7016 | Pin table, pad numbering against the package drawing (top view), pads 0.4 x 0.4 mm at 0.65 / 1.15 mm pitch against the recommended solder pad. LED to driver mapping. | Solder mask and stencil openings not drawn in the footprint. |
| VEMD8080 | Pinning figure: pin 5 anode, pins 1-4 and 6-8 cathode; pad pattern 1.31 / 1.38 / 1.31 and 2.38 mm. Closed. | |
| BMI270 | Table 22: SDO ground (0x68), CSB to VDDIO, ASDx and ASCx to VDDIO (not ground), OCSB and OSDO open, INT1 and INT2 as outputs, 100 nF on VDD and VDDIO. | Firmware must upload the configuration file. |
| MAX30208 | Pin table, GPIO1 ground and GPIO0 default input with 1 MOhm pulldown give 0x50, 0.1 uF on VDD, VDD 1.7 to 3.6 V. | GPIO0 firmware rule above. Land pattern CHECK. |
| TPS61240 | WSON pins (EN 4, FB 3, GND 1, L 5, VIN 6, VOUT 2, PowerPAD), inductor between VIN and L, 1.0 uH minimum, input 2.2 uF, output effective 2.7 uF or more, FB tied to VOUT, EN threshold 1.0 V, 200 mA output, load disconnect. | Inductor part number not verified for saturation current. |
| OCVPB21-13F6 | Pin table, IN_A and IN_B (D1, D3), RLIM formula (180 Ohm gives about 309 mA), COUT, FLAG pull-up, bump pattern and pad sizes. | D2, D3. A1 orientation to package marking (CHECK). |
| Tag-Connect | Pin order 1 VTREF, 2 SWDIO, 3 nRESET, 4 SWDCLK, 5 GND, 6 SWO matches the common Nordic SWD mapping. | Confirm against the Tag-Connect cable drawing. |

## Not checked

Passive manufacturer part numbers, crystals, battery cell, pogo contact vendor, PCB layout rules, firmware behaviour, and anything outside the datasheets in `hardware/datasheets/`.
