# Prototype Test Plan — Brief §13 Gates

Every bullet of brief §13 is turned into a test below: what it proves, how to run it, the pass criterion, and which branch holds the detail.

- **Pass criteria marked (P)** are *proposed* by us. The brief gives no number for them, so the client approves or changes them.
- **Stage legend:**
  - **B** = bench (bare board)
  - **E** = in the enclosure
  - **W** = on the wrist (people)

---

## 1. Bring-up (do first, in this order)

| # | §13 item | Method | Pass | Stage | Detail |
|---|---|---|---|---|---|
| 1 | Repeatable SWD programming, erase and recovery | 50 program / erase / recover cycles per board on 3 boards, using both TC2030 and the pogo fixture. Then lock and recover | 100 % success; recover works with ERASEPROTECT off | B | storage-nfc-dft DFT_PROGRAMMING |
| 2 | Rail startup, shutdown, fault behaviour | Current-limited first power-up (100 mA). Scope VSYS / 1.8 V / PVLED at start-up and shutdown. Short each rail through 1 Ω, then release | No short at power-up; rails within ±3 %; monotonic rise; recovery after the fault is removed (P) | B | power-battery POWER_TREE |
| 3 | Sensor identity and communication | Factory self-test reads the ID of every IC (BMI270, BMP390, MAX30208, MAX86141, DRV2605L, nPM1300, flash JEDEC ID) | 100 % on all boards | B | DFT_PROGRAMMING §4 |

## 2. Power

| # | §13 item | Method | Pass | Stage | Detail |
|---|---|---|---|---|---|
| 4 | Sleep current | PPK2 or source-meter on VBAT: ship mode, and System ON idle with all sensors in their lowest state | Ship < 2 µA (P); idle per model ± 30 % (P) | B | power-battery BATTERY_LIFE |
| 5 | Complete battery-life measurement against the approved usage profile | 3 bands on wrists, running the approved profile from 100 % until shutdown | ≥ approved target (5 or 7 days) | W | battery_model.py profiles |
| 6 | Worst-case simultaneous load | Cell emulator with 0.5 Ω series resistance, stepped 4.2 → 3.3 V. Fire all loads at once (LED full-scale, LRA overdrive, +8 dBm TX, OLED full white, flash erase). Repeat at 0 °C with a real cell | No reset; 1.8 V in spec; PPG sample in that slot valid or flagged | B, E | PEAK_LOAD §4 |
| 7 | Pogo orientation, contact resistance, charging current and temperature | 100 docks in each orientation; series 0.5 / 1 / 2 Ω; 9 V and 12 V applied; pads shorted while worn; thermal camera during charge | Charge starts every time within 1 s; no stop-start loop; OVP holds; no cell current through the pads; hottest point < 45 °C at 25 °C ambient (P) | B, E | POGO_CHARGING §6 |
| 8 | Battery NTC, protection and charge termination | Heat and cool the NTC (thermal chamber 0–50 °C); log charge current and voltage; trigger the PCM over-current trip with an electronic load | JEITA steps as configured; termination at the set voltage ± 1 % (P); PCM trips | B | POGO_CHARGING §5 |

## 3. Radio

| # | §13 item | Method | Pass | Stage | Detail |
|---|---|---|---|---|---|
| 9 | Antenna tuning in the final worn enclosure | VNA: free space → housing → on a wrist; retune the π network | S11 ≤ −10 dB across 2400–2483.5 MHz on the wrist | E, W | mcu-ble ANTENNA_RF §4 |
| 10 | BLE range and connection reliability | 3 phones (iOS + Android). Band on a wrist at 1 / 5 / 10 m, body between band and phone, 4 orientations, 1 h each | No disconnects at 5 m with the body in the way; sync completes at 10 m line-of-sight (P) | W | ANTENNA_RF §5 |
| 11 | Pairing and firmware update security | Passkey pairing; bond-loss recovery; signed vs unsigned image; downgrade attempt; 10 power pulls during an update | All behaviours as specified; always boots a valid image | B | mcu-ble BLE_SECURITY_DFU §5 |

## 4. Sensing

| # | §13 item | Method | Pass | Stage | Detail |
|---|---|---|---|---|---|
| 12 | Synchronised data capture | Tap-correlation between accel and PPG, at the start and end of an 8 h log, at 15 °C and 35 °C | Lag within ±1 sample; no growing drift | B, W | sensors TIME_SYNC §4 |
| 13 | HR and PPG waveform quality at rest and in motion | ECG chest-strap reference; rest, sleep, walk, run, cycle, gym; 20 people across Monk skin-tone groups | MAE ≤ 2 bpm rest/sleep, ≤ 5 walk/cycle, ≤ 8 run (P); report % of time with valid HR | W | optical-ppg HR_MOTION_ARTIFACT §4 |
| 14 | SpO2 against an appropriate reference | Stage B (room-air spot checks against a cleared finger oximeter, 20–30 people, all Monk groups) and Stage C (overnight); record Monk + ITA | Bias and spread reported per skin-tone group; no group materially worse (P) | W | optical-ppg SPO2 §5 |
| 15 | Optical crosstalk, ambient light, fit and skin contact | Black-target crosstalk; 0 / 500 / 10 k / ≈ 50 k lux; 3 strap tensions × wrist sizes | Crosstalk DC < 5–10 % of on-wrist DC (P); no ADC saturation in sun; define "normal fit" | E, W | optical-ppg OPTICAL_DESIGN §5 |
| 16 | Temperature response and separation from internal heat | Hot-plate step response; internal worst-case load on the plate; ambient sweep 18 → 28 °C; 10 people × 5 nights against a reference thermistor | Internal-load offset < 0.1–0.2 °C (P); time constants reported | E, W | sensors SKIN_TEMP §5 |
| 17 | Pressure-vent response and environmental robustness | −36 Pa step in a chamber; stairs and lift trials; immersion; sweat + sunscreen | 90 % response < 5 s (P); response unchanged after water and contamination | E, W | sensors PRESSURE §5 |

## 5. Display and haptics

| # | §13 item | Method | Pass | Stage | Detail |
|---|---|---|---|---|---|
| 18 | Display readability, dead-front behaviour, sleep current, power-off leakage | Window sample kit (T, haze, ΔE off-state, luminance at 0° and 45°); reading panel at 500 / 10 k lux / sun; OLED rail current when off | Off-state ΔE ≤ 1–2 (P); readable indoors through Stealth; < 0.1 µA leakage when off (P) | B, E, W | display-haptics DEAD_FRONT §5, OLED_MODULE §3 |
| 19 | Haptic strength, noise, peak current, mounting durability | 10-person recognition test; A-weighted noise at 30 cm; scope LRA current; 10,000 events + drop test | ≥ 90 % pattern recognition (P); noise below the client's limit; mount intact | E, W | HAPTICS §4 |

## 6. Conditional

| # | §13 item | Note |
|---|---|---|
| 20 | NFC range and power | **Only if active NFC is kept.** Recommendation is to drop it (storage-nfc-dft NFC_ACTIVE) |

## 7. Robustness and pre-compliance

| # | §13 item | Method | Pass | Stage |
|---|---|---|---|---|
| 21 | ESD | IEC 61000-4-2: ±8 kV contact / ±15 kV air on housing, pogo pads, window | No damage; self-recovers (criterion B) | E |
| 22 | EMC pre-compliance | Radiated emissions pre-scan at a lab (FCC Part 15 / EN 55032-class limits); RF conducted tests per EN 300 328 | Margin ≥ 6 dB to the limits (P) | E |
| 23 | Thermal | 40 °C ambient, worst-case use profile; charging at 35 °C ambient | Skin-contact surface ≤ 43 °C for prolonged contact (P, align with IEC 62368-1 touch-temperature limits) | E |
| 24 | Sweat and corrosion | Artificial sweat (ISO 3160-2 / EN 1811 style) on pogo pads, vent, windows; 50 cycles + humidity 85 °C / 85 % RH, 168 h (P) | No functional loss; contact resistance rise < 50 % (P) | E |
| 25 | Water resistance | Per the client's target: IPX7 (1 m, 30 min) or ISO 22810 / 5 ATM | No ingress; sensors work after drying | E |

## 8. Order and timing (rough)

| Weeks | Work |
|---|---|
| 1–2 | Tests 1–4 (bring-up and sleep current) |
| 2–4 | Tests 6–8, 9, 11, 12 |
| 3–6 | Tests 13–19 (people studies) and 21–22 at the lab |
| 4–8 | Tests 5, 23–25 |
| 8 | Review against brief §14 success criteria → Rev C list |

Output of every test: a short report with raw data, kept in this repository under `validation/results/<test#>/`.
