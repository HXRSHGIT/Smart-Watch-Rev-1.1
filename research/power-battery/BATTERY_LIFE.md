# Battery Life — Model, Results, Cell Choice

Brief §4.7: "at least five days of normal use, with seven days as a stretch goal. The owner must approve the target after battery volume and measurement schedules are modeled."

This file is that model. Script: [`battery_model.py`](battery_model.py), standard-library Python. Run it with `python battery_model.py`. It has built-in self-checks.

---

## 1. Method

- Every load is turned into the **average current drawn from the cell**.
- **Buck-fed loads** (1.8 V rail) are converted through power: `I_bat = I × 1.8 V / (3.7 V × 0.88)`.
- **VBAT-fed loads** (PPG LED driver, LRA, OLED charge pump) count 1:1.
- PPG LED average = pulse current × pulse width × pulses per sample × sample rate. Pulse widths are the MAX86141's integration-time settings (14.8 / 29.4 / 58.7 / 117.3 µs) and sample averaging 1–128 ([ADI datasheet via Farnell](https://www.farnell.com/datasheets/2580845.pdf)).
- **Usable capacity = 80 %** of the rating, to cover the 3.0 V cut-off, cold, and ageing to about 80 % after a year of daily charging.

### Inputs

| Input | Value | Source |
|---|---|---|
| nRF54L15 sleep | 0.7–2.9 µA @ 3 V (2 µA used) | [Nordic](https://www.nordicsemi.com/products/nrf54l15) |
| nRF54L15 TX 0 dBm / RX | 4.8 / 3.4 mA @ 3 V | Nordic |
| nRF54L15 CPU | 2.6 mA @ 3 V, derived from 193 CoreMark/mA | Nordic (derived, **assumed**) |
| MAX86141 | < 10 µA @ 25 sps, scaled with sps (**assumed**) | ADI |
| BMI270 accel low-power 25 Hz | 210 µA | [datasheet excerpt (secondary)](https://wiki.adom.inc/adom/bmi270), **verify** |
| BMI270 accel + gyro | 685 µA | Bosch |
| BMP390 @ 1 Hz | 3.2 µA | Bosch |
| MAX30208 | 0.5 µA standby, 67 µA converting | ADI |
| MX25R3235F deep power-down | 0.35 µA max | Macronix |
| DRV2605L shutdown | 4 µA | TI |
| LRA drive | 90 mA (75 typ / 102 max for 8 mm coins) | PMD, Vybronics |
| OLED on | 10 mA at ~25 % pixels lit | **assumed**, measure |
| nPM1300 + cell protection IC | 3 + 3 µA | **assumed** |

---

## 2. Three use profiles

| Profile | PPG (HR, all day) | SpO2 at night | Gyro | BLE sync | Display wakes | Haptic events | CPU duty |
|---|---|---|---|---|---|---|---|
| **Lean** | 20 mA × 58.7 µs × 1 × 25 sps | 24 min | 0.5 h | 10 s/h | 15 | 10 | 0.5 % |
| **Typical** | 30 mA × 117.3 µs × 1 × 50 sps | 48 min | 1 h | 20 s/h | 25 | 15 | 1 % |
| **WHOOP-like** | 40 mA × 117.3 µs × 2 avg × 100 sps | 96 min | 1 h | 30 s/h | 30 | 20 | 2 % |

## 3. Results (output of `battery_model.py`)

| Profile | Average | Per day | 100 mAh | 150 mAh | 200 mAh | 250 mAh | Cell for 5 d | Cell for 7 d |
|---|---|---|---|---|---|---|---|---|
| Lean | 215 µA | 5.2 mAh | 15.5 d | 23.3 d | 31.1 d | 38.8 d | 32 mAh | 45 mAh |
| Typical | 404 µA | 9.7 mAh | 8.3 d | 12.4 d | 16.5 d | 20.6 d | 61 mAh | 85 mAh |
| WHOOP-like | 1227 µA | 29.4 mAh | 2.7 d | 4.1 d | 5.4 d | 6.8 d | **184 mAh** | **258 mAh** |

### Biggest loads per profile

```
Lean        IMU accel 54 %   | green LED 14 % | BLE 6 %
Typical     green LED 44 %   | IMU accel 29 % | CPU 6 %
WHOOP-like  green LED 77 %   | IMU accel 9 %  | CPU 4 %
```

---

## 4. What this means

1. **The 5–7 day target is set by the PPG settings, not by the chips.** The same hardware runs from ~3 days to ~30 days on 200 mAh depending only on LED current, pulse width, averaging and sample rate. The client's "measurement schedule" decision **is** the battery decision.
2. **HRV-grade continuous PPG (100 sps, averaged) needs a ≈ 200–260 mAh cell** for 5–7 days. That's roughly a 3.5–4 mm × 25 × 30 mm pouch, which sets the thickness of the pod.
3. **A schedule-driven design fits a ≈ 100–150 mAh cell.** That means 25–50 sps HR by day, 100 sps only during sleep (for HRV and respiration) and workouts. It's the WHOOP-quality result where it matters, with a smaller and lighter pod.
4. **Once the LEDs are tamed, the always-on accelerometer is the biggest load.** The BMI270 in accel-only mode (≈ 210 µA, **verify on the bench**) costs more than the whole SoC. Two fixes:
   - put the BMI270 in its lowest-ODR low-power mode with the step and wear features on, and verify the real current;
   - or add a BMA400-class accelerometer (single-digit µA) for always-on motion and keep the BMI270 suspended (3.5 µA) except during workouts.
5. **SoC radio and CPU are under 10 %** of every profile. This supports the TRADE_STUDY_MCU conclusion that nRF5340 vs nRF54L15 isn't a battery-life decision.

## 5. Recommended target to put to the client

> "**5 days with a 150 mAh cell** using adaptive PPG (50 sps by day, 100 sps in sleep and workouts), or **7 days with ≈ 200 mAh**. Continuous 100 sps all day needs ≈ 260 mAh for 7 days."

Then measure on the first prototype (§13 "complete battery-life measurement against the approved usage profile") and update the `(assumed)` inputs.

---

## 6. Cell requirements

| Requirement | Why |
|---|---|
| Li-ion polymer pouch, 3.7 V nominal, 4.2 V (or 4.35 V HV) charge | nPM1300 termination is settable 3.50–3.65 V and 4.00–4.45 V in 50 mV steps ([Zephyr nPM1300 charger binding](https://nrfconnectdocs.nordicsemi.com/ncs/latest/zephyr/build/dts/api/bindings/sensor/nordic,npm1300-charger.html)) |
| Built-in protection PCM (OV, UV, OC, short) | brief §4.7 "protected" |
| 10 kΩ NTC in the pack, 3rd wire | brief §4.7. The nPM1300 NTC setting accepts 10 k, 47 k or 100 k thermistors (same binding) |
| Max charge ≥ 0.5C, ideally 1C | sets dock charge time: 150 mAh at 1C = 150 mA, ≈ 1.5 h to full |
| Pulse discharge ≥ 1C for 1 s | covers the LRA + LED + radio peak (see PEAK_LOAD.md) |
| Swelling allowance 8–10 % of thickness in the housing | standard pouch practice |
| UN 38.3 test summary + IEC 62133-2 report | needed for shipping and certification (see validation/COMPLIANCE.md) |

**Sizing rule of thumb:** small pouch cells run at about 0.35–0.45 Wh per cm³ (typical for this size class, **unverified for a specific vendor**). A 150 mAh cell (0.56 Wh) therefore needs ≈ 1.3–1.6 cm³, for example 3.0 × 20 × 25 mm.

Candidate cells must come with a vendor datasheet before they go into the components list. Order from at least two suppliers, and test capacity at 0.2C and at the profile load.

## 7. Next measurements

1. PPK2 on an nRF54L15 DK + MAX86141 EVKIT: measure green LED + AFE current at each PPG setting in the table.
2. BMI270 accel-only at 12.5/25/50 Hz with the wearable features on: confirm or replace the 210 µA.
3. SSD1306 64×32 panel current for each icon set at contrast 0x40 / 0x8F / 0xFF.
4. Re-run the model with measured numbers, and fix the cell size before mechanical freeze.
