# External Flash — Sizing, Part, Filesystem

Brief §4.6: "External nonvolatile storage for offline sensor summaries and engineering data when the phone is absent."
Brief §8, W25Q32RVXHJQ: "Verify package assembly, firmware support, deep-sleep current and data-retention needs."

---

## 1. Part choice

| | Winbond W25Q32RVXHJQ (brief) | Macronix MX25R3235F | Macronix MX25R6435F |
|---|---|---|---|
| Size | 32 Mbit (4 MB) | 32 Mbit (4 MB) | 64 Mbit (8 MB) |
| VCC | **2.7–3.6 V** | **1.65–3.6 V** | 1.65–3.6 V |
| Package | XSON-8 2 × 3 mm | USON 2 × 3, WLCSP | USON, WSON, WLCSP |
| Deep power-down | ≈ 1 µA class (verify) | 0.35 µA max | family "7 nA" headline |
| Max clock | 133 MHz | 80 MHz (quad) | 80 MHz |
| Source | [DigiKey](https://www.digikey.com/es/products/detail/winbond-electronics/W25Q32RVXHJQ-TR/22146347) | [Mouser MX25R](https://www.mouser.in/new/macronix/macronix-mx25r-nor-flash/) | [Mouser MX25R](https://www.mouser.in/new/macronix/macronix-mx25r-nor-flash/) |

**Use the MX25R family.** The digital domain is 1.8 V (MAX86141 VDD is 1.8 V), and the W25Q32RV can't run at 1.8 V. The MX25R also has lower standby current and comes in the same 2 × 3 mm outline, so the 32 and 64 Mbit parts can share a footprint (check the pinout per package).

The MX25R is the flash Nordic itself uses on its development kits, so Zephyr's `jedec,spi-nor` driver supports it with no custom work.

---

## 2. How much data per day

### 2.1 Consumer summaries (always logged)

| Record | Rate | Size | Per day |
|---|---|---|---|
| Minute summary: HR, steps, activity class, intensity, floors Δ, skin temp, flags | 1/min | ≈ 12 B | 17 KB |
| Sleep epoch (state, motion, HR) | 1/30 s during sleep, 8 h | 4 B | 4 KB |
| Beat-to-beat intervals (night HRV), P1-ready | ≈ 60 bpm × 8 h | 2 B | 58 KB |
| SpO2 window results | 1 per 10 min at night | 8 B | < 1 KB |
| Events (reminders, wake, charge, errors) | ≈ 200 | 8 B | 2 KB |
| **Total** | | | **≈ 80 KB/day** |

A **3 MB log partition** therefore holds **≈ 37 days** offline. The brief's "phone absent" case is easily covered, even with the 4 MB part.

### 2.2 Raw engineering data (§4.1 "raw or minimally processed sensor data access")

| Stream | Rate | B/s |
|---|---|---|
| PPG green, 2 photodiodes, 24-bit packed | 100 sps | 600 |
| Accel 16-bit × 3 | 100 Hz | 600 |
| Gyro (workouts) | 100 Hz | 600 |
| **Total** | | **1.2–1.8 KB/s ≈ 4.3–6.5 MB/hour** |

**4 MB holds less than one hour of raw data.** For wrist studies (sleep, overnight SpO2, workouts) that's the real limitation. Options:

1. **Engineering build** with the 64 Mbit MX25R6435F on the same footprint: ≈ 1.5–2 h.
2. **Compress:** delta + variable-length encoding on PPG and accel typically gives 2–3× on smooth signals (estimate). That's ≈ 4–6 h on 8 MB.
3. **Stream live** to a phone or PC during lab sessions (BLE_SECURITY_DFU §3). Overnight, the phone app stores it.
4. A larger SPI NAND (≥ 1 Gbit) gives ~30 h but needs a bigger package and a NAND-aware filesystem. That's an engineering-only option, not for P0.

**Recommendation:**

- **P0 engineering units:** 64 Mbit + compression + phone streaming.
- **Consumer build:** 32 Mbit.

---

## 3. Filesystem / layout

| Partition | Size (32 Mbit part) | Store | Why |
|---|---|---|---|
| Summary ring log | 3 MB | Zephyr **FCB** (flash circular buffer) | Append-only, wear spreads naturally, oldest data drops off when full, power-fail tolerant |
| Raw capture | (engineering only) | FCB or raw sectors with a header | Simple sequential streams |
| Spare / future | 1 MB | | Algorithm models, icon packs |

What is **not** on external flash:

- **Settings, bonds, keys** → internal RRAM (ZMS/NVS).
- **DFU slots** → internal RRAM (see mcu-ble BLE_SECURITY_DFU §2.4).

Reason: the external SPI bus is unauthenticated and physically probeable.

LittleFS also works, but a ring log of fixed-size records doesn't need a directory tree. FCB has less overhead and is simpler to recover.

## 4. Endurance and retention

- **NOR endurance:** typically 100 k program/erase cycles per sector (datasheet-class figure; confirm for the chosen part). 80 KB/day over a 3 MB ring erases each 4 KB sector once every ≈ 37 days. That's ≈ 10 erases a year, so endurance isn't an issue.
- **Retention:** typically ≥ 20 years (confirm). The band syncs daily anyway.
- **Data at rest:** summaries are personal health data. Encrypt the log records with a device key from the KMU (AES-CCM on the nRF54L15 crypto accelerator) so a desoldered flash reveals nothing. Cost: a few µs per record.

## 5. Power

- **Keep the flash in deep power-down** between writes (0.35 µA max on MX25R3235F).
- **Buffer in RAM:** 2–4 KB, flushed every ≈ 4 min or on a sync. That's a few page programs per flush, i.e. microamp-hours per day.
- **Never erase during an LRA burst** (power-battery PEAK_LOAD.md).

## 6. Tests

1. Write the log for 72 h at 10× the normal record rate, pulling power at random 200 times. The log must recover with at most the last unflushed RAM buffer lost.
2. Measure deep power-down current on the board with the SPI lines held in their idle state. Floating lines add leakage.
3. Record a raw capture of 30 min of walking, download it, and check sample counters for gaps.
