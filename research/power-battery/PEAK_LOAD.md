# Worst-Case Concurrent Load

Brief §4.7: "Power modes must coordinate radio, flash writes, haptics, display, optical pulses and NFC so combined peaks remain within the cell, protection and regulator limits."
Brief §13: "Worst-case simultaneous load testing."

---

## 1. Peak contributors (from VSYS / cell)

| Load | Peak at the cell | Duration | Source / basis |
|---|---|---|---|
| PPG LED pulse (one LED) | up to 124 mA full-scale per driver; planned 20–60 mA | 15–117 µs per pulse | MAX86141 LED ranges 31–124 mA ([ADI](https://www.farnell.com/datasheets/2580845.pdf)) |
| PPG LED pulses for SpO2 (red / IR, sequential) | ≈ 20–40 mA | ≈ 117 µs each | same |
| LRA drive (8 mm coin) | 75 mA typ, 102 mA max | 0.1–1 s | [PMD C08-005](https://www.precisionmicrodrives.com/?p=12426), [Vybronics VG0832012](https://www.digikey.es/en/products/detail/vybronics-inc/VG0832012/7364317) |
| LRA start-up overdrive (DRV2605L) | ≈ 1.3–1.5× the rated current for the first cycles (estimate) | ≈ 10–20 ms | DRV2605L overdrive behaviour, value to measure |
| BLE TX at +8 dBm (nRF54L15) | ≈ 10–15 mA at the cell (estimate) | ≈ 0.1–2 ms | 4.8 mA at 0 dBm from Nordic; +8 dBm figure to verify |
| CPU | ≈ 2.5 mA at the cell (from 2.6 mA @ 3 V) | continuous while awake | derived |
| OLED, bright full-screen flash | ≈ 15–25 mA (estimate) | seconds | measure on the selected panel |
| Flash program/erase | ≈ 5–10 mA at the cell (estimate) | ms per page, tens of ms per sector | verify in the MX25R datasheet |
| Active NFC (if kept) | up to ≈ 400 mA at 1.6 W RF out, 4 V | ms bursts | derived from ST's 1.6 W headline. **Reason to drop it** |

### Worst-case sum (without NFC)

124 (LED full-scale) + 140 (LRA overdrive) + 15 (radio) + 3 (CPU) + 25 (OLED) + 10 (flash) ≈ **≈ 320 mA**.

### Realistic coordinated peak

40 (LED) + 100 (LRA) + 15 + 3 + 15 + 10 ≈ **≈ 185 mA**.

---

## 2. Limits that matter

| Element | Limit | Margin vs ≈ 185 mA |
|---|---|---|
| Cell, 150 mAh @ 1C continuous / 2C pulse (typical small pouch, **check the cell DS**) | 150 mA / 300 mA | ✓ pulse, ✗ continuous. Fine, because the peaks are short |
| Cell PCM over-current trip | usually ≥ 1 A for small packs (check the DS) | ✓ |
| nPM1300 BUCK1 | 200 mA | ✓. Buck loads are only ≈ 25 mA |
| nPM1300 load switches | 100 mA each | ✓. OLED < 25 mA |
| **VSYS droop** = I × (R_cell + R_PCM + R_traces) | small pouch R ≈ 0.2–0.5 Ω (typical, cold → higher) | 185 mA × 0.5 Ω ≈ **90 mV dip** |

**The real limit is droop at low charge and low temperature, not a part's rating.** A 90 mV dip on a 3.5 V cell at 5 °C pushes PVLED under the green LED headroom (POWER_TREE §3.1). That corrupts a PPG sample, or browns out the SoC if the dip reaches its BOR.

---

## 3. Rules (firmware + hardware)

1. **No LRA during a PPG exposure.** The MAX86141's exposure timing is known (sample clock). Either start the LRA right after a FIFO interrupt and accept a few corrupted samples flagged by a "haptic active" bit, or gate the AFE off for the haptic burst. The LRA vibration also shakes the optics, so those samples are corrupted mechanically anyway; flag them.
2. **No flash erase during an LRA burst or a radio sync burst.** Queue flash writes in RAM (a few KB) and flush when idle.
3. **Radio:** BLE timing belongs to the controller. Schedule bulk sync and DFU only when VBAT > 3.6 V or the band is charging.
4. **DFU** only when VBAT > 30 % or on the dock (also in BLE_SECURITY_DFU).
5. **Bulk capacitance:**
   - ≥ 22 µF X5R on VSYS next to PVLED and the DRV2605L (0603/0402 with DC-bias derating; 22 µF nominal ≈ 10 µF effective at 4 V);
   - 10 µF near the SoC on 1.8 V;
   - follow the nPM1300 reference values for its own input and output caps.
6. **Brown-out policy:** nPM1300 VSYS and battery-low warnings (VBAT monitor) step the band down in stages:

| VBAT | Mode | What's on |
|---|---|---|
| > 3.6 V | Normal | everything |
| 3.6–3.4 V | Reduced | max 1 haptic pattern at a time; display brightness down |
| 3.4–3.3 V | Critical | PPG off (or boost only); radio sync only; "charge" icon |
| < 3.3 V | Ship | data saved, ship mode |

---

## 4. Bench test (§13 "worst-case simultaneous load")

1. Power the band from a source-meter **emulating the cell**, with the series resistance set to 0.5 Ω and VBAT stepped 4.2 → 3.3 V.
2. Run a test firmware that fires LED full-scale, LRA overdrive, BLE TX +8 dBm, an OLED full white frame and a flash sector erase **at the same instant**.
3. Scope VSYS, PVLED, 1.8 V and nRESET. Pass criteria:
   - no reset;
   - 1.8 V stays in spec;
   - the PPG sample in that slot is either valid or flagged.
4. Repeat at 0 °C with a real cell.
