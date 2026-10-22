# MCU Comparison: ESP32-C3 module vs nRF54L15

**Project:** HealthOS Band, Iteration 1 (functional sensor prototype)
**Recommendation:** ESP32-C3-MINI-1-N4X for Iteration 1.

Done by Harsh Thakur.

Figures below are from vendor documentation as understood at the time of writing and must be re-checked against the exact datasheets before ordering.

## 1. Summary

Iteration 1 exists to get clean red/IR optical waveforms and temperature data onto a computer, quickly and with as few unknowns as possible. The ESP32-C3 module is the lowest-risk way to do that. The nRF54L15 is a strong chip, but on this board it adds parts, tools and bring-up steps that do not help the first-iteration goal.

## 2. Side-by-side comparison

| Area | ESP32-C3-MINI-1-N4X | nRF54L15 | Advantage for Iteration 1 |
|---|---|---|---|
| Form | Pre-built, pre-certified module: chip, flash, crystal, RF matching and antenna in one part | Bare SoC (CSP or QFN): flash is on-chip, but crystals, RF matching, antenna and decoupling are ours to design | **ESP32** |
| Programming and logging | Native USB Serial/JTAG: one USB-C cable programs, debugs and streams raw data | No USB. Needs an SWD programmer plus a separate USB-UART bridge for logging | **ESP32** |
| Extra parts for the dev loop | None beyond the USB-C connector and ESD part | SWD header, programmer or debug probe, USB-UART bridge IC, its supply and routing | **ESP32** |
| Recovery from bad firmware | Boot button plus reset, USB download mode | Needs a working probe and protection settings (APPROTECT / ERASEPROTECT) handled carefully, or the chip can be locked | **ESP32** |
| Radio | BLE 5 and Wi-Fi 4 | BLE 5.x, Thread, Zigbee, proprietary 2.4 GHz; no Wi-Fi | ESP32 (Wi-Fi is spare capability for lab use) |
| Radio certification | Module carries its own radio approvals; the product still needs its own testing, but the radio design risk is lower | Chip-down RF design: layout, matching and antenna tuning are our responsibility | **ESP32** |
| Memory | 4 MB flash, ~400 KB RAM | ~1.5 MB on-chip non-volatile memory, 256 KB RAM | ESP32 for raw-data buffering |
| Supply | 3.0 to 3.6 V | 1.7 to 3.6 V | nRF (can share the 1.8 V sensor rail) |
| Power consumption | Higher radio and sleep current | Lower; designed for coin-cell and small-battery wearables | **nRF** |
| Tools and SDK | ESP-IDF or Arduino; large community, many worked examples for MAX30102-class sensors | nRF Connect SDK (Zephyr); powerful but a steeper setup | **ESP32** |
| Maturity | Established part with a long field history | Newer part; fewer community examples and a younger SDK | **ESP32** |
| Security features | Secure boot and flash encryption | Stronger key storage (KMU), tamper options | nRF |
| NFC tag (tap-to-pair) | None | Passive NFC tag built in | nRF |
| Package size | Module ~13 x 16.6 mm | CSP 2.25 x 2.45 mm or QFN 6 x 6 mm, but needs surrounding RF parts | Tie (size is not a goal this iteration) |
| Board complexity | Simple 2-layer-friendly module footprint | Fine-pitch package, RF layout, more passives | **ESP32** |

## 3. Why the nRF54L15 would complicate Iteration 1

1. **No native USB.** The first board's whole workflow is "plug in one cable, flash, and stream data". On the nRF this needs a programmer plus a USB-UART bridge, which is two more interfaces that can each fail before any sensor is tested.
2. **More circuitry to get right.** Chip-down RF means crystals, matching network and antenna layout. A mistake there looks like a dead radio, and it is hard to tell from a firmware fault.
3. **Locked-chip risk.** Production-style protection on the nRF can lock out the debug port. A wrong setting during early firmware work can leave a board that cannot be recovered without a full erase.
4. **Heavier toolchain.** The nRF Connect SDK is capable but has a longer learning curve, and a newer chip has fewer solved examples when something goes wrong.
5. **No benefit on the first-iteration goals.** The board is USB-powered. Its lower power consumption is the nRF's main advantage and is not needed until a battery is added.
6. **More places for schedule slip.** Extra parts, extra tools and unfamiliar RF work all add rework risk before the sensing question (do we get a clean PPG signal?) is even answered.

## 4. What this means for the final band

The ESP32-C3 is the right choice to prove the sensing platform. It is **not** assumed to be the final wearable processor. Battery life for a 5-7 day band depends on measured current, and the ESP32 draws more than the nRF in radio and sleep modes. The final MCU decision is made after Iteration 1 data: measured sensor workload, measured power, and the firmware that actually runs on the board. The sensor drivers, HR/SpO2 algorithms and data formats built on the ESP32 are plain C and will port.

## 5. Decision

Use the **ESP32-C3-MINI-1-N4X** for Iteration 1. Revisit the processor at the start of the next hardware revision, when a battery, power measurements and a size target exist.
