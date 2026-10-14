#!/usr/bin/env python3
"""HealthOS Band battery-life model (stdlib only).

Every load is reduced to an average current drawn from the cell.
Loads on a buck rail are converted through power: I_bat = I * V / (V_bat * eta).
Loads fed straight from VBAT (PPG LED driver, LRA driver) count 1:1.

Run:  python battery_model.py
Numbers marked (assumed) need a bench measurement before they are trusted.
"""

V_BAT = 3.7        # nominal cell voltage
ETA_BUCK = 0.88    # nPM1300 buck efficiency at light load (assumed)
USABLE = 0.80      # capacity left after cut-off, temperature and ageing margin (assumed)
SEC_PER_DAY = 86400.0


def bat_ua(current_ua, rail_v=None):
    """Average cell current for a load. rail_v=None means fed from VBAT directly."""
    if rail_v is None:
        return current_ua
    return current_ua * rail_v / (V_BAT * ETA_BUCK)


def duty(seconds_per_day):
    return seconds_per_day / SEC_PER_DAY


def ppg_led_ua(led_ma, pulse_us, pulses_per_sample, sps, hours=24.0):
    """Average LED current: pulse current x on-time fraction x hours active."""
    on_fraction = pulse_us * 1e-6 * pulses_per_sample * sps
    return led_ma * 1000.0 * on_fraction * hours / 24.0


# ---------------------------------------------------------------------------
# Datasheet inputs (sources in BATTERY_LIFE.md)
# ---------------------------------------------------------------------------
SOC_SLEEP_UA = 2.0          # nRF54L15 0.7-2.9 uA @3 V (product page); 5340: 1.6-2.3 uA
SOC_CPU_MA_3V = 2.6         # derived: 193 CoreMark/mA @3 V, ~500 CoreMark @128 MHz (assumed)
SOC_TX_MA_3V = 4.8          # nRF54L15 TX 0 dBm @3 V
SOC_RX_MA_3V = 3.4          # nRF54L15 RX @3 V
AFE_UA_25SPS = 10.0         # MAX86141 < 10 uA at 25 sps (1.8 V)
AFE_SHDN_UA = 1.6           # MAX86141 shutdown
IMU_ACC_LP_UA = 210.0       # BMI270 accel-only low-power 25 Hz (secondary source, verify)
IMU_FULL_UA = 685.0         # BMI270 accel + gyro
IMU_SUSPEND_UA = 3.5
BARO_1HZ_UA = 3.2           # BMP390 @1 Hz
TEMP_STBY_UA = 0.5          # MAX30208 standby
TEMP_CONV_UA = 67.0         # MAX30208 during conversion
TEMP_CONV_S = 0.015         # conversion time (assumed)
FLASH_DPD_UA = 0.35         # MX25R3235F deep power-down max
HAPTIC_SHDN_UA = 4.0        # DRV2605L shutdown (EN low), 0 if its supply is load-switched
PMIC_IQ_UA = 3.0            # nPM1300 bucks + monitoring, light load (assumed)
PCM_UA = 3.0                # cell protection IC quiescent (assumed, typical DW01-class)
OLED_ON_MA = 10.0           # SSD1306 64x32, ~25 % pixels lit, from VBAT (assumed)
LRA_MA = 90.0               # 8 mm coin LRA drive, between 75 typ and 102 max


def profile(name, ppg, spo2_min_per_night, gyro_h, ble_sync_s_per_h,
            display_wakes, haptic_events, cpu_duty):
    """Return {load: average cell uA} for one day of use."""
    led_ma, pulse_us, pulses, sps = ppg
    loads = {}

    # PPG: green LED for HR, all day. LED driver runs from VBAT (PVLED >= 3.1 V).
    loads["PPG green LED"] = ppg_led_ua(led_ma, pulse_us, pulses, sps)
    afe_ua = AFE_UA_25SPS * sps / 25.0          # assume AFE current scales with sample rate
    loads["PPG AFE (MAX86141)"] = bat_ua(afe_ua, 1.8)

    # SpO2: red + IR, 100 sps, short windows during sleep.
    spo2_h = spo2_min_per_night / 60.0
    loads["SpO2 red + IR LEDs"] = 2 * ppg_led_ua(20.0, 117.3, 1, 100, hours=spo2_h)

    # Motion: accel always on, gyro only during workouts.
    loads["IMU accel (always on)"] = bat_ua(IMU_ACC_LP_UA, 1.8)
    loads["IMU gyro (workouts)"] = bat_ua((IMU_FULL_UA - IMU_ACC_LP_UA) * gyro_h / 24.0, 1.8)

    loads["Pressure (BMP390 1 Hz)"] = bat_ua(BARO_1HZ_UA, 1.8)
    loads["Skin temp (1/min)"] = bat_ua(TEMP_STBY_UA + TEMP_CONV_UA * duty(1440 * TEMP_CONV_S), 1.8)

    # SoC: sleep floor + CPU work + radio.
    loads["SoC sleep floor"] = bat_ua(SOC_SLEEP_UA * 3.0 / 1.8, 1.8)
    loads["SoC CPU (DSP, sensor FIFO)"] = bat_ua(SOC_CPU_MA_3V * 1000 * cpu_duty * 3.0 / 1.8, 1.8)
    conn_ua = (SOC_TX_MA_3V + SOC_RX_MA_3V) / 2 * 1000 * 0.002 / 1.0   # 1 s interval, 2 ms radio
    sync_ua = (SOC_TX_MA_3V + SOC_RX_MA_3V) / 2 * 1000 * 0.5 * ble_sync_s_per_h / 3600.0
    loads["BLE link + sync"] = bat_ua((conn_ua + sync_ua) * 3.0 / 1.8, 1.8)

    # Display (from VBAT via the panel's own charge pump), haptics (VBAT).
    loads["OLED wakes (3 s each)"] = OLED_ON_MA * 1000 * duty(display_wakes * 3.0)
    loads["Haptic events (0.6 s each)"] = LRA_MA * 1000 * duty(haptic_events * 0.6)

    # Always-on overheads.
    loads["Flash deep power-down"] = bat_ua(FLASH_DPD_UA, 1.8)
    loads["Haptic driver shutdown"] = HAPTIC_SHDN_UA
    loads["PMIC + cell protection"] = PMIC_IQ_UA + PCM_UA
    loads["AFE shutdown between"] = 0.0 if sps > 0 else AFE_SHDN_UA
    return name, loads


PROFILES = [
    # name, PPG (mA, pulse us, pulses/sample, sps), SpO2 min/night, gyro h/day,
    # BLE sync s/hour, display wakes/day, haptic events/day, CPU duty
    profile("Lean: 25 sps HR, light use", (20, 58.7, 1, 25), 24, 0.5, 10, 15, 10, 0.005),
    profile("Typical: 50 sps HR, 1 h workout", (30, 117.3, 1, 50), 48, 1.0, 20, 25, 15, 0.01),
    profile("WHOOP-like: 100 sps continuous (HRV grade)", (40, 117.3, 2, 100), 96, 1.0, 30, 30, 20, 0.02),
]


def life_days(capacity_mah, avg_ua):
    return capacity_mah * USABLE / (avg_ua / 1000.0) / 24.0


def self_check():
    _, base = profile("check", (20, 58.7, 1, 25), 0, 0, 0, 0, 0, 0)
    # LED duty maths: 20 mA x 58.7 us x 25 sps = 29.35 uA
    assert abs(base["PPG green LED"] - 29.35) < 0.01
    # doubling capacity doubles life
    assert abs(life_days(200, 500) / life_days(100, 500) - 2.0) < 1e-9
    # a VBAT load is not scaled, a 1.8 V buck load is scaled down
    assert bat_ua(100) == 100 and bat_ua(100, 1.8) < 100
    # more PPG duty must cost more
    _, hi = profile("check", (40, 117.3, 2, 100), 0, 0, 0, 0, 0, 0)
    assert hi["PPG green LED"] > 30 * base["PPG green LED"]


if __name__ == "__main__":
    self_check()
    caps = [100, 150, 200, 250, 300]
    for name, loads in PROFILES:
        total = sum(loads.values())
        print(f"\n=== {name} ===")
        for k, v in sorted(loads.items(), key=lambda kv: -kv[1]):
            if v >= 0.05:
                print(f"  {k:32s} {v:8.1f} uA  {100 * v / total:5.1f} %")
        print(f"  {'TOTAL':32s} {total:8.1f} uA  = {total * 24 / 1000:.1f} mAh/day")
        print("  Life (days): " + "  ".join(f"{c} mAh: {life_days(c, total):4.1f}" for c in caps))
        for target in (5, 7):
            need = total / 1000 * 24 * target / USABLE
            print(f"  Cell needed for {target} days: {need:.0f} mAh")
    print("\nself-check passed")
