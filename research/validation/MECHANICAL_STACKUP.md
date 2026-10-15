# Mechanical Stack-Up, Board Outline and Placement

Brief §15 step 4: "Mechanical and RF definition: enclosure stack, optical system, thermal path, vent, PCB outline, stackup and antennas."

Every dimension here is a **planning estimate**, to be replaced by the industrial designer's CAD. The purpose is to show what fits and what fights for space.

---

## 1. Size class

The brief asks for "small, light… not the large face, weight or interaction model of a smartwatch" and a WHOOP-like form. Plan for a pod of roughly:

> **≈ 35 × 25 mm footprint, ≈ 9–11 mm thick (including the sensor dome)**

Reported dimensions of current WHOOP-class pods are in this range; confirm against a measured sample. The strap adds no electronics.

## 2. Vertical stack (centre of the pod)

| Layer (top = away from skin) | Thickness | Notes |
|---|---|---|
| Top cover / display window | 0.6–0.8 mm | Glass or hard-coated PC; dead-front ink or tint for Stealth |
| Display (bare 0.49" COG panel) | ≈ 1.2 mm | Plus ≈ 0.1 mm foam/adhesive |
| Battery | 3.0–4.0 mm | 150–250 mAh pouch, plus 8–10 % swelling allowance (power-battery BATTERY_LIFE §6) |
| Battery-to-PCB foam / insulator | 0.2–0.3 mm | |
| Main PCB | **0.6–0.8 mm** | 4–6 layer HDI. A 1.6 mm board would waste ≈ 1 mm |
| Tallest bottom-side parts | ≈ 1.0 mm | most ICs ≤ 0.8 mm; LRA sits beside, not under |
| Back housing + optical windows | 0.8–1.0 mm | Two-shot black + clear, or glass inserts |
| Sensor dome protrusion | 0.5–1.0 mm | Presses optics and temperature pad into the skin |
| **Total** | **≈ 8.0–10.8 mm** | |

**Thickest part:** the battery. The cell capacity chosen by the client (5 vs 7 days, adaptive vs continuous PPG) moves the pod by about 1 mm.

The LRA (Ø8 × 3.2 mm coin) can't go under the battery and the board without adding 3 mm. **It has to sit beside the battery** in its own pocket, which uses ≈ 9 × 9 mm of the footprint.

## 3. Footprint allocation (≈ 35 × 25 mm)

```
 ┌─────────────────────────────────────────────┐
 │ ANTENNA END   (clear of metal, ≈ 6–8 mm)    │  ← top end of pod
 ├─────────────────────────────────────────────┤
 │ SoC + crystal + RF match │ PMIC + bucks     │
 │ flash                    │ (inductors)      │
 ├──────────────────────────┴──────────────────┤
 │        BATTERY (≈ 25 × 20 mm, above PCB)    │
 │                                             │
 │  bottom side:  [PD1]──[SFH7016]────[PD2]    │  ← optical island ≈ 20 mm long
 │                 MAX86141   MAX30208 pad     │
 ├─────────────────────────────────────────────┤
 │ LRA pocket │ pogo pads │ BMP390 + vent side │  ← bottom end
 └─────────────────────────────────────────────┘
```

Placement rules this follows:

- **Antenna** at one end, away from the battery, LRA and pogo pads (mcu-ble ANTENNA_RF).
- **Optical island** in the centre of the skin face, under the dome (optical-ppg OPTICAL_DESIGN).
- **Skin-temperature pad** next to the optics, thermally isolated from the PMIC (sensors SKIN_TEMP).
- **Pogo pads** at the opposite end from the antenna.
- **Pressure vent** on a side face, not the skin face (sensors PRESSURE_BMP390).
- **Display** on top, centred, so it reads well when the wrist is turned.

## 4. PCB technology

| Choice | Why |
|---|---|
| 4–6 layers, 0.6–0.8 mm thick | Thickness budget; ground plane under the RF and AFE |
| HDI microvias (1+N+1) | Needed for the nRF54L15 CSP and the MAX86141 0.4 mm WLP |
| Rigid board + flex tail(s), or rigid-flex | A flex tail can carry the temperature island and/or the display connection. Rigid-flex costs more but removes connectors |
| ENIG finish | Flat pads for WLP/CSP; also used on pogo landing pads (contacts themselves are separate parts) |

**Get a stack-up from the chosen fab early.** The 50 Ω RF line width depends on it (≈ 0.18–0.2 mm on thin dielectric, ANTENNA_RF §3).

## 5. Weight (rough)

| Part | Mass |
|---|---|
| Battery 150–250 mAh | ≈ 3.5–5.5 g (typical small pouch, unverified) |
| PCB + parts | ≈ 2–3 g |
| Housing + windows | ≈ 4–7 g (material-dependent) |
| LRA, display, contacts | ≈ 1.5 g |
| **Pod** | **≈ 11–17 g** |
| Strap | depends on material |

## 6. Open items for the industrial designer

1. Pod outline, thickness and curvature (a curved back helps optical contact on the wrist).
2. Housing material. Avoid metal or carbon-filled plastic near the antenna end.
3. Pogo contact type and sealing. Vent location. Window construction for both variants.
4. Strap attachment and how the pod sits on the wrist bone (this affects PPG and temperature contact).
