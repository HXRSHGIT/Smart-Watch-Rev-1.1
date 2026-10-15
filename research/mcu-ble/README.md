# R&D — BLE SoC, Security and Antenna

Branch `rnd/mcu-ble`. Covers brief §4.6 (BLE, secure pairing, authenticated DFU), §8 (controller choice) and §13 (BLE range, antenna tuning).

| File | What it answers |
|---|---|
| [TRADE_STUDY_MCU.md](TRADE_STUDY_MCU.md) | nRF5340 vs nRF54L15: area, power, pins, memory, firmware, with a weighted score |
| [BLE_SECURITY_DFU.md](BLE_SECURITY_DFU.md) | Pairing model, bonds, MCUboot + SMP update, downgrade protection, raw-data streaming |
| [ANTENNA_RF.md](ANTENNA_RF.md) | Antenna options, layout rules, on-wrist tuning, link budget |

## R&D questions → answers

| # | Question (brief §) | Answer | Status |
|---|---|---|---|
| 1 | Which SoC? (§8) | **nRF54L15**: CSP47 if HDI is available, QFN48 otherwise. Saves ≈ 50 mm² vs nRF5340; the power difference is ≈ 2 µA average | Recommendation, needs fab confirmation |
| 2 | Enough GPIO? (§8) | 21–23 pins needed, 31 available | Done |
| 3 | Secure pairing on a band with no keypad? (§4.6) | LESC + **Passkey Display on the OLED** (MITM-protected). Just Works is rejected | Done, Stealth readability to confirm |
| 4 | Authenticated FW update? (§4.6) | MCUboot + ED25519, key in KMU, SMP only over bonded links. Both slots in internal RRAM | Done, check the NCS version |
| 5 | Rollback protection? | Software downgrade prevention needs overwrite-only mode; hardware counter support on nRF54L15 is unconfirmed | Open |
| 6 | Raw data access? (§4.1) | ≈ 2.5 KB/s worst case. Record-to-flash + bulk download; live stream for bench only | Done |
| 7 | Range on the wrist? (§13) | ≈ 5 dB margin at 10 m at 0 dBm → use +4 to +8 dBm for sync | Estimate, measure |

## Decisions for the client

- Android, iOS or both (§4.6 says "requires owner confirmation"). It changes the test matrix, not the hardware.
- Does the PCB house support HDI (needed for the CSP)?

## Next experiments

1. Build the first firmware image on an nRF54L15 DK and measure its size → fix the partitions.
2. Measure average current of a maintained connection at 1 s interval on the DK with a PPK2.
3. Order 2 antenna types. Tune on the first board in the housing, on a wrist.

Done by Harsh Thakur.
