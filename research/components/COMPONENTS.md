# HealthOS Band — Component Catalogue (Rev 1.1)

Every part named in brief §8, plus the alternatives worth evaluating before schematic freeze.

**Rules used in this file**

- Numbers come from the manufacturer datasheet or product page linked under each part. Anything not confirmed from a source is marked **(unverified)**.
- Prices are indicative only and marked unverified. Check a distributor before quoting.
- "Finding" answers the brief's "Review requirement" column for that part.

Checked: 2026-10-14.

---

## Quick reference

| # | Function | Part | Package | Body (mm) | Interface | Key supply | Lowest-power state |
|---|---|---|---|---|---|---|---|
| 1 | BLE SoC | nRF5340-QKAA | aQFN-94 | 7.0 × 7.0 | — | VDD 1.7–3.6 V, VDDH 2.5–5.5 V | System ON + RTC ≈ 1.6–2.3 µA |
| 2 | PMIC | nPM1300-QEAA | QFN-32 | 5.0 × 5.0 | I²C | VBUS 4.0–5.5 V | Ship 370 nA, Hibernate 500 nA |
| 3 | PPG AFE | MAX86141ENP+ | WLP-20, 0.4 mm pitch | 2.048 × 1.848 | **SPI** | VDD 1.8 V, PVLED 3.1–5.5 V | Shutdown 1.6 µA |
| 4 | PPG emitter | SFH 7016 | 6-pad SMT, silicone | 1.85 × 1.65 × 0.6 | — | Vf G 2.4 / R 1.9 / IR 1.3 V typ | — |
| 5 | Photodiode ×2 | VEMD8080 | 8-pad SMD | 4.8 × 2.5 × 0.48 | — | photovoltaic (0 V) | passive |
| 6 | IMU | BMI270 | LGA-14 | 2.5 × 3.0 × 0.8 | I²C / SPI | 1.71–3.6 V | Suspend ≈ 3.5 µA |
| 7 | Pressure | BMP390 | LGA-10, vented lid | 2.0 × 2.0 × 0.75 | I²C / SPI | 1.65–3.6 V | Sleep < 1 µA |
| 8 | Skin temp | MAX30208CLB+ | Thin LGA-10 | 2.0 × 2.0 × 0.75 | I²C | 1.7–3.6 V | Standby 0.5 µA |
| 9 | Haptic driver | DRV2605L | DSBGA-9 (YZF) or VSSOP-10 (DGS) | 1.5 × 1.5 / 3 × 3 | I²C | 2.0–5.2 V | Shutdown 4 µA |
| 10 | NOR flash | W25Q32RVXHJQ | XSON-8 | 2 × 3 | SPI / Quad | 2.7–3.6 V | Deep power-down (see §10) |
| 11 | NFC reader | ST25R210 | UQFPN-28 | 4 × 4 | SPI | (see §11) | LPCD |
| 12 | Pogo protection | OCVPB21-13F6 | WLCSP-13, 0.4 mm pitch | (unverified) | — | ±13 V OVP | — |
| 13 | Display | 0.49" 64×32 PMOLED, SSD1306 | FPC panel | 14.5 × 11.6 × 1.2 (one variant) | I²C | VDD + internal charge pump | Sleep (display off) |

---

## 1. Nordic nRF5340-QKAA — BLE and application controller

| Item | Value | Source |
|---|---|---|
| Cores | App: Cortex-M33 @ 128/64 MHz, 1 MB flash, 512 KB RAM. Net: Cortex-M33 @ 64 MHz, 256 KB flash, 64 KB RAM | [Nordic PS v1.3.1](https://infocenter.nordicsemi.com/pdf/nRF5340_PS_v1.3.1.pdf) |
| Package | aQFN-94, 7 × 7 mm, 0.4 mm pitch (QKAA). Also a WLCSP (CLAA) | PS v1.3.1 |
| Supply | VDD 1.7–3.6 V, or VDDH 2.5–5.5 V via the internal high-voltage regulator (can run straight from a Li-ion cell) | PS v1.3.1 |
| GPIO | 48 | PS v1.3.1 |
| Radio current | TX 0 dBm: 3.2 mA · RX 1 Mbps: 2.6 mA (DC/DC, 3 V) | PS v1.3.1; [Mouser summary](https://www.mouser.in/new/nordic-semiconductor/nordic-nrf5340-soc) |
| Sleep | System ON with RTC: ≈ 1.6–2.3 µA depending on LFCLK source | [Nordic DevZone](https://devzone.nordicsemi.com/f/nordic-q-a/102217/nrf5340-system-on-sleep-current) |
| Max TX power | +3 dBm | PS v1.3.1 |
| Peripherals | QSPI, 4× serial (SPI/I²C/UART), USB FS, NFC-A tag, I²S, PDM, 12-bit SAADC | PS v1.3.1 |
| Temperature | −40 to +105 °C | PS v1.3.1 |

**Review requirement:** compare with nRF54.

**Finding:** there's a full trade study on branch `rnd/mcu-ble`. The two headline facts:

1. The nRF54L15 has **no VDDH input**. Its supply range is 1.7–3.6 V, so it needs a regulated rail from the nPM1300, while the nRF5340 can sit directly on VBAT.
2. The nRF54L15's radio draws **more** current per the product page: TX 4.8 mA, RX 3.4 mA at 3 V. In exchange it's single-core, smaller (QFN-48 6×6 or CSP 2.25×2.45) and has lower sleep current.

**Wearable gotchas**

- aQFN-94 needs a 4–6 layer board with fine-pitch via-in-pad or dog-bone escape.
- The 32 MHz crystal is mandatory. The 32.768 kHz crystal is optional (the internal RC works, but costs sleep current and timing accuracy).
- The free NFC-A tag pins (NFCT) can give a passive NFC tag at almost no cost. Compare this with the active ST25R210 (§11).

Price: ≈ USD 6–8 at 1k (unverified).

---

## 2. Nordic nPM1300-QEAA — PMIC, charger, fuel gauge

| Item | Value | Source |
|---|---|---|
| Charger | Linear Li-ion/LiPo, 32–800 mA, JEITA with NTC input, termination 3.5–4.45 V (unverified range) | [nPM1300 PS v1.0](https://infocenter.nordicsemi.com/pdf/nPM1300_PS_v1.0.pdf) |
| Regulators | 2 × 200 mA buck (dual mode), 2 × 50 mA LDO or 100 mA load switch | [Nordic product page](https://www.nordicsemi.com/Products/nPM1300) |
| Fuel gauge | Algorithm-based, runs on the host using the nPM1300 ADC (V, I, T) | nPM1300 PS |
| LED drivers | 3 × 5 mA | product page |
| Low-power modes | Ship 370 nA · Hibernate 500 nA | product page |
| GPIO / misc | 5 GPIO, watchdog, hard reset, timer wake | product page |
| Package | QFN-32, 5 × 5 mm (QEAA). A WLCSP is also offered | PS |

**Review requirement:** recalculate rails and concurrent peak.

**Findings**

- **The buck outputs top out at 3.3 V.** The MAX86141 LED supply (PVLED) needs **3.1–5.5 V**, so the LEDs must run from VBAT or a small boost. They cannot come off a buck. See `rnd/power-battery` → POWER_TREE.md.
- The two 200 mA bucks set the ceiling for every regulated load added together. Peaks from the LRA and the LED pulses should come from VBAT, not from a buck.
- The fuel gauge is a software model. It needs the cell's battery profile (Nordic tooling builds one from a discharge of the actual cell), so pick the cell early.

Price: ≈ USD 2.5–3.5 (unverified).

---

## 3. Analog Devices MAX86141 — optical AFE

| Item | Value | Source |
|---|---|---|
| Function | 2 optical readout channels, 3 LED drivers (up to 6 LEDs) | [ADI MAX86140/86141 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/max86140-max86141.pdf) |
| Package | 20-bump WLP, 2.048 × 1.848 mm, 0.4 mm pitch | [ADI product page](https://www.analog.com/en/products/max86141.html) |
| Supplies | VDD 1.8 V (digital/analog) · PVLED 3.1–5.5 V (LED driver) | ADI product page |
| Interface | **SPI** (not I²C) | ADI product page |
| ADC | 19-bit charge-integrating, ambient light cancellation | datasheet |
| LED current | 31–124 mA full-scale ranges per driver | [Farnell copy of datasheet](https://www.farnell.com/datasheets/2580845.pdf) |
| Power | < 10 µA typ readout channel at 25 sps · shutdown 1.6 µA typ | Farnell datasheet copy |
| FIFO | 128-sample, with interrupt | datasheet |

**Review requirement:** logic levels, LED supply, timing, optical design, assembly.

**Findings**

- **Logic level:** VDD and I/O are 1.8 V. The nRF I/O rail must be 1.8 V, or the SPI lines need level translation. The simplest answer is to run the whole digital domain at 1.8 V; every other sensor here accepts it.
- **LED supply:** PVLED ≥ 3.1 V. On a 3.0–4.2 V cell, PPG drops out near empty unless a boost is added (see power branch).
- **Timing:** the AFE has its own oscillator and FIFO. For motion-artifact work its samples have to be timestamped against the IMU (see `rnd/sensors` TIME_SYNC.md).
- **Assembly:** a 0.4 mm WLP needs Type 4/5 paste, X-ray inspection, and no hand rework.

Price: ≈ USD 4–5 (unverified).

---

## 4. ams OSRAM SFH 7016 — PPG emitter

Source: [SFH 7016 datasheet v1.5 (2022-04-12)](https://look.ams-osram.com/m/566c673078988944/original/SFH-7016.pdf), [product page](https://ams-osram.com/products/leds/multi-color-leds/osram-multi-chip-led-sfh-7016).

| Parameter | Green | Red | IR |
|---|---|---|---|
| Centroid λ (typ) | 530 nm | 655 nm | 940 nm |
| Max DC IF | 30 mA | 40 mA | 60 mA |
| Max pulse IF (D ≤ 0.005) | 0.75 A (tp ≤ 50 µs) | 0.3 A (tp ≤ 900 µs) | 1 A (tp ≤ 60 µs) |
| Vf min/typ/max @ 20 mA | 2.20 / 2.40 / 2.80 V | 1.70 / 1.90 / 2.20 V | 1.10 / 1.30 / 1.50 V |
| Ie @ 20 mA min/typ/max | 2.2 / 4.0 / 5.4 mW/sr | 2.5 / 4.2 / 7.0 mW/sr | 1.65 / 3.0 / 4.05 mW/sr |
| Half angle | ±60° | ±60° | ±60° |
| Rth J-S typ | 210 K/W | 260 K/W | 320 K/W |
| Brightness tempco | −0.35 %/K | −0.7 %/K | −0.3 %/K |

Package: 1.85 × 1.65 × 0.6 mm, clear silicone, emitters independently driven. ESD 2 kV HBM.

**Review requirement:** green/red/IR current, thermal rise, window loss, supply.

**Findings**

- **Headroom:** green Vf reaches 2.8 V max at 20 mA and climbs further at the 50–100 mA pulses PPG uses. Add the MAX86141 driver dropout and the 3.1 V PVLED floor, and the LED supply is the tightest point in the design. Characterise green Vf at the planned pulse current over temperature.
- **Red tempco** (−0.7 %/K) is the largest of the three, and SpO2 depends on the red/IR ratio. Skin-contact temperature drift directly biases SpO2, so the calibration has to include temperature.
- The red pulse limit (0.3 A) is far below green and IR, so it sets the maximum SpO2 drive.

---

## 5. Vishay VEMD8080 — photodiode (×2)

Source: [Vishay product page 84565](https://www.vishay.com/en/product/84565/), [DigiKey listing](https://azcus.digikey.com/en/products/detail/vishay-semiconductor-opto-division/VEMD8080/8602378).

| Item | Value |
|---|---|
| Package | 4.8 × 2.5 × 0.48 mm low-profile SMD |
| Sensitive area | 4.5 mm² |
| Spectral range | 350–1100 nm, peak ≈ 850 nm |
| Capacitance | 47 pF typ at VR = 0 V, 1 MHz |
| Rise time | 70 ns typ (VR = 10 V, RL = 1 kΩ) |
| Half-sensitivity angle | ±65° |

**Review requirement:** spacing, capacitance, saturation, ambient light, crosstalk.

**Findings**

- **Bias:** the MAX86141 runs photodiodes at **zero bias** (photovoltaic mode). The 47 pF at 0 V is the figure that matters, not any reverse-bias value.
- **Ambient light:** the AFE cancels ambient, but direct sunlight on a 4.5 mm² area can still saturate it. An opaque gasket and an IR-cut or green filter on the window decide whether outdoor HR works.
- **Board area:** each diode is 4.8 × 2.5 mm, so two of them plus the emitter set the minimum width of the optical island.

---

## 6. Bosch BMI270 — IMU

Source: [BMI270 datasheet (Bosch via Mouser)](https://www.mouser.com/datasheet/2/783/BST_BMI270_FL000-1530947.pdf).

| Item | Value |
|---|---|
| Package | LGA-14, 2.5 × 3.0 × 0.8 mm |
| Supply | VDD 1.71–3.6 V, VDDIO 1.2–3.6 V |
| Interface | I²C (1 MHz), SPI (10 MHz), plus an auxiliary I²C master |
| Accel / gyro range | ±2–16 g / ±125–2000 °/s |
| Current | 685 µA full operation (accel + gyro) · ≈ 3.5 µA suspend. Accel-only low-power is in the tens of µA (exact figure unverified) |
| FIFO | 2 KB |
| Built-in features | Step counter/detector, activity recognition, wrist gestures, wrist wear wake-up, any/no-motion. These are part of the "wearable" config file loaded at boot |

**Review requirement:** orientation, interrupts, power modes, software.

**Findings**

- **Gyro power:** the gyro is what costs 685 µA. Keep it off except during workouts. Accel-only operation plus the built-in features is the sleep and daytime mode.
- **Config blob:** the 8 KB config has to be uploaded at every power-up, which costs boot time and an I²C burst.
- **Interrupts:** wire **both** INT pins, one for motion events and one for FIFO watermark.

Price ≈ USD 1.5–2 (unverified).

---

## 7. Bosch BMP390 — pressure

Source: [BMP390 datasheet](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp390-ds002.pdf).

| Item | Value |
|---|---|
| Package | LGA-10 with vent hole, 2.0 × 2.0 × 0.75 mm |
| Range | 300–1250 hPa |
| Relative accuracy | ±0.03 hPa (≈ ±25 cm), 700–1100 hPa, 25–40 °C |
| Absolute accuracy | ±0.50 hPa |
| Current | 3.2 µA at 1 Hz |
| Interface | I²C / SPI, 512-byte FIFO |

**Review requirement:** waterproof breathable vent and contamination protection.

**Finding:** one floor is about 3 m, or roughly 0.36 hPa. That's well above the sensor's resolution, so the real limits are the vent (an ePTFE membrane) and wrist-height and temperature artifacts. Details in `rnd/sensors` PRESSURE_BMP390.md.

---

## 8. Analog Devices MAX30208 — skin temperature

Source: [MAX30208 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX30208.pdf).

| Item | Value |
|---|---|
| Package | Thin LGA-10, 2 × 2 × 0.75 mm |
| Accuracy | ±0.1 °C (30–50 °C), ±0.15 °C (0–70 °C) |
| Resolution | 16-bit, 0.005 °C |
| Current | 67 µA during conversion · 0.5 µA standby |
| Supply | 1.7–3.6 V |
| Interface | I²C, 32-word FIFO, high/low alarms, 2 GPIO |

**Finding:** the part is accurate enough. The accuracy of the result depends on the thermal path. ADI designs the package so its bottom side faces the skin through a flex or a thin board with a thermal via pad, isolated from the main board. See `rnd/sensors` SKIN_TEMP_MAX30208.md.

---

## 9. TI DRV2605L — haptic driver

Source: [TI DRV2605L datasheet](https://www.ti.com/lit/ds/symlink/drv2605l.pdf).

| Item | Value |
|---|---|
| Package | DSBGA-9 (YZF) ≈ 1.5 × 1.5 × 0.625 mm max height, or VSSOP-10 (DGS) 3 × 3 mm |
| Supply | 2.0–5.2 V (runs from VBAT) |
| Interface | I²C, plus PWM/analog input, EN pin |
| Actuators | ERM and LRA. LRA auto-resonance tracking (closed loop) |
| Effects library | Licensed TouchSense (Immersion) ROM, 6 libraries / 123 effects |
| Current | Iq 0.5 mA when active · shutdown 4 µA typ (EN low) |

**Finding:** use the **DSBGA** package, which is about 15× smaller than the VSSOP. Gate EN from a GPIO; 4 µA in shutdown is acceptable, but EN still has to be held low. Peak current is set by the LRA (≈ 75–100 mA for an 8 mm coin, see §15), not by the driver.

---

## 10. Winbond W25Q32RVXHJQ — 32 Mbit NOR flash

Sources: [DigiKey W25Q32RVXHJQ-TR](https://www.digikey.com/es/products/detail/winbond-electronics/W25Q32RVXHJQ-TR/22146347), [Winbond W25Q32RV](https://www.winbond.com/hq/search/?q=W25Q32RV).

| Item | Value |
|---|---|
| Package | XSON-8, 2 × 3 mm |
| Supply | 2.7–3.6 V |
| Interface | SPI / Dual / Quad, 133 MHz |
| Page program | 2 ms typ (DigiKey "write cycle time") |
| Temperature | −40 to +105 °C |
| Deep power-down | (unverified, check the datasheet; Winbond 3 V parts are typically ≈ 1 µA) |

**Finding:** this is a **3 V-only** part. If the digital domain runs at 1.8 V (forced by the MAX86141), it either needs its own 3 V rail and level shifting, or should be swapped for a wide-voltage part. The **Macronix MX25R3235F** (1.65–3.6 V, deep power-down 0.35 µA max, USON 2×3 or WLCSP) removes that problem; see §14.

---

## 11. ST ST25R210 — active NFC reader (conditional)

Sources: [ST product page](https://www.st.com/en/nfc/st25r210.html), [ST community launch note](https://community.st.com/other-hardware-and-tools-166/new-aliro-ready-nfc-reader-for-secure-access-control-designs-163852).

| Item | Value |
|---|---|
| Package | UQFPN-28, 4 × 4 mm |
| Output power | up to 1.6 W |
| Features | Low-power card detection (LPCD), Aliro-ready (access control) |
| Protocols | NFC-A/B, NFC-V; check the datasheet for NFC-F |
| Run current | (unverified; get it from the datasheet once a use case exists) |

**Finding:** a 1.6 W field can't come from a 200 mA buck, so the RF stage must run from VBAT. That stacks with LED and haptic peaks. **Recommendation:** leave it off P0 unless the client names a use case. The nRF5340 NFCT pin already gives a passive tag (tap-to-pair) at no BOM cost.

---

## 12. ST OCVPB21-13F6 — pogo-input protection

Sources: [ST product page](https://www.st.com/ja/protections-and-emi-filters/ocvpb21-13f6.html), [RS listing](https://th.rs-online.com/web/p/tvs-diodes/2162708).

| Item | Value |
|---|---|
| Function | ESD + OVP + OCP + **input rectification bridge** for reversible charging, plus USB data-line polarity mux |
| ESD | IEC 61000-4-2 level 4: ±15 kV contact on bridge inputs |
| OVP | up to ±13 V |
| OCP | adjustable 100–500 mA (external resistor) |
| Data-line mux | RON 6 Ω typ (not needed here: the brief says pogo pins carry no USB data) |
| Package | WLCSP, 13 bumps, 0.4 mm pitch |
| Temperature | −30 to +65 °C |

**Findings**

- **Orientation:** the bridge solves the brief's "reversible two-contact pogo" requirement in a single part.
- **Current cap:** the 500 mA OCP is the maximum, which is well above the ≈ 1C charge current a 150–250 mAh cell will use.
- **Temperature limit:** the −30 to +65 °C rating is narrower than the other parts here. Confirm it covers the charging environment.
- **Unused function:** the data-mux half goes unused. ST also lists an OCVPB22-14F6 variant that is worth comparing.

---

## 13. Display — 0.49" 64×32 PMOLED (SSD1306)

Sources: [Waveshare 0.49" module](https://www.waveshare.com/0.49inch-oled-module.htm), [BuyDisplay 0.49" 64×32](https://www.buydisplay.com/i2c-white-0-49-inch-oled-display-module-64x32-arduino-raspberry-pi), [Tinytronics](https://www.tinytronics.nl/shop/en/displays/oled/0.49-inch-oled-display-64*32-pixels-white-i2c).

| Item | Value |
|---|---|
| Resolution | 64 × 32, monochrome (usually white) |
| Active area | 11.18 × 5.58 mm |
| Panel outline | 14.5 × 11.6 × 1.2 mm (one variant). Others differ, so get the drawing per supplier |
| Controller | SSD1306 (COG), I²C |
| Panel supply | SSD1306 internal charge pump generates VCC (≈ 7–9 V) from VBAT/VDD (exact limits unverified per panel) |

**Review requirement:** exact module, colour, flex, cover stack, power-off topology.

**Findings**

- **Buy the bare panel, not a hobby module.** The Waveshare and BuyDisplay boards add a regulator and pull-ups and are only good for bench evaluation. For the product, buy the **bare COG panel with FPC** (14-pin class) and lay out the charge-pump capacitors yourself.
- **Back-power:** drive I²C pull-ups from the switched display rail, and set SDA/SCL to disconnected or low before switching it off. Otherwise the SSD1306 is back-powered through its ESD diodes.
- Off-state appearance and dead-front transmission are covered in `rnd/display-haptics`.

---

## 14. Alternatives

### MCU — nRF54L15 / L10 / L05

Source: [Nordic nRF54L15 product page](https://www.nordicsemi.com/products/nrf54l15).

| Item | nRF54L15 | vs nRF5340 |
|---|---|---|
| CPU | Cortex-M33 @ 128 MHz + RISC-V coprocessor | single radio/app core |
| Memory | 1.5 MB NVM (RRAM), 256 KB RAM. L10: 1 MB/192 KB · L05: 0.5 MB/96 KB, pin-compatible | less RAM |
| Packages | CSP47 2.25 × 2.45 mm, QFN48/QFN52 6 × 6 mm, QFN40 | much smaller |
| Supply | **1.7–3.6 V only** | no VDDH |
| Radio | TX 0 dBm 4.8 mA, RX 3.4 mA (@ 3 V); max +8 dBm (CSP) | higher per-packet current, higher max power |
| Sleep | 0.7–2.9 µA | similar |
| GPIO | 31 (QFN48), 32 (CSP47) | fewer; count needed (see mcu-ble) |

### Optical AFE

- **MAX86176** (ADI): PPG + ECG AFE. Pick it only if ECG becomes a P1 feature. [ADI](https://www.analog.com/en/products/max86176.html)
- **MAXM86161A** (ADI): integrated module with AFE, LEDs and photodiode on a single supply. It cuts optical design risk but fixes the spacing. [Mouser](https://www.mouser.in/new/analog-devices/adi-maxm86161a-modules/)
- **AS7058** (ams OSRAM): multi-vital AFE (PPG/ECG/BioZ), WLCSP. [Short datasheet](https://www.mouser.com/datasheet/2/588/ams_osram_11_8_2023_AS7058_ShortDatasheet_DS001085-3366997.pdf)

### Motion

- **BMA400** (Bosch): accel-only, a few µA, with built-in step counter and activity recognition. Loses the gyro for workout motion artifacts. [Datasheet](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bma400-ds000.pdf)
- **LIS2DW12** (ST): accel-only, ultra-low-power modes. [Datasheet](https://www.st.com/resource/en/datasheet/lis2dw12.pdf)

### Pressure

- **BMP581** (Bosch): lower noise and current than BMP390, 2 × 2 mm. [Datasheet](https://cdn.sparkfun.com/assets/9/a/4/4/f/BMP581-Datasheet.pdf)
- Gel-filled water-resistant parts (e.g. ST LPS27HHW, LPS33W) remove the membrane but need a port. Covered in the sensors branch.

### Temperature

- **TMP117** (TI): ±0.1 °C, 3.5 µA at 1 Hz, 250 nA shutdown. WSON-6 2 × 2 mm or DSBGA-6 1.53 × 1.0 mm, 1.8–5.5 V. [TI](https://www.ti.com/product/TMP117). A valid swap; it has no FIFO.
- **MAX30205** (ADI): older clinical body-temperature sensor. No advantage over MAX30208. [ADI](https://www.analog.com/en/products/max30205.html)

### Flash

- **Macronix MX25R3235F**: 32 Mbit, **1.65–3.6 V**, deep power-down 0.35 µA max, standby 24 µA max. USON 2×3 or WLCSP. [Mouser overview](https://www.mouser.in/new/macronix/macronix-mx25r-nor-flash/), [datasheet](https://www.macronix.com/Lists/Datasheet/Attachments/8755/MX25R3235F,%20Wide%20Range,%2032Mb,%20v1.8.pdf). **Recommended** if the I/O domain is 1.8 V.

---

## 15. LRA candidates

| Part | Type | Size | Rated | Resonance | Current | Accel | Source |
|---|---|---|---|---|---|---|---|
| Precision Microdrives C08-005 | Z-axis coin | Ø8 mm | 1.8 V rms | 235 Hz | 75 mA typ | 1.28 G typ | [PMD](https://www.precisionmicrodrives.com/?p=12426) |
| Vybronics VG0832012 / VG0832013D | Z-axis coin | Ø8 × 3.2 mm (0832) | 1.8 V AC | 235 Hz | 102 mA max | ≥ 0.61 G | [DigiKey](https://www.digikey.es/en/products/detail/vybronics-inc/VG0832012/7364317) |

The "0832" in the name means Ø8 mm × 3.2 mm thick. That thickness is likely the thickest single item after the battery, so check the enclosure stack-up. X-axis rectangular LRAs feel stronger in a band but are longer. Covered in `rnd/display-haptics` HAPTICS.md.

---

## 16. Battery

The cell isn't chosen yet. It has to come out of the power model (`rnd/power-battery` BATTERY_LIFE.md) and the enclosure volume.

Requirements from the brief: single cell, protected, pack NTC.

Selection checklist:

- capacity at the 0.2C rate
- maximum charge current (sets the nPM1300 ICHG)
- maximum continuous and pulse discharge (must cover LED, haptic and radio peaks)
- PCM trip current
- NTC value (10 kΩ B3435 suits nPM1300 defaults; verify)
- tab or wire termination
- swelling allowance (≈ 8–10 % of thickness)
- UN 38.3 and IEC 62133-2 reports from the cell maker

Pouch naming convention (e.g. 302030 = 3.0 × 20 × 30 mm) is used by most Chinese makers. Any candidate must come with a datasheet before it's listed here.

---

Done by Harsh Thakur.
