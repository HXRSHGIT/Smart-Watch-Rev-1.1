# R&D — Power, Battery and Charging

Branch `rnd/power-battery`. Covers brief §4.7 and the power rows of §8 and §13.

| File | What it answers |
|---|---|
| [battery_model.py](battery_model.py) | Day-average current from every load. Run `python battery_model.py` (self-checks included) |
| [BATTERY_LIFE.md](BATTERY_LIFE.md) | Model inputs, results for 3 profiles, cell size for 5 and 7 days, cell requirements |
| [POWER_TREE.md](POWER_TREE.md) | Rails, which load goes where, the LED-supply and flash-voltage problems, display switching, ship mode |
| [PEAK_LOAD.md](PEAK_LOAD.md) | Worst-case simultaneous current, droop, scheduling rules, bench test |
| [POGO_CHARGING.md](POGO_CHARGING.md) | Reversible pads, OCVPB21, fault cases, sweat corrosion, charge settings |

## Key findings

1. **Battery life is a PPG-settings decision.** On the same hardware:
   - 25 sps lean HR → **≈ 5 mAh/day**;
   - 50 sps → **≈ 10 mAh/day**;
   - 100 sps HRV-grade all day → **≈ 29 mAh/day**.
   
   For 5 days that means a 32 / 61 / 184 mAh cell. For 7 days, 45 / 85 / 258 mAh.
2. **Suggested target to put to the client:** 5 days on ≈ 150 mAh with adaptive PPG (fast in sleep and workouts), or 7 days on ≈ 200 mAh.
3. **The PPG LED supply needs ≥ 3.1 V** and can't come from the nPM1300 bucks. Lay out a small boost with a bypass link on P0. Without the boost, heart rate stops in roughly the last 10–15 % of the charge (estimate).
4. **The brief's flash (W25Q32RV) is 3 V-only.** Swap it for the MX25R3235F so everything digital runs on one 1.8 V rail. BUCK2 then stays off.
5. **Once the LEDs are optimised, the BMI270 accel is the largest always-on load** (≈ 210 µA, to verify). A BMA400-class wake sensor is an option.
6. **Peak current is fine for the parts' ratings.** The real risk is VSYS droop at low charge and cold. Firmware scheduling rules and bulk caps are in PEAK_LOAD.md.
7. **The OCVPB21 covers reversible docking, ESD and OCP in one part.** The open question is its bridge voltage drop against the nPM1300's 4.0 V VBUS start threshold. Use a 5.0–5.2 V dock.

## Decisions for the client

- Approve the usage profile: PPG rate by day and night, SpO2 minutes per night, sync rate. This sets the cell.
- Approve the cell size, which sets pod thickness.
- Accept "HR pauses near empty", or pay for the boost.

## Next experiments

1. MAX86141 EVKIT + PPK2: LED + AFE current at each PPG setting, and green dropout vs PVLED.
2. BMI270 accel-only current at 12.5/25/50 Hz with the wearable features on.
3. Cell sample test: capacity at 0.2C and at the profile load, internal resistance at 25 °C and 0 °C.
4. OCVPB21 eval: bridge drop at 75 / 150 mA, OVP trip level.

Done by Harsh Thakur.
