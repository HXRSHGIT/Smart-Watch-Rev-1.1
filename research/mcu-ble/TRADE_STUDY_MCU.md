# Trade Study — BLE SoC: nRF5340 vs nRF54L15

Brief §8 asks to "compare against a suitable nRF54 device for area, power, GPIO, SDK maturity, availability and migration cost before schematic freeze."

Candidates:

- **nRF5340-QKAA**: the brief's candidate.
- **nRF54L15**: the nRF54L family member with the most memory. The L10 and L05 are pin-compatible fall-backs.
- **nRF54H20** was looked at and dropped. It's a high-end multi-core part (WLCSP ≈ 2.7 × 2.2 mm per a third-party package drawing, unverified) aimed at heavier applications, and its SDK support is the least mature. Nothing in this band needs it.

---

## 1. Side-by-side

| Criterion | nRF5340-QKAA | nRF54L15 | Source |
|---|---|---|---|
| CPU | App M33 128 MHz + Net M33 64 MHz | M33 128 MHz + RISC-V coprocessor (FLPR) | [5340 PS](https://infocenter.nordicsemi.com/pdf/nRF5340_PS_v1.3.1.pdf), [54L15 page](https://www.nordicsemi.com/products/nrf54l15) |
| NVM / RAM (app) | 1 MB flash / 512 KB | 1.5 MB RRAM / 256 KB | same |
| Package / body | aQFN-94, 7 × 7 mm | **CSP47 2.25 × 2.45 mm**, QFN48 6 × 6 mm, QFN52, QFN40 | same |
| GPIO | 48 | 31 (QFN48) / 32 (CSP47) | same |
| Supply | VDD 1.7–3.6 V **or VDDH 2.5–5.5 V** | 1.7–3.6 V only | same |
| TX 0 dBm / RX 1 Mbps | 3.2 / 2.6 mA (3 V, DC/DC) | 4.8 / 3.4 mA (3 V) | same |
| Max TX power | +3 dBm | +8 dBm (CSP), +7 dBm (QFN) | same |
| Sleep (System ON, RTC) | ≈ 1.6–2.3 µA | 0.7–2.9 µA | [DevZone](https://devzone.nordicsemi.com/f/nordic-q-a/102217/nrf5340-system-on-sleep-current), 54L15 page |
| QSPI | Hardware QSPI | No hardware QSPI. External flash via SPIM, or "sQSPI" soft peripheral on the RISC-V core | [DevZone sQSPI threads](https://devzone.nordicsemi.com/f/nordic-q-a/121466/using-external-flash-with-sqspi-on-nrf54l15-for-firmware-update/535779) |
| Key storage | — | KMU (hardware key slots, used by MCUboot) | [NCS bootloader config](https://nrfconnectdocs.nordicsemi.com/addons/addon-sidewalk/latest/application_development/bootloader_configuration.html) |
| NFC-A tag (NFCT) | Yes | Yes | PS |
| SDK | nRF Connect SDK, mature since 2020 | nRF Connect SDK, production support since v2.8 (2024) | NCS release notes |

---

## 2. What actually matters for this band

### 2.1 Board area — the deciding factor

A WHOOP-class pod leaves roughly 20–25 mm of usable board width. Footprint including fan-out:

| Option | Body | Footprint with fan-out (approx.) | Assembly needs |
|---|---|---|---|
| nRF5340 aQFN-94 | 49 mm² | ≈ 60 mm² | 0.4 mm pitch, 2 rows, needs via-in-pad or HDI |
| nRF54L15 QFN48 | 36 mm² | ≈ 45 mm² | 0.4 mm pitch QFN, standard |
| nRF54L15 CSP47 | 5.5 mm² | ≈ 10 mm² | microvia HDI, Type 5 paste |

The CSP frees about 50 mm² compared with the nRF5340. That's roughly the area of the whole MAX86141 + photodiode optical island.

### 2.2 Power — smaller difference than the datasheet suggests

The nRF54L15's radio draws ~50 % more current per packet, but the radio is only on for a tiny fraction of the time in this product.

Estimate for a maintained connection at 1 s interval, ≈ 2 ms of radio activity per event (half TX, half RX):

| | Radio average | Sleep floor | Total |
|---|---|---|---|
| nRF5340 | (3.2 + 2.6) / 2 mA × 2 ms / 1 s ≈ **5.8 µA** | ~2 µA | ≈ 8 µA |
| nRF54L15 | (4.8 + 3.4) / 2 mA × 2 ms / 1 s ≈ **8.2 µA** | ~1–2 µA | ≈ 10 µA |

That's about 2 µA of difference. The PPG LEDs and the IMU average in the hundreds of µA, so **the SoC choice moves battery life by well under 5 %**. CPU energy per sample of DSP work is similar; the M33 runs at the same clock on both.

The real power difference comes from the supply arrangement:

- **nRF5340** can run straight from VBAT through VDDH, so no buck is needed for the SoC.
- **nRF54L15** needs the nPM1300 BUCK1 (1.8 V). The sensors need that rail anyway, because the MAX86141 VDD is 1.8 V, so the SoC adds nothing extra.

### 2.3 Pin budget (real count)

| Function | Pins | Notes |
|---|---|---|
| SPI bus (SCK, MOSI, MISO) | 3 | shared by MAX86141 and flash |
| MAX86141 CS + INT | 2 | |
| Flash CS | 1 | standard SPI. Quad adds 2 |
| I²C bus A (always-on: BMI270, BMP390, MAX30208, DRV2605L, nPM1300) | 2 | |
| I²C bus B (switched: OLED) | 2 | separate bus so the OLED's pull-ups can be switched off with it |
| BMI270 INT1 + INT2 | 2 | motion event + FIFO watermark |
| nPM1300 host INT | 1 | |
| DRV2605L EN | 1 | |
| OLED RES# | 1 | panel power via an nPM1300 load switch, no GPIO |
| 32.768 kHz crystal | 2 | optional, recommended for timing accuracy |
| NFCT antenna | 2 | only if a passive tag is kept |
| Debug UART (TX/RX) | 2 | test pads only |
| **Total** | **21–23** | |

SWD is dedicated on both parts and isn't counted.

**Result:** 31 GPIO on the nRF54L15 leaves ~8 spare. GPIO isn't a differentiator, but don't plan to add QSPI flash and a parallel display on the nRF54L15.

### 2.4 Memory

- **Firmware size estimate:** BLE host + controller ≈ 150–200 KB, Zephyr + drivers ≈ 80 KB, algorithms (HR, steps, sleep, activity tree) ≈ 100–200 KB, MCUboot ≈ 40–48 KB. Total ≈ 400–550 KB per image (estimate, to be measured on the first build).
- **nRF54L15:** 1.5 MB internal holds MCUboot + two ~700 KB image slots. **DFU doesn't need external flash at all.** That's simpler, faster to boot, and keeps the update path off an untrusted bus.
- **nRF5340:** 1 MB app flash forces the secondary slot into external flash. The network core image adds a second update path.

### 2.5 Firmware complexity

- **nRF5340:** two cores. The BLE controller runs on the network core with its own image, IPC and DFU, which adds complexity to bring-up and updates.
- **nRF54L15:** single application core. The RISC-V FLPR coprocessor is optional; it can run sQSPI or low-power sensor polling later.

### 2.6 Availability

Both are production parts from Nordic. Check stock at schematic freeze; this file doesn't record live stock.

---

## 3. Scoring (weights reflect this product)

| Criterion | Weight | nRF5340 | nRF54L15 (CSP) | nRF54L15 (QFN48) |
|---|---|---|---|---|
| Board area | 30 % | 2 | 5 | 3 |
| Average power | 20 % | 4 | 4 | 4 |
| Firmware simplicity / DFU | 15 % | 3 | 5 | 5 |
| Assembly risk | 15 % | 3 | 2 | 4 |
| SDK maturity | 10 % | 5 | 4 | 4 |
| Supply from VBAT | 10 % | 5 | 3 | 3 |
| **Weighted** | | **3.25** | **4.15** | **3.80** |

Scores are 1–5, from the facts above.

---

## 4. Recommendation

1. **Pick the nRF54L15 for P0.** Use the CSP47 if the PCB house can do HDI microvias, or the QFN48 for a cheaper first spin. The two aren't footprint-compatible, so decide before layout.
2. Run the SoC from the 1.8 V BUCK1, the same rail as the MAX86141 and the sensors. One I/O domain means no level shifters.
3. Keep the nRF5340 as the fall-back only if HDI is impossible **and** the QFN48 doesn't fit.
4. Migration cost if the client insists on the nRF5340: schematic and layout of the SoC block only. Firmware ports within nRF Connect SDK, but adds the network-core image.

## 5. Open items

- Confirm with the PCB fab: 0.35 mm-pitch CSP capability, microvia cost, and stack-up.
- Measure actual image size after the first firmware build, then fix the partition sizes.
- RF: the nRF54L15 gives more TX headroom (+7/+8 dBm), useful to recover body loss (see ANTENNA_RF.md), at a current cost.
