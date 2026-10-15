# PPG Front-End — MAX86141 + SFH 7016 + 2 × VEMD8080

Brief §8:
- MAX86141: "Confirm logic levels, LED supply, timing, optical design and assembly capability."
- SFH 7016: "Validate green/red/IR current, thermal rise, window loss and supply."
- VEMD8080: "Validate detector spacing, capacitance, saturation, ambient-light behavior and crosstalk."

---

## 1. Verified part data

| Part | Item | Value | Source |
|---|---|---|---|
| MAX86141 | Package | 20-bump WLP, 2.048 × 1.848 mm, 0.4 mm pitch | [ADI](https://www.analog.com/en/products/max86141.html) |
| | Supplies | VDD 1.8 V · PVLED 3.1–5.5 V | ADI |
| | Interface | SPI | ADI |
| | Optical channels | 2 readout channels (one per photodiode), 19-bit charge-integrating ADC, ambient light cancellation | [ADI datasheet (Farnell copy)](https://www.farnell.com/datasheets/2580845.pdf) |
| | LED drivers | 3 drivers, full-scale 31 / 62 / 93 / 124 mA ranges | same |
| | Exposure (integration) time | 14.8 / 29.4 / 58.7 / 117.3 µs | same |
| | On-chip averaging | 1–128 samples | same |
| | Power | < 10 µA readout at 25 sps · 1.6 µA shutdown | same |
| SFH 7016 | Emitters | 530 / 655 / 940 nm centroid, independently driven | [ams OSRAM DS v1.5](https://look.ams-osram.com/m/566c673078988944/original/SFH-7016.pdf) |
| | Vf @ 20 mA (typ / max) | G 2.40 / 2.80 · R 1.90 / 2.20 · IR 1.30 / 1.50 V | same |
| | Max DC / max pulse | G 30 mA / 0.75 A (≤ 50 µs) · R 40 mA / 0.3 A (≤ 900 µs) · IR 60 mA / 1 A (≤ 60 µs), D ≤ 0.005 | same |
| | Rth junction–solder (typ) | G 210 · R 260 · IR 320 K/W | same |
| | Brightness tempco | G −0.35 · R −0.7 · IR −0.3 %/K | same |
| | Size | 1.85 × 1.65 × 0.6 mm | same |
| VEMD8080 | Size / area | 4.8 × 2.5 × 0.48 mm / 4.5 mm² | [Vishay](https://www.vishay.com/en/product/84565/) |
| | Capacitance | 47 pF at 0 V | [DigiKey](https://azcus.digikey.com/en/products/detail/vishay-semiconductor-opto-division/VEMD8080/8602378) |
| | Spectral range | 350–1100 nm, ±65° | Vishay |

---

## 2. Answers to the brief's review points

### 2.1 Logic levels

The MAX86141 runs on **1.8 V VDD**, so its SPI and INT are 1.8 V logic. **Put the SoC I/O on the same 1.8 V rail** (power-battery POWER_TREE): the nRF54L15 can run its whole VDD at 1.8 V. Then no level translator is needed. The other digital parts accept 1.8 V I/O: BMI270, BMP390, MAX30208 and MX25R flash. The DRV2605L is powered from VSYS, so **check that its I²C/EN input-high threshold (VIH) is met by 1.8 V logic** before freezing the bus.

### 2.2 LED supply

**PVLED ≥ 3.1 V.** The driver needs headroom above the LED's Vf at the pulse current.

- **Green at 20 mA:** Vf is 2.40 V typ, 2.80 V max. It's higher at 40–60 mA, and +3.6 mV/K colder (TCV −3.6 mV/K).
- **Near-empty cell (3.4 V):** headroom for green is only a few hundred mV in the worst case.

This is why power-battery recommends laying out a small boost with a bypass link on P0. **Bench test:** sweep PVLED from 3.0 to 4.2 V at the planned green pulse current, and log the PPG DC level and noise. The voltage where the DC level starts to fall is the dropout.

### 2.3 LED current and thermal rise

LED average power in PPG is tiny because the pulses are microseconds long:

- WHOOP-like setting: 40 mA × 117 µs × 2 × 100 sps → duty ≈ 2.3 % → **≈ 0.94 mA average**.
- At Vf ≈ 3 V that's **≈ 3 mW** in the green die.
- With Rth ≈ 210 K/W junction-to-solder, the junction rises **≈ 0.6 K above the board**. That's negligible.
- **Max ratings are not a concern** at these settings (DC 30 mA, pulse 0.75 A).

**What does matter thermally** is skin-side heating, which biases the skin-temperature trend (sensors SKIN_TEMP). 3 mW is still small, so keep the LED area thermally separate from the MAX30208 contact anyway.

### 2.4 Timing

- The AFE has an **internal sample clock**, separate from the SoC's 32.768 kHz/HFCLK. Over minutes the two drift by its tolerance (check the datasheet value).
- **Read the FIFO on interrupt and timestamp in SoC time**, then resample. Never assume nominal sps. See sensors TIME_SYNC.md.
- For SpO2, red and IR are **interleaved within each sample frame**, so their ratio isn't affected by clock drift.

### 2.5 Photodiode capacitance and saturation

- The MAX86141 is built for large-area photodiodes in **zero-bias photovoltaic mode**, with the PD connected directly to its inputs and **no external TIA**. 47 pF is within its intended range; confirm the maximum input capacitance in the datasheet.
- **Saturation:** the ADC and ALC have a maximum ambient current. A 4.5 mm² diode in sunlight with a poor light seal can exceed it. The real fix is the opaque seal and window design (OPTICAL_DESIGN.md), not the electronics.
- **Two diodes on two channels** give spatial diversity: pick the better channel per sample window, or average. Also useful for motion-artifact detection.

### 2.6 Assembly

- WLP 0.4 mm pitch: Type 4/5 solder paste, stencil ≤ 100 µm, X-ray after reflow, no hand rework. The CSP version of the nRF54L15 has the same need, so one HDI-capable assembler covers both.
- **Optical parts (SFH 7016, VEMD8080) are silicone-encapsulated or open-window.** Keep no-clean flux off the optical faces; mask or clean per vendor notes. Don't conformal-coat the optical faces.

---

## 3. Sample rates

| Use | Rate | Why |
|---|---|---|
| HR at rest | 25 sps is enough | HR band 0.5–3.5 Hz. Spectral and peak methods work at 25 sps |
| HR during motion | 50–100 sps | better artifact separation with accelerometer reference |
| SpO2 (red + IR) | 50–100 sps per colour | pulse amplitude ratio; higher rate helps motion detection |
| **HRV (beat-to-beat)** | **≥ 100 sps with interpolation of the peak** | 10 ms raw resolution at 100 sps; parabolic/spline peak interpolation gets timing to ≈ 1–2 ms. RMSSD at rest is often 20–60 ms, so timing error must be small |
| Respiratory rate (P1) | 25 sps is enough (the signal is 0.1–0.5 Hz) | uses beat-to-beat and baseline modulation |

**Hardware conclusion:** support **100 sps with 2× averaging** on all channels. Battery life then depends on how long it runs per day (see power-battery). **Nothing in P1 (HRV, respiration, staging) needs more than this hardware.**

## 4. Starting register plan (to tune on the bench)

| Mode | LEDs | Exposure | Averaging | sps | LED current |
|---|---|---|---|---|---|
| Day HR | green | 58.7 µs | 1 | 25–50 | auto-ranged 10–40 mA |
| Workout HR | green | 117.3 µs | 2 | 100 | auto-ranged |
| Sleep HR + HRV | green | 117.3 µs | 2 | 100 | auto-ranged |
| SpO2 window | red, IR (+ green for HR) | 117.3 µs | 2 | 100 | auto-ranged to keep DC at ~50–70 % of full scale |
| Off-wrist check | IR, low current | 14.8 µs | 1 | 1 | 5 mA |

**Auto-ranging:** adjust LED current so the DC level stays in a target window, so dark or thick skin gets more current and fair skin less. The current is **logged with each sample**, because SpO2 calibration needs it.

**Off-wrist detection:** a low-power IR "proximity" check every second stops the LEDs from running into the air. This saves power and stops fake HR readings.
