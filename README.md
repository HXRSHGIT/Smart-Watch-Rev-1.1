# Smart Watch Rev 1.1 — HealthOS Band R&D

R&D repository for the client's **HealthOS Band** (WHOOP-style wellness band with a hidden 64×32 OLED).
Source brief: [`docs/HARDWARE_ENGINEER_HANDOFF_REQUIREMENTS.md`](docs/HARDWARE_ENGINEER_HANDOFF_REQUIREMENTS.md) (copied unchanged).

Done by Harsh Thakur.

## How this repo is organised

`main` holds the brief, this index and the R&D map. Each R&D topic lives on its **own branch**, in its own folder under `research/`, so branches merge without conflicts.

| Branch | Folder | Covers (brief §) |
|---|---|---|
| `rnd/components` | `research/components/` | §8 — every candidate part plus alternatives, full detail (`COMPONENTS.md`) |
| `rnd/mcu-ble` | `research/mcu-ble/` | §4.6, §8 — nRF5340 vs nRF54, BLE security, DFU, antenna |
| `rnd/storage-nfc-dft` | `research/storage-nfc-dft/` | §4.6, §8 — external flash, active NFC, SWD, production test |
| `rnd/power-battery` | `research/power-battery/` | §4.7, §8 — power tree, battery sizing, battery-life model, pogo charging, peaks |
| `rnd/display-haptics` | `research/display-haptics/` | §4.4, §4.5 — OLED module, dead-front, back-power, LRA and driver |
| `rnd/optical-ppg` | `research/optical-ppg/` | §4.1, §8 — PPG HR, SpO2, optical stack, crosstalk |
| `rnd/sensors` | `research/sensors/` | §4.1 — IMU, pressure and vent, skin temperature, time sync |
| `rnd/algorithms` | `research/algorithms/` | §4.2, §4.3, §5 — activity, calories, sleep, HRV and other P1 algorithms |
| `rnd/validation` | `research/validation/` | §13–15 — test plan, compliance, mechanical, RF, water and sweat |

## R&D map: what actually needs research

Legend: **R&D** = open question, needs study or experiment · **Design** = known engineering, needs careful execution · **Owner** = client decision, not engineering.

| § | Point | Class | Why |
|---|---|---|---|
| 2 | Stealth dead-front vs visible OLED, same PCB | **R&D** | Transmission vs off-state blackness trade; needs material samples and measurement |
| 3 | Present all health outputs as estimates | Owner | Wording and claims policy; the sentence is cut off in the brief |
| 4.1 | Continuous / resting HR | **R&D** | Wrist PPG motion artifact; LED current vs battery |
| 4.1 | Workout HR and zones | **R&D** | HR accuracy during motion is the hardest PPG problem |
| 4.1 | Spot + sleep SpO2 | **R&D** | Reflective wrist SpO2 needs red/IR calibration against a reference; skin-tone bias |
| 4.1 | Skin temperature trend | **R&D** | Thermal isolation from PCB and battery heat; trend vs absolute |
| 4.1 | Motion data | Design | BMI270 is mature; orientation and FIFO setup |
| 4.1 | Pressure for floors | **R&D** | Waterproof breathable vent; sensitivity to wrist movement and temperature |
| 4.1 | Raw data access | Design | Logging and streaming bandwidth over BLE and flash |
| 4.1 | Sensor time sync | **R&D** | Common timebase across AFE, IMU and MCU FIFOs |
| 4.2 | Steps / distance / active min | Design | Known algorithms; tuning for wrist placement |
| 4.2 | Calories | **R&D** | Model choice (HR + motion + profile); estimate only |
| 4.2 | Floors / elevation | **R&D** | Barometer + IMU fusion |
| 4.2 | Activity classification + confidence | **R&D** | Needs a labelled dataset and an on-device model budget |
| 4.3 | Sleep detection / duration | **R&D** | Actigraphy + HR; validation vs reference |
| 4.3 | HW readiness for HRV / RR / stages | **R&D** | Sets PPG sample rate and timing jitter requirements now |
| 4.4 | 64×32 OLED module choice | **R&D** | Exact orderable module, flex, cover stack, outdoor readability |
| 4.4 | No back-power when display off | Design | Load switch + I/O state; measure leakage |
| 4.4 | Wake by gesture / tap | **R&D** | False-wake rate vs IMU power |
| 4.5 | LRA selection + patterns | **R&D** | Size, resonance, peak current, mounting in a thin band |
| 4.6 | BLE Android/iOS | Owner | Platforms to support |
| 4.6 | Secure pairing + authenticated DFU | Design | MCUboot / nRF Connect SDK; key management |
| 4.6 | External flash logging | Design | Capacity sizing vs offline days |
| 4.6 | SWD + production test access | Design | Pad plan, fixture |
| 4.7 | Battery capacity vs 5–7 days | **R&D** | Needs a duty-cycle power model, then a cell that fits the enclosure |
| 4.7 | Reversible pogo, faults | **R&D** | Bridge vs ideal-diode orientation fix, contact heating, ESD |
| 4.7 | Concurrent peak load | **R&D** | PPG pulses + radio + flash + haptic + NFC on a small cell |
| 4.7 | Charging limits | Design | Follow the cell datasheet; NTC wiring to nPM1300 |
| 5 | P1: HRV, RR, recovery, GPS, falls | **R&D** | Algorithm work; HW must not block it |
| 8 | MCU choice (nRF5340 vs nRF54) | **R&D** | Trade study before schematic freeze |
| 8 | Active NFC (ST25R210) | **R&D** | Use case unknown; power and antenna cost |
| 8 | Separate optical / NFC / display rails | **R&D** | Depends on the power model |
| 13 | Acceptance gates | Design | Test plan and fixtures per gate |

## Gaps in the brief

- Sections **6, 7, 9, 10, 11 and 12 are missing** (numbering jumps 5 → 8 → 13). Probably owner decisions, targets and deliverables. Ask the client.
- §3 is cut off mid-sentence: "…must be presented as estimates until the complete product".
- Open owner decisions: phone platforms, battery-life target, NFC use case, display module, water-resistance target.
