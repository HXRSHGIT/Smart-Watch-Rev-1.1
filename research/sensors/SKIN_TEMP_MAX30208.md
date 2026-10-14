# Skin Temperature — MAX30208 Thermal Path

Brief §4.1: "Skin-temperature trend measurement. The product should distinguish trend tracking from core body-temperature measurement."
Brief §8, MAX30208: "Requires a skin-facing thermal path isolated from PCB and battery heat."

---

## 1. The sensor

| Item | Value | Source |
|---|---|---|
| Type | **Contact** digital temperature sensor (silicon bandgap). It measures its own die temperature, which you make equal to the skin by conduction. It's **not** an infrared sensor | [ADI MAX30208](https://www.analog.com/en/products/MAX30208.html) |
| Accuracy | ±0.1 °C 30–50 °C · ±0.15 °C 0–70 °C | [datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX30208.pdf) |
| Resolution | 0.005 °C (16-bit) | same |
| Package | thin LGA-10, 2 × 2 × 0.75 mm | same |
| Current | 67 µA while converting, 0.5 µA standby | same |
| Extras | 32-word FIFO, high/low alarms, 2 GPIO, I²C | same |

**The chip is ±0.1 °C. Whether the product is ±0.1 °C or ±1 °C depends entirely on the mechanics.** The die reads whatever its package is coupled to: skin, PCB, battery, LED, or room air.

## 2. Heat sources in a band

| Source | Power | When |
|---|---|---|
| nPM1300 while charging | ≈ 0.14 W (power-battery POGO §5) | docked: off-wrist, ignore |
| PPG LEDs | ≈ 3 mW at the highest setting | always |
| SoC radio and CPU bursts | mW average, short peaks | always |
| LRA | short bursts | events |
| Battery | small in discharge at these currents | always |
| Ambient air on the outer face | room → sun | always, often the biggest disturbance |
| **Skin** (the signal) | ≈ 30–36 °C at the wrist, varies with blood flow | worn |

## 3. Thermal design

```
     outer housing (air side)
   ┌──────────────────────────────────┐
   │ main PCB (SoC, PMIC, battery…)   │   ← keep heat here
   │      │ low-conductance link       │
   │  ┌───┴──────────┐  thin flex tail or isolated PCB island
   │  │ MAX30208     │
   │  │ thermal vias │
   │  └──────┬───────┘
   │   metal contact (stainless / Ti pad), flush with skin face, low thermal mass
   └──────────┼───────────────────────┘
            skin
```

Rules:

1. **High conductance to the skin.** Put a small **metal contact pad** in the skin face (e.g. Ø 3–4 mm stainless insert), bonded to the sensor's exposed side or to a copper island under it with thermal vias. Use thermal paste or a pad in between, never an air gap.
2. **Low conductance to everything else.** Use a flex tail or a narrow-necked PCB island (thin traces, no copper pour connection) between the sensor island and the main board. Keep it away from the PMIC and battery.
3. **Low thermal mass** on the sensor island, so it follows the skin quickly (time constant ≈ tens of seconds to a few minutes, to measure).
4. **Skin contact:** the pad must touch the skin through all strap positions. Put it next to the PPG dome, which already presses into the skin.
5. **Insulate from ambient:** no metal path from the pad to the outer housing.

### Second sensor for compensation (recommended)

Add a **second, cheap temperature reading on the main board** (the nRF's internal TEMP peripheral or the BMP390's temperature). With two points (skin-side and board-side), firmware can estimate and remove heat leaking from the board. That's the standard "dual-sensor" trick for wearable skin temperature. The MAX30208's 32-word FIFO and alarms aren't needed for that, but don't hurt.

## 4. Trend vs core temperature (brief requirement)

- **Wrist skin temperature isn't core temperature.** It's typically several °C lower and changes with room temperature, blankets, blood flow and exercise.
- **Products that track it** (e.g. WHOOP, Oura) report a **deviation from the user's own baseline**, measured during sleep, when conditions are most stable. They don't report an absolute body temperature.
- **For this band:**
  - **Take the nightly value:** median of sleep-period readings, with the first 30–60 min after sleep onset excluded (settling).
  - **Show deviation** from a rolling ≈ 2-week baseline in °C, e.g. "+0.4 °C vs your normal".
  - **Never show a "fever" number,** and never claim core temperature.

**Wording:** "Skin temperature trend, relative to your baseline. Not body temperature. Not a thermometer."

## 5. Tests (§13 "Temperature response and separation from internal heat sources")

1. **Step response:** band from 22 °C air onto a 34 °C controlled hot plate with a skin-like interface. Record the time to 63 % and 90 %.
2. **Internal heat isolation:** on the hot plate at 34 °C, run worst-case internal load (PPG max, BLE streaming, LRA every 10 s) for 30 min. Sensor offset must stay below 0.1–0.2 °C (proposed).
3. **Ambient sensitivity:** on the plate, change room air from 18 → 28 °C. Measure the reading change. This is the coefficient the dual-sensor compensation removes.
4. **Wrist nights:** 10 people × 5 nights, with a reference skin thermistor taped next to the band. Compare night-median deviations.
