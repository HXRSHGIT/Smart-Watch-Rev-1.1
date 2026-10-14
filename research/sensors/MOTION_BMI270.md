# Motion — Bosch BMI270

Brief §4.1: "Motion data suitable for activity and sleep algorithms."
Brief §8: "Verify orientation, interrupt use, power modes and software support."

---

## 1. Verified data

| Item | Value | Source |
|---|---|---|
| Package | LGA-14, 2.5 × 3.0 × 0.8 mm | [Bosch DS](https://www.mouser.com/datasheet/2/783/BST_BMI270_FL000-1530947.pdf) |
| Current | 685 µA accel + gyro full operation · 3.5 µA suspend | Bosch |
| Accel-only low power, 25 Hz | 210 µA | datasheet excerpt via [wiki.adom.inc](https://wiki.adom.inc/adom/bmi270), **verify on the bench** |
| FIFO | 2 KB, with sensor-time frames | [Bosch DS (SparkFun copy)](https://cdn.sparkfun.com/assets/5/c/0/0/d/bst-bmi270-ds000.pdf) |
| Sensor time | 24-bit, 39.0625 µs per LSB | [Bosch community](https://community.bosch-sensortec.com/t5/MEMS-sensors-forum/BMI270-timestamp-conversion/m-p/9397) |
| On-chip features (base/wearable config) | step counter/detector, step activity, wrist gesture, wrist wear wake-up, any/no-motion | Bosch; see display-haptics WAKE_GESTURE |
| Config file | ≈ 8 KB blob uploaded over I²C/SPI at every power-up | Bosch SensorAPI |

---

## 2. Operating modes for this band

| Mode | Accel | Gyro | When | Approx. current |
|---|---|---|---|---|
| Always-on (day + night) | 25–50 Hz, low-power, ±4 g | suspend | default | ≈ 210 µA (verify) |
| Workout | 100 Hz, performance, ±8 g | 100 Hz, ±1000 dps | user or auto workout | 685 µA |
| Raw capture (engineering) | 100–200 Hz | 100–200 Hz | lab | 685 µA |
| Ship / storage | suspend | suspend | factory | 3.5 µA |

**Why the gyro stays off:** steps, activity class, sleep actigraphy and wrist-raise all work from the accelerometer alone. The gyro adds value only for:

- workout rep counting and swim strokes (P1);
- better orientation during fast motion.

## 3. The power question

At ≈ 210 µA, the always-on accelerometer is the **largest load in the lean profile and the second-largest in the typical profile** (power-battery BATTERY_LIFE.md). Options, cheapest first:

1. Measure the actual current at 12.5 Hz with the wearable features on. The on-chip features need a minimum ODR, so check what the step counter needs.
2. Add a BMA400-class ultra-low-power accelerometer (single-digit µA, with its own step counter and activity features) for always-on use. Keep the BMI270 in suspend except for workouts. Costs ≈ 4 mm² and a part.
3. Accept the current and size the cell for it.

**Recommendation:** go with option 2 as a populated-optional footprint on P0, and decide from the measurements.

## 4. Orientation and placement

- **Axes:** record the BMI270 axes against the band axes in the mechanical drawing:
  - X along the forearm (toward the hand);
  - Y across the wrist;
  - Z out of the skin.
  
  Algorithms (wrist-raise, activity, sleep posture) need this mapping. Bosch's wrist features also take a configurable orientation, so set it once.
- **Left vs right wrist:** add a setting in the app. It flips the sign of X/Y for wrist-raise.
- **Placement:** anywhere on the rigid board. **Avoid** the LRA area, because haptics saturate the accelerometer briefly; flag the samples instead. Keep it away from the flex if the band uses rigid-flex.

## 5. Interrupts and FIFO

| Pin | Use |
|---|---|
| INT1 | FIFO watermark (e.g. 1–2 s of accel data) → nRF wakes, drains the FIFO in one burst |
| INT2 | on-chip feature events: wrist wear wake-up, step-detector, no-motion |

- **FIFO with headers** includes **sensor-time frames** (39.0625 µs resolution). Use them for time alignment with the PPG (TIME_SYNC.md).
- **Bus:** the BMI270 sits on the always-on I²C bus at 400 kHz–1 MHz. Draining 1 s of 50 Hz accel (300 B) takes ≈ 3–7 ms. SPI is faster, but costs a chip-select pin and the MAX86141 is already on SPI. **I²C is fine at these rates.**

## 6. Software

- **Driver:** Bosch SensorAPI (BSD-3) and the Zephyr in-tree `bmi270` driver. The Zephyr driver focuses on the basic data path, so feature-engine use (steps, wrist gestures) needs the Bosch API or an extension. Plan ≈ 1–2 weeks of firmware.
- **Boot:** the config file must be uploaded on every boot. Measure boot time and add a retry if the upload fails (check `INTERNAL_STATUS`).

## 7. Tests

1. Current at each mode (PPK2, isolated rail).
2. Step counter: 500 steps × 10 people, walking and running, wrist and pocket-carry → error vs hand count.
3. Haptic saturation: run the LRA while logging the accel at 100 Hz, and mark the affected window length.
