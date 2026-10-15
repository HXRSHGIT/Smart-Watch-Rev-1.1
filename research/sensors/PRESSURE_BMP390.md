# Pressure — Floors, Relative Altitude, Venting

Brief §4.1: "Pressure data suitable for relative altitude, floors climbed and environmental compensation."
Brief §4.2: "Floors climbed and relative elevation change."
Brief §8, BMP390: "Provide a waterproof breathable vent and contamination protection."

---

## 1. Signal size

| Quantity | Value |
|---|---|
| Pressure change near sea level | ≈ 12 Pa per metre (≈ 0.12 hPa/m) |
| One floor (≈ 3 m) | ≈ 36 Pa |
| Arm raised / lowered (≈ ±0.7 m wrist travel) | ≈ ±8 Pa. **Artifact** |
| Weather change, normal day | ≈ 1–3 hPa over hours (100–300 Pa) |
| Weather front / storm | can exceed 1 hPa/hour (≈ 8 m/hour of fake climb) |
| Car or room ventilation, doors | step changes of a few Pa |
| BMP390 relative accuracy | ±3 Pa (±0.03 hPa) ≈ ±25 cm, 700–1100 hPa, 25–40 °C ([Bosch DS](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp390-ds002.pdf)) |

**Conclusion:** the sensor can resolve a floor easily. The real problems are:

- **arm motion**, which is the same size as a quarter of a floor;
- **weather drift**, which is the same size as many floors over a day.

## 2. Floor algorithm (fuse with steps)

1. Sample at 1 Hz with ×8–16 oversampling and the IIR filter on; run a ≈ 10 s moving filter.
2. **Count height only while the IMU says the user is walking** (step cadence present). Climbing without steps (lift, car) isn't a floor.
3. A floor = ≥ 3 m net rise (≈ 36 Pa) within a walking bout, at a plausible climb rate (stairs ≈ 0.2–0.5 m/s, estimate). This rejects weather drift, which is slow and has no steps, and arm motion, which is fast and reverses.
4. **Elevation gain for workouts:** same idea, with the phone GPS altitude (brief P1) as a long-term anchor when available.

**Expected behaviour:** good on stairs, misses slow ramps, and correctly ignores lifts. That's the usual wearable floor behaviour. State it in the help text.

## 3. Vent — the hardware problem

The BMP390 measures through a hole in its metal lid. The band must be **water-resistant** (target from validation COMPLIANCE.md), but the sensor needs **air pressure**.

### Option A — ePTFE vent membrane over a housing port

| Gore pressure-vent family | Rating (per Gore) |
|---|---|
| PE12, PE13 | IP68 (1.5 m, 30 min) |
| PE7 | IP68 (2 m, 1 h) |
| PE15, PE17 (wearable-oriented) | ISO 22810: 50 m for 10 min / 100 m for 15 min |

Source: [Gore pressure vents datasheet (Aug 2024)](https://www.gore.com/system/files/2024-08/GORE-Pressure-Vents-Datasheet-US-AUG24.pdf), [product page](https://www.gore.com/products/gore-pressure-vents).

- **Build:** port Ø 0.8–1.5 mm in the housing, vent adhesive-mounted inside, small sealed chamber from vent to sensor (gasket or foam ring around the BMP390).
- **Response:** the chamber volume + membrane resistance sets a time constant. Keep the chamber **small** (< 20 mm³, estimate) so floors register within seconds.
- **Contamination:** sweat salts, sunscreen and soap can clog the membrane. Recess the port, add a protective mesh/grille, and put it on a **side face**, not the skin face.

### Option B — gel-filled water-resistant sensor

- **ST LPS27HHW:** potting gel + metal cap, 260–1260 hPa, down to 4 µA, ceramic LGA-10 with a cylindrical port ([ST](https://www.st.com/content/st_com/en/products/mems-and-sensors/pressure-sensors/lps27hhw.html), [datasheet](https://cdn.sparkfun.com/assets/c/9/7/6/2/LPS27HHW_datasheet.pdf)).
- **Build:** the sensor port goes through an O-ring to the outside. The gel itself is the water barrier, so no membrane is needed.
- **Pros:** no clogging membrane; designed for water-resistant watches.
- **Cons:** taller package, O-ring seal design, gel ages.

**Recommendation:**

- **P0:** BMP390 + a Gore wearable vent (PE15/PE17 class) on a side face, because the brief names the BMP390.
- **Before Rev C:** compare against the LPS27HHW with an O-ring port. If the target water rating is high (swimming), the gel route is usually more robust.

## 4. Temperature effects

- The BMP390 compensates internally, but a **fast** temperature change (band put on a warm wrist, shower) causes transient pressure error while the die settles.
- **Firmware:** ignore floor counting for ≈ 1–2 min after a large BMP390 temperature step. Its own temperature output is good enough to detect this.
- **Keep the BMP390 away from** the charger, the bucks and the PPG LEDs.

## 5. Tests (§13 "Pressure-vent response and environmental robustness")

1. **Step response:** put the band in a small pressure chamber and apply a −36 Pa step (≈ +3 m). Time to 90 % < 5 s (proposed).
2. **Stairs:** 10 people × 10 flights up and down, plus lift rides → floors counted vs truth.
3. **Water:** IPX7/IPX8 or ISO 22810 immersion per the target. After drying, re-run test 1; the response must be unchanged.
4. **Contamination:** artificial sweat + sunscreen applied to the port, 50 cycles. Re-run test 1.
