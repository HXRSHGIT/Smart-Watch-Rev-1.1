# Optical Mechanical Design — Spacing, Barriers, Window, Contact

Brief §13: "Optical crosstalk, ambient light, fit and skin-contact testing."
Brief §8: "Validate detector spacing… crosstalk."

---

## 1. Light paths

```
         skin / tissue
   ┌───────────────────────────────┐
   │   ↗ (1) useful: through tissue│ ↘
 LED ─► (2) light-piping inside the cover window ─► PD   ← crosstalk
   │   (3) reflection off the skin surface        ─► PD   ← crosstalk (no pulse)
   │   (4) ambient light leaking at the edges     ─► PD   ← noise
```

Only path (1) carries the pulse. Paths (2)–(4) add DC, which eats the ADC range and adds noise, but carries no heart signal. **Most "bad PPG" products fail on path (2)**: one continuous clear window across LED and PD.

## 2. Rules

| Rule | Why |
|---|---|
| **Separate windows** (or separate inserts) over the LED and each PD, with opaque material between them through the **full cover thickness** | blocks path (2) |
| **Opaque barrier wall** between LED and PD from the PCB up to the cover, black, matte, IR-opaque (many black plastics are **IR-transparent**; check at 940 nm) | blocks the in-housing path |
| Cover as **thin** as practical over the optics (≈ 0.3–0.8 mm) | less lateral piping, less loss |
| LED and PD **flush with the cover**, or a thin index-matched fill in between | less air-gap scatter |
| **Raised optical dome** pressing into the skin (WHOOP-style sensor boss) | improves contact and blocks surface path (3) and ambient (4) |
| Black **gasket/foam** around the optical island to the housing | ambient (4) |
| No **white or shiny** materials near the optics (white FR-4, silkscreen, ENIG pads) | cover them with black mask or ink |

## 3. Emitter–detector spacing

Light at each wavelength travels a typical "banana" path. Wider spacing looks deeper but returns less light.

| λ | Penetration | Typical wrist-device spacing (design starting point) |
|---|---|---|
| Green 530 nm | shallow, high absorption: capillary bed, good for HR, little motion artifact | ≈ 2–4 mm |
| Red 655 / IR 940 nm | deep, low absorption: arteriolar, needed for SpO2 | ≈ 4–7 mm |

These ranges are starting points from common practice. **Optimise them with a test board** (§5). They aren't datasheet values.

### Layout with one SFH 7016 and two VEMD8080

```
   [VEMD8080 #1]        [SFH 7016]        [VEMD8080 #2]
   4.8 × 2.5 mm    ←d1→  1.85 × 1.65  ←d2→  4.8 × 2.5 mm
   long axis across the band
```

- **Symmetric (d1 = d2):** two equal channels. Gives diversity against local poor contact, and averaging for SNR.
- **Asymmetric (d1 ≈ 3 mm, d2 ≈ 6 mm):** the near PD is optimised for green HR, the far PD for red/IR SpO2. This is the better choice for SpO2. **Recommended starting point.**

The optical island is then roughly 4.8 + 3 + 1.85 + 6 + 4.8 ≈ **20 mm** long. That fits along the band axis of a ≈ 22 × 35 mm pod, but it's a large share of the bottom face. The MAX30208 contact and the pogo pads also need room on that face. See validation MECHANICAL_STACKUP.

## 4. Window material

| Material | Transmission | Hardness | Note |
|---|---|---|---|
| PC (polycarbonate) | ≈ 88–90 % visible (typical) | soft, needs hard-coat | easy to mould, two-shot black + clear possible |
| PMMA | ≈ 92 % (typical) | scratches | cheap |
| Glass / chemically strengthened | ≈ 91–92 % (typical) | hard | separate inserts glued in |
| Sapphire | ≈ 85 % uncoated (high index → more reflection) | hardest | cost; AR-coat both sides |

Typical-class transmission figures; confirm with the moulder's material data.

**Recommendation:** two-shot moulded PC (black body + clear windows), hard-coated. Or glass inserts in a black housing. **Either way the windows are separate.**

## 5. Test plan (§13)

1. **Spacing test board:** a flex with the SFH 7016 and VEMD8080s at 2, 3, 4, 5, 6, 7 mm, driven by a MAX86141 EVKIT. Measure perfusion index (AC/DC) for G/R/IR on 10 people at rest. Pick d1 and d2.
2. **Crosstalk:** band on a **black, non-reflective target** (or in air in a dark box). Any signal is crosstalk. Target: crosstalk DC < 5–10 % of on-wrist DC (proposed). Repeat on a skin phantom.
3. **Ambient:** on-wrist under 0 / 500 / 10,000 / ~50,000 lux (sun). Check ALC headroom, ADC never saturated, HR error vs ECG chest strap.
4. **Fit:** strap tension at 3 settings (loose / normal / tight) × wrist sizes. Measure perfusion index and HR error. Define "normal" for the user guide.
5. **Skin tones:** run tests 1–4 across Monk Skin Tone groups (see SPO2.md §4).
