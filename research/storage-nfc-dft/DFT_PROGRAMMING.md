# Programming, Recovery and Production Test Access

Brief §4.6: "Factory programming, erase, recovery and debug through accessible SWD pads. Production test access for critical rails, reset and selected buses."
Brief §13: "Repeatable SWD programming, erase and recovery." "Correct rail startup, shutdown and fault behavior."

---

## 1. SWD connector

| Option | Board cost | Fixture | Comment |
|---|---|---|---|
| **Tag-Connect TC2030-NL** (6 pads, "no legs") | 6 pads (≈ 0.02 in² pad area) + 3 alignment holes, no parts | TC2030-CTX-NL cable, hand-held | Standard for small boards; signals VCC, SWDIO, SWCLK, SWO, nRESET, GND ([Tag-Connect/DebugStore](https://thedebugstore.com/de/products/tag-connect-tc2030-ctx-nl-st14-stm32-swd-programming-cable)) |
| **Bare test pads** for a pogo fixture | 5–6 Ø 0.8–1.0 mm pads at ≥ 1.27–2.0 mm pitch | Custom bed-of-nails | Best for production; same pads also serve test |
| 10-pin 1.27 mm header | ≈ 6 × 6 mm + height | Standard cable | Too big and tall |

**Recommendation:**

- **P0:** TC2030-NL footprint on the PCB back side (dev and bring-up).
- **Production:** the same signals also on round test pads, alongside the rail and bus test points (§3). One pogo fixture then programs and tests in one clamp.

Once the band is sealed, the only way in is the two charging pogo pads. Program and test **before** final assembly, and keep the BLE DFU path robust (mcu-ble BLE_SECURITY_DFU).

## 2. Debug protection (nRF54L15)

- **Locking:** **UICR.APPROTECT** and **UICR.SECUREAPPROTECT** lock the debug port. Nordic recommends locking both for production. Once locked, debug can't be reopened without erasing the NVM.
- **Recovery:** `nrfutil device recover` runs ERASEALL and loads firmware that leaves the port open.
- **ERASEPROTECT:** if **UICR.ERASEPROTECT** is set, ERASEALL is disabled and *recover fails*. The device can then never be reprogrammed over SWD. **Never set it on engineering units. For production, decide deliberately** (it stops a thief wiping and reusing a band, but also stops RMA rework).

Source: [Nordic DevZone, nRF54L15 lock/unlock procedure](https://devzone.nordicsemi.com/f/nordic-q-a/128209/request-for-nrf54l15-jtag-lock-unlock-procedure/567027), [ERASEPROTECT clarification](https://devzone.nordicsemi.com/f/nordic-q-a/128778/clarification-on-nrf54l15-eraseprotect/569379).

| Build | APPROTECT | ERASEPROTECT |
|---|---|---|
| Engineering (P0/Rev C) | open | off |
| Pilot | locked | off |
| Production | locked | client decision |

## 3. Test points

| Test point | Why |
|---|---|
| VBAT (after PCM), GND | cell voltage, current measurement with series shunt in the fixture |
| VSYS | power path |
| 1.8 V (BUCK1) | main rail |
| PVLED (boost out or VSYS) | LED supply |
| OLED VBAT and VDD (after load switches) | prove switch-off (back-power test) |
| nRESET | hold in reset / reset test |
| I²C SDA/SCL (always-on bus) | bus test, sensor ID read-back from the fixture if needed |
| UART TX/RX | test firmware console |
| nPM1300 SHPHLD | wake from ship mode without docking |

Pads: Ø 0.8 mm minimum, on one face, with ≥ 1.27 mm spacing (fixture vendors work fine at this). Keep them away from the optical window and pogo area.

## 4. Factory flow

1. **Power-up test (current-limited).** Fixture applies VBAT from a source-meter at 3.8 V, 100 mA limit. Pass: no short (current < 5 mA before the firmware starts).
2. **Rails.** Measure 1.8 V, VSYS. Check BUCK1 within ±3 %.
3. **Program the test firmware over SWD** (MCUboot + factory test app).
4. **Self-test over UART.** The firmware reads back WHO_AM_I and part IDs: BMI270, BMP390, MAX30208, MAX86141, DRV2605L, nPM1300, flash JEDEC ID. It also drives the LRA (fixture accelerometer or current signature), lights the OLED (fixture camera or photodiode), and pulses each PPG LED (fixture photodiode).
5. **Sleep current.** Command ship mode → expect < 2 µA. Command System ON idle → expect within the spec set after P0.
6. **Program production firmware.** Write the device identity (serial, BLE address policy) and keys (KMU).
7. **Lock APPROTECT** → verify debug refuses access → enter ship mode.
8. **Log** every reading per serial number.

## 5. Recovery paths

| Situation | Path |
|---|---|
| Bad firmware, debug open | SWD reprogram |
| Bad firmware, debug locked | `nrfutil device recover` (erases all), then reprogram + re-provision keys |
| Bad app image after DFU | MCUboot keeps the previous image (swap mode) or BLE DFU again (overwrite-only) |
| Sealed unit, BLE dead | Only service disassembly. This is why DFU robustness matters |

## 6. Tests for §13

1. 50 program/erase/recover cycles on 3 boards with the TC2030 and with the pogo fixture → 100 % success.
2. Lock, then recover, on 3 boards → recover works when ERASEPROTECT is off.
3. Ship-mode current on every P0 board, logged.
