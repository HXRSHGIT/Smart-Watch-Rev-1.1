# Display Wake — Wrist Raise and Tap

Brief §4.4: "Display activation by gesture, tap or scheduled event, subject to false-wake and battery testing."

---

## 1. What the BMI270 offers

The BMI270 runs its gesture features on-chip from a **config file loaded at every boot**. Bosch ships different config files, and **only one can be loaded at a time**:

| Config | Gives | Doesn't give |
|---|---|---|
| **Base / wearable** | step counter and detector, step activity (walk/run/still), **wrist wear wake-up**, **wrist gesture**, any/no-motion | tap |
| **Legacy** | **single/double tap** | wrist gestures |

Source: [Bosch community: "BMI270 features – wrist gesture recognition and tap detection"](https://community.bosch-sensortec.com/mems-sensors-forum-jrmujtaw/post/bmi270-features---wrist-gesture-recognition-and-tap-detection-IVnrS8qPlx42iL9), [Espressif BMI270 component notes](https://components.espressif.com/components/espp/bmi270/versions/1.3.5/readme).

**Finding: the brief asks for "gesture, tap" but one BMI270 config can't do both on-chip.** Options:

1. **Base config (recommended).** Wrist-raise wake + step counting on-chip. Do **tap in firmware** from accel data, which needs a higher ODR (≥ 200 Hz bursts) whenever the band is "awake-able", and costs power. Or replace tap with "double wrist-flick", which the base config's wrist gesture already detects.
2. **Legacy config.** Tap on-chip. Wrist raise, step counting and activity then move to the nRF. That costs far more CPU and power, so not recommended.
3. **A second accelerometer** (e.g. BMA400 class, which has its own tap/step features) for always-on wake and tap, with the BMI270 suspended except in workouts. That also solves the BMI270 always-on current (power-battery BATTERY_LIFE.md §4). Costs ≈ 4 mm² of board area plus a part.

**Recommendation:**

- **P0:** base config, wrist-raise wake, no tap. Leave an unpopulated BMA400-class footprint if the area allows.
- **Prototype test:** measure the real always-on current. If BMI270 accel-only is really ≈ 200 µA, the second accelerometer pays for itself (≈ 3–5 mAh/day saved).

## 2. Wrist-raise logic

- **On-chip wrist-wear wake-up** fires when the arm rotates into "looking at the band" posture. Tune its angle thresholds for the band's mounting orientation (BMI270 axes vs wrist axes).
- **Firmware confirmation (cheap):**
  1. On the interrupt, read the gravity vector. Require the display face to be within ±35° of up (proposed).
  2. Light the display for 2–3 s.
  3. If the posture is held, extend to 5 s.
- **Suppress wake** when:
  - asleep (sleep algorithm says asleep), unless an alarm is pending;
  - in workout mode with running cadence (arm swing makes false triggers), unless the user turns it on;
  - charging.

## 3. False-wake budget

**Each false wake costs ≈ 30 µAh** (10 mA × 3 s). Even 100 false wakes/day is only ≈ 3 mAh/day. That's noticeable but not fatal. The bigger problems are user annoyance and night-time light, so **the night suppression matters more than the daytime rate**.

### Test (§13)

10 people × 1 day each, with logging firmware.

| Measure | Target (proposed) |
|---|---|
| True raises detected | ≥ 90 % |
| False wakes per hour awake | ≤ 5 |
| False wakes while asleep | 0 |
| Wake latency | ≤ 300 ms |

## 4. Scheduled and event wake

- **Reminders and alarms:** the RTC on the nRF triggers the haptic plus display. No sensor is involved.
- **Measurement results (HR/SpO2 spot check):** shown when the measurement finishes.
- **Charging:** dock detection (nPM1300 VBUS) shows the battery icon.
