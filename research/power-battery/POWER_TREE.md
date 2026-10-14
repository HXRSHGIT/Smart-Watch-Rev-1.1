# Power Tree

Brief §4.7 and §8: "Recalculate every rail and concurrent peak", "review whether separate optical, NFC or display rails remain justified after the final duty cycles and battery are known."

---

## 1. Voltage needs of every load

| Load | Supply pins | Allowed range | Source |
|---|---|---|---|
| nRF54L15 | VDD | 1.7–3.6 V | [Nordic](https://www.nordicsemi.com/products/nrf54l15) |
| MAX86141 | VDD (core + I/O) | **1.8 V** | [ADI](https://www.analog.com/en/products/max86141.html) |
| MAX86141 | PVLED (LED drivers) | **3.1–5.5 V** | ADI |
| BMI270 | VDD / VDDIO | 1.71–3.6 / 1.2–3.6 V | Bosch |
| BMP390 | VDD / VDDIO | 1.65–3.6 / 1.2–3.6 V | Bosch |
| MAX30208 | VDD | 1.7–3.6 V | ADI |
| MX25R3235F flash | VCC | 1.65–3.6 V | Macronix |
| W25Q32RV flash (brief's part) | VCC | 2.7–3.6 V ✗ | Winbond via DigiKey |
| DRV2605L | VDD | 2.0–5.2 V | TI |
| SSD1306 OLED | VDD (logic) | 1.65–3.3 V | [SSD1306 spec (quoted in panel datasheets)](https://download.unisystem.com/OLED-displays/WEO009616BWPP3N0Y000/WEO009616BWPP3N0Y000.pdf) |
| SSD1306 OLED | VBAT (charge-pump input) | **3.3–4.2 V** → internal VCC ≈ 7.5 V | same |

---

## 2. Proposed tree

```
 Pogo ─► OCVPB21 (bridge+OVP+OCP) ─► nPM1300 VBUS
                                         │ charger
 Cell (3.0–4.2 V, PCM, NTC) ◄────────────┤ VBAT
                                         │ power path
                                       VSYS ──┬─► BUCK1 1.8 V (≈ 5–30 mA) ─► nRF54L15, MAX86141 VDD,
                                              │                             BMI270, BMP390, MAX30208,
                                              │                             MX25R flash, I²C pull-ups (always-on bus)
                                              │       └─► LS1 (load switch) ─► OLED VDD + OLED I²C pull-ups
                                              │
                                              ├─► LS2 (load switch) ───────► OLED VBAT (charge pump)
                                              │
                                              ├─► MAX86141 PVLED   (direct VSYS, + bulk cap)
                                              ├─► DRV2605L VDD     (direct VSYS)
                                              │
                                              └─► BUCK2: spare / off (only needed if a 3 V-only part stays)
```

One 1.8 V rail runs the whole digital and sensor domain:

- no level shifters;
- one I²C voltage;
- lowest power, since every sensor's current scales with supply.

---

## 3. Points that need decisions

### 3.1 LED supply (PVLED ≥ 3.1 V) — biggest issue

The nPM1300 bucks only go up to 3.3 V and can't supply much more than 200 mA, so PVLED has to come from **VSYS** (≈ VBAT when not charging). Two options:

| Option | Behaviour | Cost |
|---|---|---|
| **A. PVLED = VSYS direct** | Works while VBAT > ≈ 3.1 V **plus** green LED Vf **plus** driver headroom. Green Vf is 2.4 V typ / 2.8 V max at 20 mA ([SFH 7016 DS](https://look.ams-osram.com/m/566c673078988944/original/SFH-7016.pdf)) and higher at 40–100 mA pulses. **PPG may drop out at roughly 3.4–3.5 V** (estimate; measure), the last ~10–15 % of the charge | 0 parts |
| **B. Small boost to ~4.5–5 V for PVLED** | PPG works down to cut-off; constant LED headroom | +1 IC, inductor, ≈ 10–15 mm² board, ≈ 85–90 % efficiency on LED energy |

**Recommendation:**

- On **P0, lay out option B** with a 0 Ω bypass link, so A can be tested on the same board.
- **Measure the actual dropout voltage** at the planned pulse currents over 0–40 °C, then decide for the next revision.
- Candidate boosts must be ≤ 2 × 2 mm with low-Iq PFM (e.g. TI TPS61240-class; confirm the part is current).

The client should hear that low battery degrades heart rate before the band shuts down; if A is chosen, firmware should say so (show "low battery – HR paused").

### 3.2 Flash voltage

The brief's W25Q32RV is 2.7–3.6 V only. Keeping it would need BUCK2 at 3.0 V **and** level translation on the SPI bus.

**Swap to MX25R3235F** (1.65–3.6 V, deep power-down 0.35 µA). This removes a rail.

### 3.3 Display rails

The SSD1306's VBAT charge-pump input needs 3.3–4.2 V. That's the cell itself, so the display stops being reliable below ≈ 3.3 V. That's fine: the band should already be warning "charge me" by then.

Two load switches (LS1, LS2), both from the nPM1300 (100 mA rating each):

1. **LS2 on OLED VBAT:** the panel draws nothing while dark. The SSD1306 "display off" command still leaves the controller powered.
2. **LS1 on OLED VDD + its own I²C pull-ups**, so that switching the OLED off can't back-power it through SDA/SCL (brief §4.4). The OLED gets **its own I²C bus**, so pulling those lines low or Hi-Z doesn't disturb the always-on sensors.

Power-up order: VDD → VBAT. Power-down order: VBAT → VDD. Both follow the SSD1306 sequence; check it against the selected panel's datasheet.

### 3.4 NFC rail

Not needed. The active ST25R210 is recommended out of P0 (storage-nfc-dft NFC_ACTIVE.md). If it comes back, its up-to-1.6 W RF stage must run from VSYS with its own bulk capacitor.

### 3.5 Optical rail

Not needed as a separate regulator. AFE VDD shares BUCK1. PVLED is VSYS or the boost (§3.1).

---

## 4. Rail currents (1.8 V BUCK1)

| Load | Typical | Peak |
|---|---|---|
| nRF54L15 | ≈ 1–5 µA sleep, 2.6 mA CPU, ≈ 5–8 mA radio at 1.8 V | ≈ 10 mA |
| MAX86141 VDD | < 10–40 µA | ≈ 1 mA (unverified) |
| BMI270 | 210–685 µA | < 1 mA |
| BMP390, MAX30208 | µA | < 0.1 mA each |
| MX25R flash | 0.35 µA DPD | program/erase ≈ 10 mA class (verify in DS) |
| OLED VDD (logic) | | < 1 mA |
| **Total** | **< 1 mA average** | **≈ 25 mA** |

BUCK1 (200 mA) runs at ≈ 10 % of its rating at peak. **BUCK2 can be left disabled.**

## 5. Ship / storage mode

- **nPM1300 ship mode draws 370 nA; hibernate draws 500 nA** ([Nordic](https://www.nordicsemi.com/Products/nPM1300)).
- Add the cell PCM quiescent (≈ 1–3 µA, assumed). A 150 mAh cell at 50 % charge then sits for **≈ 2–5 years** before reaching cut-off.
- **Exit ship mode by docking** (VBUS present) or the SHPHLD pin. With no button on the band, wake-on-dock is the only exit. Factory flow: program → test → enter ship mode → box.

## 6. Next steps

1. Bench the green LED dropout on the MAX86141 EVKIT with PVLED swept 3.0–4.2 V.
2. Choose and verify the PVLED boost part.
3. Confirm the SSD1306 power sequencing and the VBAT-low behaviour on the chosen panel.
