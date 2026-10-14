# Haptics — LRA, Driver, Mounting, Patterns

Brief §4.5:
- "Quiet, clearly perceptible wrist vibration."
- "Exact LRA should be selected using enclosure space, resonance, impedance, peak current and mechanical mounting."
- "Multiple recognizable vibration patterns for reminders, goal completion, alarms and error/status feedback."

---

## 1. Actuator candidates

| Part | Type | Size | Rated | f₀ | Current | Acceleration | Source |
|---|---|---|---|---|---|---|---|
| Precision Microdrives C08-005 | Z-axis coin LRA | Ø8 mm | 1.8 V rms | 235 Hz | 75 mA typ | 1.28 G typ | [PMD](https://www.precisionmicrodrives.com/?p=12426) |
| Vybronics VG0832012 | Z-axis coin LRA | Ø8 × 3.2 mm | 1.8 V AC | 235 Hz | 102 mA max | ≥ 0.61 G | [DigiKey](https://www.digikey.es/en/products/detail/vybronics-inc/VG0832012/7364317) |
| Vybronics VG0832013D | Z-axis coin LRA | Ø8 × 3.2 mm | 1.8 V AC | 235 Hz | (DS) | (DS) | [DigiKey](https://www.digikey.cn/en/products/detail/vybronics-inc/VG0832013D/9974290) |
| X-axis rectangular LRA (wearable class) | X/Y-axis | ≈ 10–12 × 3–4 × 2.5–3 mm class | ≈ 1.8–2 V rms | ≈ 150–200 Hz | ≈ 80–150 mA | stronger feel per volume | ask AAC / Jahwa / Vybronics for current parts (**unverified** class figures) |

### Z-axis or X-axis on a band?

- **Z-axis coin:** moves perpendicular to the skin, which the skin feels as pressure taps. Easy to place and cheap. It "buzzes" against the wrist bone, and a loose strap kills the effect.
- **X-axis linear:** moves along the arm. Feels stronger and "cleaner" for the same energy in wrist products (common choice in premium watches). Longer, and needs to be aligned with the band axis.

**Recommendation:** fit a Ø8 mm coin LRA on P0 (available, cheap, DRV2605L-ready). Get X-axis samples for a side-by-side perception test before Rev C.

**Thickness:** the 3.2 mm coin is likely the thickest part after the battery. Check the stack-up (validation MECHANICAL_STACKUP.md).

## 2. Driver: TI DRV2605L

From the [TI datasheet](https://www.ti.com/lit/ds/symlink/drv2605l.pdf):

- **Supply and package:** 2.0–5.2 V supply, run from VSYS. DSBGA-9 ≈ 1.5 × 1.5 mm.
- **Closed loop:** closed-loop LRA drive with **auto-resonance tracking**, which follows f₀ as it drifts with temperature and mounting.
- **Overdrive and active braking:** sharp start and stop. This makes short taps distinct, which matters for "recognisable patterns".
- **Effects library:** licensed effect ROM (includes an LRA library) plus a sequencer, so patterns are a few I²C writes.
- **Auto-calibration:** run once in production per unit; store the results (compensation, back-EMF, feedback) in the nRF settings.
- **Current:** quiescent 0.5 mA active, 4 µA shutdown (EN low).

Alternatives:

- **DRV2604L:** same family, RAM for custom waveforms instead of ROM.
- **DRV2625:** newer, adds waveform sequencer/RAM and diagnostics.

Check both datasheets before freeze. Keep the DRV2605L unless the licensed ROM is a concern.

**Supply gating:** 4 µA shutdown is ≈ 1 % of the typical battery budget. Feeding the DRV2605L from a GPIO-switched load switch removes it, at the cost of one more switch.

## 3. Mounting

- **Couple the LRA to the housing on the skin side**, not to the PCB. The PCB is stiff and spreads energy into the whole pod and the battery, so you get noise instead of a feel.
- **Use double-sided foam or PSA** of the LRA vendor's recommended thickness. Glue that's too stiff transmits buzz; foam that's too soft absorbs the effect.
- **Keep it ≥ 5 mm from the PPG optics** if possible, and flag PPG samples taken during haptics (power-battery PEAK_LOAD.md §3). Vibration corrupts PPG mechanically as well as electrically.
- **Mount on the antenna side?** Avoid: the LRA is metal. Keep it out of the antenna clearance (mcu-ble ANTENNA_RF.md).

## 4. Patterns

Design rules:

- Use **rhythm and count**, not intensity, to tell patterns apart. People can't reliably tell amplitude steps apart on the wrist, but they do recognise rhythm.
- Each pattern should be ≤ 1.5 s.
- Keep it to **4–5 patterns** in total.

| Event (brief) | Pattern | Total |
|---|---|---|
| Reminder (water, medicine, study…) | 2 short taps (60 ms, gap 120 ms) | ≈ 0.25 s |
| Goal completed | rising "ta-ta-taaa" (60 / 60 / 250 ms) | ≈ 0.6 s |
| Alarm (wake) | 3 × (400 ms on, 300 ms off), repeat every 10 s up to 1 min | escalating |
| Error / attention (low battery, sync fail) | 1 long buzz (600 ms) | 0.6 s |
| Confirmation (tap / pairing accepted) | 1 crisp tap (30 ms + brake) | 0.05 s |

**Perception test:** 10 people, band worn normally, 5 patterns played at random times. Measure:

- recognition accuracy (target ≥ 90 %, proposed);
- "noticed?" (target 100 % at rest, ≥ 80 % while walking);
- audible noise in a quiet room (A-weighted dB at 30 cm; agree the limit with the client, because the brief asks for "quiet").

## 5. Power

- **Energy per event:** 90 mA × 0.6 s ≈ 15 µAh per event at the cell. At 20 events/day that's ≈ 13 µA average (power-battery model).
- **Peak:** ≈ 100–140 mA with overdrive. This is the largest single peak after a full-scale LED pulse, so schedule it (PEAK_LOAD.md).
