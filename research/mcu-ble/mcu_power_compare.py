"""Battery-life impact of the SoC choice: nRF54L15 vs ESP32-C3, same band, same use profiles.

Reuses research/power-battery/battery_model.py and swaps only the SoC loads.
ESP32-C3 figures (3.3 V): ESP32-C3-MINI-1 datasheet v2.2 tables 6-5/6-6/6-7 and the ESP-IDF
NimBLE power_save example README (light sleep 2.3 mA on main XTAL, 140 uA with 32 kHz crystal).
BLE TX/RX are datasheet PEAK values at 100 % duty, so the ESP radio line is an upper estimate.
Run: python mcu_power_compare.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "power-battery"))
import battery_model as bm

ESP = dict(sleep_xtal32k_ua=140.0, sleep_main_xtal_ua=2300.0,
           cpu_ma=23.0,                 # modem-sleep, 160 MHz, CPU running, peripheral clocks off
           tx_ma=170.0, rx_ma=86.0)     # BLE @0 dBm TX peak, BLE RX peak
SOC_KEYS = ("SoC sleep floor", "SoC CPU (DSP, sensor FIFO)", "BLE link + sync")


def esp_loads(cpu_duty, ble_sync_s_per_h, sleep_ua):
    conn = (ESP["tx_ma"] + ESP["rx_ma"]) / 2 * 1000 * 0.002 / 1.0            # same 1 s / 2 ms link as the base model
    sync = (ESP["tx_ma"] + ESP["rx_ma"]) / 2 * 1000 * 0.5 * ble_sync_s_per_h / 3600.0
    return {"SoC sleep floor": bm.bat_ua(sleep_ua, 3.3),
            "SoC CPU (DSP, sensor FIFO)": bm.bat_ua(ESP["cpu_ma"] * 1000 * cpu_duty, 3.3),
            "BLE link + sync": bm.bat_ua(conn + sync, 3.3)}


# profile args copied from battery_model.PROFILES: (cpu_duty, ble_sync_s_per_h)
ARGS = {"Lean": (0.005, 10), "Typical": (0.01, 20), "WHOOP-like": (0.02, 30)}

rows = []
for (name, loads), (short, (duty, sync)) in zip(bm.PROFILES, ARGS.items()):
    base = sum(loads.values())
    other = base - sum(loads[k] for k in SOC_KEYS)
    nrf_soc = base - other
    for label, sleep in (("ESP32-C3 + 32 kHz xtal", ESP["sleep_xtal32k_ua"]),
                         ("ESP32-C3, no 32 kHz xtal", ESP["sleep_main_xtal_ua"])):
        esp_soc = sum(esp_loads(duty, sync, sleep).values())
        rows.append((short, label, nrf_soc, esp_soc, base, other + esp_soc))

print(f"{'Profile':11} {'ESP variant':26} {'nRF SoC':>8} {'ESP SoC':>8} {'nRF total':>10} {'ESP total':>10} "
      f"{'nRF days@150':>12} {'ESP days@150':>12} {'ESP cell for 5 d':>16}")
for short, label, n_soc, e_soc, n_tot, e_tot in rows:
    print(f"{short:11} {label:26} {n_soc:7.1f}u {e_soc:7.0f}u {n_tot:9.1f}u {e_tot:9.0f}u "
          f"{bm.life_days(150, n_tot):12.1f} {bm.life_days(150, e_tot):12.1f} "
          f"{e_tot / 1000 * 24 * 5 / bm.USABLE:13.0f} mAh")

# self-check: swapping in the nRF constants must reproduce the base model's SoC lines
n = bm.PROFILES[1][1]
assert abs(sum(n[k] for k in SOC_KEYS) - (
    bm.bat_ua(bm.SOC_SLEEP_UA * 3.0 / 1.8, 1.8)
    + bm.bat_ua(bm.SOC_CPU_MA_3V * 1000 * 0.01 * 3.0 / 1.8, 1.8)
    + bm.bat_ua(((bm.SOC_TX_MA_3V + bm.SOC_RX_MA_3V) / 2 * 1000 * (0.002 + 0.5 * 20 / 3600.0)) * 3.0 / 1.8, 1.8))) < 1e-6
print("self-check passed")
