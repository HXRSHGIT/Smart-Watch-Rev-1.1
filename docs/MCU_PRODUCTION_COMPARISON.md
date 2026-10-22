# ESP32-C3 vs nRF54L15 — What Each Choice Means in Production

**Project:** HealthOS Band (WHOOP-style band, 5–7 day battery target, hidden 64×32 OLED)
**Question:** If the processor chosen now goes into the production band, how does each choice affect the product?

Done by Harsh Thakur.

---

## 1. Bottom line

| | ESP32-C3 | nRF54L15 |
|---|---|---|
| Iteration 1 (USB-powered sensor board) | **Best fit**: one cable, pre-certified module, fast bring-up | Workable, but more tools and parts |
| Production band (battery, 5–7 days, small pod) | **Does not meet the brief**: ~3.7 days on 150 mAh in the typical profile, needs a ≥ 200 mAh cell for 5 days | **Meets the brief**: ~12 days on 150 mAh in the same profile |

The ESP32-C3 is excellent for proving the sensors. In production it costs about **3× the battery** for the same life, a quarter of the pod footprint, and a different power-management IC. The nRF54L15 was designed for exactly this class of product.

If production must use the same chip as Iteration 1, the processor for both should be the **nRF54L15**, using a pre-certified module (Ezurio BL54L15, 14 × 10 × 1.6 mm) for Iteration 1 if the bring-up speed of a module is wanted.

All figures below are from the vendor documents listed in §13. Battery numbers come from the repository's battery model (`research/power-battery/battery_model.py`) with only the processor loads swapped (`research/mcu-ble/mcu_power_compare.py`).

---

## 2. The parts being compared

| | ESP32-C3-MINI-1-N4X (module) | nRF54L15 (SoC) |
|---|---|---|
| CPU | 32-bit RISC-V single core, 160 MHz | Arm Cortex-M33, 128 MHz, plus 128 MHz RISC-V coprocessor |
| Floating point / DSP | **No hardware FPU** (RV32IMC) | FPU + DSP instructions |
| CoreMark | 483 (3.02 /MHz) | 503 (3.93 /MHz), from non-volatile memory |
| RAM | 400 KB SRAM (16 KB used for cache) + 8 KB RTC | 256 KB |
| Non-volatile memory | 4 MB flash in package, 100 000 erase cycles | 1524 KB RRAM, **10 000 write cycles**, 10-year retention at 85 °C |
| Radio | BLE 5 + Wi-Fi 4 (2.4 GHz) | BLE (incl. Channel Sounding), 802.15.4 (Thread/Zigbee/Matter), proprietary up to 4 Mbps; no Wi-Fi |
| Max TX power | +20 dBm | +8 dBm (CSP) / +7 dBm (QFN) |
| RX sensitivity, BLE 1 Mbps | −97 dBm | −96 dBm |
| USB | Native USB Serial/JTAG | **None** |
| NFC | None | NFC-A tag (tap-to-pair) |
| Supply | **3.0–3.6 V** | **1.7–3.6 V** (supply and GPIO) |
| Size | 13.2 × 16.6 × 2.4 mm module + antenna keep-out | CSP47 2.4 × 2.2 mm (0.3 mm pitch) or QFN48 6 × 6 mm (0.4 mm pitch) + crystal, inductor, RF match, antenna |
| GPIO | 15 (3 are boot straps) | 32 (CSP47) / 31 (QFN48) |
| Temperature | −40 to 85 °C (N4X) or 105 °C (H4X) | −40 to 105 °C |
| ESD (device) | HBM ±2 kV, CDM ±500 V | QFN: HBM 1 kV, CDM 500 V · CSP: HBM 3 kV, CDM 250 V |
| Moisture sensitivity | MSL 3 (solder within 168 h of opening) | QFN MSL 2 · CSP MSL 1 |

---

## 3. Battery life — the deciding difference

### 3.1 Datasheet currents

| Mode | ESP32-C3 (3.3 V) | nRF54L15 (3.0 V) | Ratio |
|---|---|---|---|
| BLE TX at 0 dBm | 170 mA (peak) | 4.8 mA | ~35× |
| BLE RX | 86 mA (peak) | 3.4 mA | ~25× |
| CPU running | 23 mA at 160 MHz (radio off, peripheral clocks off) | 2.6 mA CoreMark | ~9× |
| Sleep while keeping a BLE connection | **140 µA** with an external 32 kHz crystal · **2.3 mA** without one | **2.9 µA** System ON idle, 256 KB RAM retained, RTC running | ~50× / ~800× |
| Deepest sleep (BLE link lost) | 5 µA deep-sleep, 1 µA power-off | 0.7 µA System OFF | |

The sleep row matters most. A band spends > 99 % of its life asleep between connection events. ESP-IDF's own low-power guide says the internal 136 kHz RC oscillator **cannot hold a BLE connection**: you need either the main crystal running (2.3 mA) or an external 32 kHz crystal (140 µA). The MINI-1 module has no 32 kHz crystal; it must be added on GPIO0/GPIO1.

### 3.2 Whole-band battery life (same sensors, same use, only the processor changed)

| Use profile | nRF54L15 band | ESP32-C3 + 32 kHz crystal | ESP32-C3, no 32 kHz crystal |
|---|---|---|---|
| Lean (25 sps HR, light use) | 215 µA → **23.3 days** on 150 mAh | 886 µA → **5.6 days** | 3075 µA → 1.6 days |
| Typical (50 sps HR, 1 h workout) | 404 µA → **12.4 days** | 1355 µA → **3.7 days** | 3544 µA → 1.4 days |
| WHOOP-like (100 sps continuous) | 1227 µA → **4.1 days** | 2562 µA → **2.0 days** | 4751 µA → 1.1 days |
| Cell needed for 5 days, typical | **61 mAh** | **203 mAh** | 532 mAh |

Processor share of the typical band: **44 µA (11 %)** on the nRF vs **995 µA (73 %)** on the ESP32. On the ESP32 the processor becomes the biggest load, ahead of the PPG LEDs.

The ESP radio line uses datasheet peak currents for a 2 ms event once per second, so it is an upper estimate; a measured ESP link will be lower, but the 140 µA sleep floor alone (≈ 3.4 mAh/day) already exceeds the nRF band's whole processor budget (≈ 1.1 mAh/day). No firmware optimisation closes that gap.

### 3.3 What this does to the product

- A 200 mAh+ cell instead of ~60–150 mAh adds about **1 mm of pod thickness** and **2–3 g** (MECHANICAL_STACKUP §2, §5).
- The 5–7 day target in brief §4.7 is not reachable on ESP32 in a WHOOP-size pod with continuous HR.

---

## 4. Power system — ESP32 forces a different PMIC

| Item | ESP32-C3 | nRF54L15 |
|---|---|---|
| Rail | 3.3 V only (3.0 V minimum) | Runs directly on the shared 1.8 V rail |
| Supply capability required | Espressif: rail must deliver **≥ 0.5 A**; peaks 340 mA at +20 dBm, 170 mA at 0 dBm | Peak ≈ 10 mA at +8 dBm |
| Fits the planned nPM1300 (200 mA bucks)? | **No** — needs a separate ≥ 500 mA buck/buck-boost | **Yes** — one 200 mA buck covers it with margin |
| End-of-discharge | A 3.3 V LDO/buck from a Li-ion cell loses regulation below ≈ 3.4 V; usable capacity shrinks or a buck-boost is needed | 1.8 V buck stays in regulation down to the cell cut-off |
| Peak-load droop (PEAK_LOAD.md) | 170 mA radio bursts stack on PPG LED and haptic pulses (≈ 185 mA already) → ~350 mA on a small cell | Radio adds < 10 mA |
| eFuse programming | VDD3P3_CPU must not exceed 3.3 V while burning eFuses | n/a |

---

## 5. Board area, thickness and RF

| Item | ESP32-C3 module | nRF54L15 |
|---|---|---|
| Footprint | 219 mm² + antenna keep-out (≈ 25–30 % of a 35 × 25 mm pod) | ≈ 5 mm² CSP or 36 mm² QFN + ≈ 20 small passives + chip antenna |
| Thickness | 2.4 mm module | 0.85 mm QFN (nominal); CSP thinner |
| Antenna | Module PCB antenna; must sit at a board edge with nothing under it. On a wrist, body loading detunes it and we cannot retune it | Our own chip/PCB antenna, matched for the enclosure and wrist |
| Chip-down option | ESP32-C3FH4X (QFN32 5 × 5) is possible, but then we lose the module's certification and still carry the power problem | Native design approach |
| Pre-certified module option | The ESP module itself | Ezurio BL54L15: 14 × 10 × 1.6 mm, FCC/ISED/CE/MIC/RCM/UKCA, integrated antenna |

---

## 6. Sensor interfaces

| Item | ESP32-C3 | nRF54L15 |
|---|---|---|
| Logic level vs 1.8 V sensors | 3.3 V I/O. Sensors on 1.8 V (MAX86141 core/SPI, MAX30102 core) need translation. MAX86141 SPI is push-pull, so it needs a real translator IC, not BSS138s | Runs at 1.8 V — every sensor connects directly |
| Serial buses | SPI, 1× I2C, 2× UART, I2S | 5 serial units (I2C/SPI/UART, one HS-SPI 32 MHz), PDM, I2S |
| Free pins (band needs ≈ 21–23, TRADE_STUDY_MCU) | 15 GPIO, 3 are straps, 2 go to USB, 2 to a 32 kHz crystal → **≈ 8–10 usable**: **not enough for the full band** without an I/O expander | 31–32 GPIO: fits with spares |
| Signal processing (HR, SpO2, HRV filters) | No FPU: floating-point filters run in software; must be rewritten in fixed point | FPU + DSP extensions; RISC-V coprocessor can handle sensor FIFOs |
| ADC | 12-bit, ±10 mV after calibration; DNL ±7 LSB | 14-bit at 31.25 ksps |
| Wake on sensor interrupt | Light-sleep GPIO wake | GPIO SENSE wake (see erratum [114] in §9) |

---

## 7. Firmware, phone app and updates

| Item | ESP32-C3 | nRF54L15 |
|---|---|---|
| SDK / RTOS | ESP-IDF (FreeRTOS), NimBLE or Bluedroid host | nRF Connect SDK (Zephyr), Nordic SoftDevice Controller |
| BLE wearable track record | Mainly used in Wi-Fi IoT products | Nordic parts are widely used in BLE wearables and sensors |
| Firmware update over BLE | Possible, but OTA-over-BLE is mostly custom work | MCUboot + MCUmgr/SMP, with Nordic's **ready iOS and Android DFU libraries** (our BLE_SECURITY_DFU plan) |
| Memory for dual-slot update | 4 MB flash: two app slots + NVS + logs share it | Both slots in 1.5 MB RRAM; logs go to the external MX25R flash |
| Logging to internal memory | 100 000 cycles: workable for small logs | 10 000 cycles: **do not log to RRAM**; use the external flash (already planned) |
| Chip revision handling | MINI-1-N4 is **NRND**; replacement N4X uses chip rev v1.1, which needs a specific minimum ESP-IDF version | Single production revision (Rev 2) with published errata |
| Porting cost if Iteration 1 uses ESP and production uses nRF | Drivers and algorithms in plain C port; BLE, power, bootloader, DFU and build system are rewritten | — |

---

## 8. Security and privacy (health data, GDPR / DPDP)

| Item | ESP32-C3 | nRF54L15 |
|---|---|---|
| Secure boot | Secure Boot v2 (eFuse-held key digest) | Secure boot with hardware root of trust; MCUboot ED25519 |
| Data at rest | Flash encryption (key in eFuse) | TrustZone, secure storage, key management unit (KMU) |
| Physical attack protection | No tamper detectors listed | Tamper detectors (TAMPC, glitch detector), side-channel-protected crypto engine (CRACEN) |
| Debug lock | Disable USB-JTAG through eFuse | APPROTECT / ERASEPROTECT |
| Production key provisioning | eFuse burning is **one-way**; a mistake bricks the unit | KMU provisioning at the SWD fixture; note erratum [13] on KMU busy state |

Both can be made secure. The nRF has the stronger physical-attack story, which matters if health data is stored on the band.

---

## 9. Known silicon issues that affect this product

**nRF54L15 Revision 2 errata (v1.1, May 2026)** — 35 open anomalies, all inherited from Rev 1. The ones relevant to the band:

| ID | Issue | Effect on the band | Handling |
|---|---|---|---|
| [41] | RX sensitivity −2 dB on 2432 and 2464 MHz | Slightly shorter range on two channels | Acceptable; included in the link-budget margin |
| [30] | Real-time clock drifts at low temperature on internal clock | Timestamps in cold weather | Fixed in nRF Connect SDK 3.0+; also use the 32 MHz crystal |
| [105] | I2C peripheral locks up if disabled during clock stretching | MAX30208 / I2C sensor bus could hang | Never disable TWIM mid-transfer; reset recovers it |
| [114] | +300 µA in idle if a wake pin toggles fast | Sensor interrupts could add 300 µA | Use latched detect mode (LDETECT) |
| [100] | Analog-capable P1 pins briefly shorted at power-on | Don't put supply/drive nets on P1.04–P1.14 | Pin assignment rule |
| [37] | Higher System OFF current right after reset | Shipping-mode current | 1-line register workaround |
| [58] | Comparator leaves 300 µA static current | Only if COMP is used | Don't use COMP for battery sensing (PMIC does it) |

**ESP32-C3** — The module datasheet marks **ESP32-C3-MINI-1-N4 as NRND (not recommended for new designs)**; the bare ESP32-C3FN4 chip is **EOL**. Use **ESP32-C3-MINI-1-N4X** (or H4X for 105 °C). Chip-revision-specific issues are in the ESP32-C3 Series SoC Errata; firmware must target an ESP-IDF version that supports rev v1.1.

---

## 10. Certification and manufacturing

| Item | ESP32-C3 module | nRF54L15 chip-down | nRF54L15 via BL54L15 module |
|---|---|---|---|
| Radio certification (FCC/CE/etc.) | Module grant reused; product-level unintentional-emission and RF-exposure tests still needed | **Full** intentional-radiator testing | Module grant reused |
| Radios in scope | BLE **and Wi-Fi** | BLE only (+802.15.4 if enabled) | BLE |
| Bluetooth SIG listing | Required (product qualification) | Required | Required |
| Factory programming | USB/UART; eFuse keys one-way | SWD fixture (TC2030 pads, DFT_PROGRAMMING.md) | SWD |
| Assembly | MSL 3, single reflow for the module | QFN MSL 2 / CSP MSL 1; CSP needs HDI microvias | Module, standard reflow |
| Board technology | 2–4 layer | CSP needs HDI 1+N+1; QFN48 works on standard 4-layer | Standard |

---

## 11. What the nRF54L15 adds in flashing, debugging and day-to-day development

Moving from the ESP32-C3 to the nRF54L15 does not change the sensors or the algorithms. It changes **how firmware gets onto the chip, how we see what it is doing, and how a broken unit is recovered.** Each item below is extra work or extra equipment compared with the ESP32's single USB cable.

### 11.1 Flashing and recovery

| Item | ESP32-C3 | nRF54L15 | What it means for us |
|---|---|---|---|
| How firmware is loaded | USB-C cable, ROM bootloader (`esptool`), always present in silicon | **SWD debug probe only.** No USB, no ROM bootloader | Every bench, every engineer and every factory station needs a probe |
| Hardware needed | A USB cable | SEGGER J-Link (or the J-Link on an nRF54L15 DK used as an external programmer), plus a debug connector on the board | About one probe per developer plus spares; a DK can be the programmer during Iteration 1 |
| Debug connector | None | SWDIO, SWDCLK, nRESET, VDD reference, GND: a 10-pin 1.27 mm Cortex header on dev boards, Tag-Connect TC2030 pads on the band (DFT_PROGRAMMING.md) | Board area and a fixture design; the probe must sense the 1.8 V reference |
| Software tools | `esptool`, ESP-IDF | **nRF Util** (`nrfutil device program`, `nrfutil device recover`) and `west flash`. The older `nrfjprog` is being retired, so older guides and scripts do not apply | Tool versions must be kept in step with the SDK; out-of-date tools report "unknown device" on nRF54L parts |
| Recovering a board with bad firmware | Hold BOOT, reset, re-flash over USB | Probe **erase-all** (`nrfutil device recover`) wipes the whole chip, then re-flash | Recovery also wipes stored keys, calibration and logs held in RRAM |
| If debug protection is on | Secure download mode and eFuses limit USB access | `APPROTECT` blocks the debugger; erase-all temporarily re-opens it. **If `ERASEPROTECT` is also set, erase-all is disabled** and the port can only be re-opened by firmware that cooperates with the debugger | A wrong protection setting can permanently lock a unit. Protection is set **only at the end of the production line**, never on development boards |
| Updating units in the field | OTA (custom BLE OTA, or Wi-Fi) | MCUboot bootloader + BLE update (MCUmgr/SMP) with Nordic's phone libraries | MCUboot and image signing must be set up **before** the first unit leaves the bench. If MCUboot itself is damaged, only SWD can fix the unit |
| Fallback serial recovery | Built into ROM | Optional MCUboot serial recovery over UART (must be designed in) | Worth enabling on Iteration 1 boards |

### 11.2 Seeing what the firmware does (logs and data)

| Item | ESP32-C3 | nRF54L15 |
|---|---|---|
| Debug logs | Over the same USB cable | **SEGGER RTT through the debug probe** (fast, no extra pins), or a UART |
| Streaming raw PPG to a PC | Native USB | UART + a **USB-UART bridge IC** (with a 1.8 V I/O supply pin), over BLE, or RTT through the probe |
| Step-through debugging | USB-JTAG on the same cable | Full Cortex-M debug (breakpoints, ETM/ITM trace) through the probe: more capable, but the probe must be attached |
| Measuring current | Bench meter | Same, plus Nordic's Power Profiler Kit II, the usual tool for µA-level sleep checks: one more piece of equipment, but needed to prove the battery numbers |

### 11.3 Build system and firmware setup

- **nRF Connect SDK (Zephyr).** Larger install, the `west` build tool, **devicetree** for pins and peripherals, **Kconfig** for features, and sysbuild to build the application and MCUboot together. Powerful, but the learning curve is steeper than ESP-IDF.
- **Custom board definition.** Our board needs its own devicetree board files (pin control, clocks, rails) before any sample runs. The ESP32 module works with stock settings.
- **The SDK version is part of the hardware fix list.** Several errata workarounds (for example [30] GRTC drift) exist only in nRF Connect SDK 3.0 or later, so the SDK version must be pinned and recorded.
- **Two processors.** The RISC-V coprocessor runs its own firmware image. Using it (for sensor FIFOs or sQSPI) means a second build and harder debugging. It is optional; Iteration 1 does not need it.

### 11.4 Hardware design work the module would have done for us

| Item | Work on the nRF54L15 |
|---|---|
| 32 MHz crystal | Required; placement and load capacitance (internal tunable capacitors) must be set |
| 32.768 kHz crystal | Optional; saves current versus the internal RC oscillator. Decide by measurement |
| DC/DC inductor | Required for the low currents in §3; without it the chip runs in the less efficient LDO mode |
| RF matching and antenna | Our own matching network and antenna, tuned **in the real enclosure on a wrist** with a vector network analyser |
| Pin assignment rules | Avoid the errata pins (§9: P1.04–P1.14 at power-up); keep analog inputs away from noisy lines |

### 11.5 Security setup and production line

| Step | What has to be done | Risk if done wrong |
|---|---|---|
| Signing keys | Generate MCUboot signing keys, store them off-line, sign every release | Lost key = no more field updates; leaked key = anyone can push firmware |
| Key provisioning | Load keys into the KMU at the programming station (erratum [13]: do not re-trigger provisioning while the KMU is busy) | Unit boots unsigned, or not at all |
| Debug lock | Set `APPROTECT` (and, if chosen, `ERASEPROTECT`) as the **last** station step | Locked before testing is complete → the unit cannot be re-flashed |
| Factory flow | Pogo-pin SWD fixture → program → RF self-test (radio test firmware) → functional test → protect → serialise | Each station needs a probe; programming time sets line throughput |
| Radio certification testing | The lab needs DTM / radio-test firmware and a way to command it (UART or probe) | Test pads must be planned into the board |

### 11.6 How to keep this complexity manageable

1. **Use the BL54L15 pre-certified module for Iteration 1.** It removes the crystal, RF matching, antenna tuning and radio certification from the first board, while running the production silicon.
2. **Use an nRF54L15 DK as programmer and reference.** Its on-board J-Link programs our board through the debug-out header; one DK per engineer.
3. **Put a 10-pin debug header and a USB-UART bridge on Iteration 1.** This gives back the one-cable workflow for data streaming, with RTT for logs.
4. **Enable MCUboot with serial recovery from day one,** so a bad build is fixed without erasing the chip.
5. **Pin the SDK and tool versions** in the repository, and keep debug protection **off** until the production line.
6. **Write the board devicetree once** and reuse it for every revision.

---

## 12. Pros and cons summary

### ESP32-C3

**Pros**
- Single USB-C cable for flashing, debugging and data streaming.
- Pre-certified module with antenna: lowest RF and certification risk.
- 4 MB flash and 400 KB RAM for raw-data buffering.
- Large community, fast prototyping, Wi-Fi available for lab data offload.
- +20 dBm TX for long range when needed.

**Cons in production**
- ~3× the battery for the same life; 5 days typical needs ≥ 200 mAh, against 61 mAh on the nRF.
- 3.3 V-only: needs its own ≥ 500 mA regulator, can't share the 1.8 V rail, loses regulation at low cell voltage.
- The planned nPM1300 PMIC cannot power it.
- Module takes ~25–30 % of the pod footprint and 2.4 mm height.
- Only ~8–10 usable GPIO after straps, USB and the 32 kHz crystal: not enough for the full band.
- No FPU: PPG filtering must be written in fixed point.
- Needs level translators for every 1.8 V sensor, including a push-pull translator for MAX86141 SPI.
- No NFC tap-to-pair. Wi-Fi radio adds certification scope with no product use.
- Base part number already NRND; must use the newer N4X.

### nRF54L15

**Pros**
- Meets the 5–7 day target with a small cell (≈ 12 days typical on 150 mAh).
- Runs on the shared 1.8 V rail; every sensor connects directly; fits the nPM1300.
- Tiny (CSP 2.4 × 2.2 mm) with 31–32 GPIO.
- FPU/DSP plus a RISC-V coprocessor for sensor handling.
- NFC tap-to-pair, Channel Sounding, Thread/Matter capable.
- Strongest security: TrustZone, KMU, tamper and side-channel protection.
- Mature BLE DFU with ready phone libraries.
- Pre-certified module option (BL54L15) if a module is preferred.

**Cons**
- No USB and no ROM bootloader: every flash and recovery goes through an SWD probe; data streaming needs a USB-UART bridge or RTT (§11).
- Recovery by erase-all wipes keys and calibration; a wrong `ERASEPROTECT` setting can lock a unit permanently.
- Zephyr build system, a custom board devicetree and pinned SDK versions add set-up work before the first sample runs.
- Chip-down RF design (antenna, matching, crystal) and full radio certification unless a module is used.
- Newer part: 35 published errata (none blocking, several need firmware or pin-assignment rules), younger SDK, fewer community examples.
- RRAM endurance 10 000 cycles: logs must go to external flash (already planned).
- CSP package needs HDI; QFN48 avoids that at a larger footprint.
- Steeper toolchain (Zephyr / nRF Connect SDK).

---

## 13. Sources

- Espressif, *ESP32-C3 Series Datasheet* v2.4 — tables 1-1, 5-1 to 5-11, 6-8, 6-12.
- Espressif, *ESP32-C3-MINI-1 & MINI-1U Datasheet* v2.2 — tables 1-1, 6-4 to 6-7, §12.
- Espressif, ESP-IDF *Bluetooth LE low-power mode* guide and `examples/bluetooth/nimble/power_save` README (light sleep 2.3 mA main XTAL / 140 µA 32 kHz crystal).
- Nordic Semiconductor, *nRF54L15/nRF54L10/nRF54L05 Datasheet* v1.0 (Sep 2025) — key features, tables 96–98.
- Nordic Semiconductor, *nRF54L15 Revision 2 Errata* v1.1 (2026-05-12).
- Nordic datasheet v1.0 §9.6 CTRL-AP (erase all, erase protection) and UICR APPROTECT / ERASEPROTECT registers.
- Nordic DevZone: nrfjprog retirement and `nrfutil device recover` for nRF54L15.
- Ezurio, *BL54L15 Series Datasheet* v1.1.
- This repository: `research/power-battery/battery_model.py`, `research/mcu-ble/mcu_power_compare.py`, `research/mcu-ble/TRADE_STUDY_MCU.md`, `research/validation/MECHANICAL_STACKUP.md`, `research/power-battery/PEAK_LOAD.md`.
