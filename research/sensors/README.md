# R&D — Motion, Pressure, Skin Temperature, Time Sync

Branch `rnd/sensors`. Covers the sensing rows of brief §4.1, the BMI270/BMP390/MAX30208 rows of §8, and their §13 tests.

| File | What it answers |
|---|---|
| [MOTION_BMI270.md](MOTION_BMI270.md) | Modes, the always-on current problem, orientation, interrupts/FIFO, software |
| [PRESSURE_BMP390.md](PRESSURE_BMP390.md) | Signal size vs artifacts, floors algorithm, ePTFE vent vs gel sensor, tests |
| [SKIN_TEMP_MAX30208.md](SKIN_TEMP_MAX30208.md) | Contact sensor thermal path, heat sources, dual-sensor compensation, trend vs core, tests |
| [TIME_SYNC.md](TIME_SYNC.md) | Clock bases, hardware timestamping, rate estimation, resampling, validation |

## Key findings

1. **BMI270 accel-only (≈ 210 µA, verify) is a top-2 always-on load.** Keep the gyro off outside workouts. Consider a BMA400-class wake accelerometer as a populated-optional footprint.
2. **Floors:** one floor ≈ 36 Pa, well above sensor resolution. The problems are arm motion (± 8 Pa) and weather drift, so count height only during step bouts.
3. **Vent:** Gore wearable vents (PE15/PE17 class, ISO 22810 50–100 m ratings) on a side face for P0. Evaluate the gel-filled ST LPS27HHW as the swim-proof alternative.
4. **The MAX30208 is a contact sensor, ±0.1 °C at the chip.** Product accuracy comes from the mechanics: metal skin pad, isolated island or flex tail, low thermal mass, and a second board-side reading for compensation.
5. **Temperature is shown as a nightly deviation from baseline,** never as body temperature.
6. **Time sync:** hardware-capture the FIFO interrupts on the RTC, estimate each sensor's real rate continuously, and resample to a common grid. Validate with a tap cross-correlation.

## Decisions for the client

- Water-resistance target. It decides the vent technology.
- Is a second accelerometer acceptable on the BOM, if it buys ≈ 3–5 mAh/day?

## Next experiments

1. BMI270 current at 12.5/25/50 Hz with features on.
2. Pressure chamber step response with the vent stack.
3. Skin-temp hot-plate rig: step response and internal-heat offset.
4. Tap cross-correlation alignment test on the first board.

Done by Harsh Thakur.
