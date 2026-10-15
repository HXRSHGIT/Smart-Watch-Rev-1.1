# R&D — Display, Dead-Front, Haptics and Wake

Branch `rnd/display-haptics`. Covers brief §2 (Stealth vs visible), §4.4 (display and reminders), §4.5 (haptics), and the display/haptic rows of §13.

| File | What it answers |
|---|---|
| [OLED_MODULE.md](OLED_MODULE.md) | The real 0.49" panel, its driver, power, no-back-power topology, alternatives |
| [DEAD_FRONT.md](DEAD_FRONT.md) | Transmission trade, how to build it, outdoor numbers, measurement plan |
| [HAPTICS.md](HAPTICS.md) | LRA choice, DRV2605L, mounting, 5 patterns, perception test |
| [WAKE_GESTURE.md](WAKE_GESTURE.md) | Wrist-raise vs tap on the BMI270, false-wake budget |

## Key findings

1. **The "0.49 inch OLED" name covers a bare COG panel (≈ 14.5 × 11.6 × 1.2 mm) and thicker hobby breakouts.** Only the bare panel fits. Its driver may be **SSD1306 or SSD1315** depending on the maker.
2. **No back-power** needs the display on its **own I²C bus with switched pull-ups**, two nPM1300 load switches (VDD, VBAT), and pins released before power-off.
3. **Stealth can't be read in direct sun.** With a 180 cd/m² panel behind a 25 % window, glare from the cover wins outdoors. An **AR coating** is the most effective fix. Recommend the visible-window variant for outdoor users.
4. **Haptics:** Ø8 mm coin LRA + DRV2605L for P0, X-axis LRA samples for comparison. Couple it to the housing, not the PCB. Use 5 rhythm-based patterns.
5. **The BMI270 can't do wrist-raise and tap at the same time** (two different config files). P0: wrist-raise only, or add a second low-power accelerometer that also cuts always-on current.

## Decisions for the client

- Is tap-to-wake required? If so: firmware tap at a power cost, or a second accelerometer.
- Accept "not readable in direct sun" for Stealth?
- Acceptable vibration noise level, since "quiet" needs a number.

## Next experiments

1. Bare-panel samples from 3 makers: current per icon, luminance, off-state leakage.
2. Window sample kit (5–8 covers): T, haze, off-state ΔE, readability panel.
3. LRA coin vs X-axis perception test with 10 people.
4. Wrist-raise false-wake logging over 10 person-days.

Done by Harsh Thakur.
