# Display — 0.49" 64×32 OLED and Alternatives

Brief §4.4:
- "Very small monochrome OLED; current evaluation class is 64 × 32 pixels."
- "Candidate display size: approximately 14.5 × 11.6 mm module with an active area around 11.2 × 5.6 mm. The engineer must verify the exact orderable module and mechanical interface."
- "Display-off state must not back-power the module through communication pins."

---

## 1. What the 0.49" class actually is

| Item | Value | Source |
|---|---|---|
| Resolution | 64 × 32, monochrome (usually white) | suppliers below |
| Active area | 11.18 × 5.58 mm | [Waveshare](https://www.waveshare.com/0.49inch-oled-module.htm), [BuyDisplay](https://www.buydisplay.com/i2c-white-0-49-inch-oled-display-module-64x32-arduino-raspberry-pi) |
| Pixel | 0.153 × 0.153 mm, duty 1/32 | supplier data |
| Brightness | ≈ 180 cd/m² (one supplier's figure) | supplier data |
| Contrast / viewing | 10,000:1, ≈ 160° | supplier data |
| Panel outline | 14.5 × 11.6 × 1.2 mm (bare COG variant). One module listing gives 14.85 × 16.6 × 2.36 mm (includes FPC/board) | supplier data |
| Driver | **SSD1306 or SSD1315**, depending on the panel maker | supplier data |
| Driver supplies | VDD 1.65–3.3 V (logic), VBAT 3.3–4.2 V (charge-pump input), internal VCC ≈ 7.5 V | [SSD1306 spec as quoted in a panel datasheet](https://download.unisystem.com/OLED-displays/WEO009616BWPP3N0Y000/WEO009616BWPP3N0Y000.pdf) |

**Two different products are sold under the "0.49 inch OLED" name:**

1. **Bare COG panel with FPC** (≈ 14.5 × 11.6 × 1.2 mm). This is what the brief's numbers describe and what goes in the band.
2. **Hobby breakout boards** (Waveshare, BuyDisplay, AliExpress). These add an LDO and pull-ups and are thicker. Use them only for firmware bring-up.

**Action:** request the drawing and FPC pin-out from 2–3 panel makers for the **bare** panel. Confirm:

- the driver (SSD1306 vs SSD1315: close command sets but not identical; check the init sequence);
- the FPC bend radius and length;
- the bonding/stiffener area;
- and that the panel's own datasheet gives luminance at a stated contrast setting.

## 2. Power

| State | Current | Note |
|---|---|---|
| Lit, ~25 % pixels, medium contrast | ≈ 5–15 mA (estimate) | PMOLED current scales with lit pixels × brightness. **Measure per icon** |
| Display OFF command (controller alive, pump off) | µA class (check the panel DS) | still powered |
| VBAT and VDD switched off | 0 | target state between wakes |

The power-battery model uses 10 mA × 3 s per wake. At 25 wakes/day that's ≈ 9 µA average, about 2 % of the typical budget. **The display isn't a battery problem** as long as it's really switched off between wakes.

## 3. Power-off topology (no back-powering)

```
 1.8 V BUCK1 ─► LS1 ─► OLED VDD ─┬─ 4.7 kΩ ─ SDA_D ─┐
                                 └─ 4.7 kΩ ─ SCL_D ─┤ dedicated I²C bus (TWIM #2)
                                                    │
 VSYS ─────────► LS2 ─► OLED VBAT (charge pump)     │
                                                    │
 nRF GPIO RES# ─────────────────────────────────────┘
```

Rules:

1. **Separate I²C bus for the display.** Its pull-ups sit on the **switched** VDD, so when LS1 is off no pull-up current flows into the panel.
2. **Before switching off:** send Display OFF, wait, open LS2 (VBAT), then open LS1 (VDD). Then set SDA_D, SCL_D and RES# to **disconnected input** (or drive low) on the nRF side. A GPIO driven high into an unpowered VDD back-powers the driver through its ESD diodes. That's exactly what the brief warns about.
3. **Power-up:** close LS1, wait ≥ 1 ms, release RES#, close LS2, then initialise. Check the exact sequence and delays against the chosen panel's datasheet.
4. **Prove it in test:** with the display off, measure current on OLED VDD and VBAT (DFT test points). Target < 0.1 µA (proposed).

The nPM1300's two load switches (100 mA each) do LS1 and LS2 with no extra parts.

## 4. Alternatives worth a look

| Option | Size | Power | Readability | Fit |
|---|---|---|---|---|
| **0.49" 64×32 PMOLED** (brief) | active 11.2 × 5.6 mm | mA when lit, 0 when off | emissive, ≈ 180 cd/m² | Matches the "hidden until wake" concept. Weak in direct sun |
| 0.42" 72×40 PMOLED (SSD1306-class, common) | slightly smaller active area | similar | similar | A bit more resolution in a smaller area. Check availability |
| **Sharp memory-in-pixel LCD** LS011B7DH03, 1.08" 160×68 | 32 × 14 × 0.745 mm, active 25.3 × 10.7 mm | **≈ 25 µW** typ, can stay on all the time | reflective: **best in sunlight**, poor in the dark without a front light | Doesn't fit the Stealth "dark when off" look (it's grey/silver), and it's twice as wide ([DigiKey](https://www.digikey.com/en/products/detail/sharp-microelectronics/LS011B7DH03/25953418), [Data Modul](https://data-modul.com/en/products/product-catalogue/mip-displays/ls011b7dh03)) |
| Discrete LEDs behind the dead-front (icon segments) | tiny | lowest | bright | No arbitrary icons or numbers. Too limited for HR/SpO2 results |

**Recommendation:** keep the 0.49" PMOLED for both variants (brief §2: same PCB, same resolution). Mention the memory LCD to the client only as a P1 "always-readable" variant, because it changes the industrial design.

## 5. Readability numbers (see also DEAD_FRONT.md)

- **Indoor (≈ 500 lux):** any cover works.
- **Outdoor shade (≈ 10,000 lux) and sun (≈ 50,000–100,000 lux):** glare from the cover surface swamps a 180 cd/m² emitter. Worked numbers in DEAD_FRONT.md §3.
- **Firmware:** raise contrast to max (0xFF) and set the pre-charge period for short outdoor wakes. Use big, bold icons (≥ 2 px strokes). Lifetime and current go up with brightness, but wakes are seconds long.

## 6. Bench work

1. Buy 3 different bare 0.49" panels plus their breakouts.
2. For each panel, measure:
   - current per icon at 3 contrast settings;
   - luminance (cd/m²) with a luminance meter;
   - off-state leakage with the topology above.
3. Confirm the driver IC and the init sequence; write the driver once for both SSD1306 and SSD1315.
