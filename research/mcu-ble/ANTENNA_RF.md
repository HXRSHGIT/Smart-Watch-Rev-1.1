# 2.4 GHz Antenna on a Wrist Band

Brief §13: "BLE range, connection reliability and antenna tuning in the final worn enclosure."
Brief §15 step 4: "Mechanical and RF definition: … PCB outline, stackup and antennas."

---

## 1. The real problem

A wrist band is close to the worst place for a 2.4 GHz antenna:

1. **Tissue absorbs and detunes.** The wrist sits 1–5 mm from the antenna. Muscle and skin are lossy at 2.4 GHz (high permittivity, high conductivity), so efficiency drops and resonance shifts down in frequency. On-body losses of **≈ 5–15 dB** against free space are commonly reported for wrist-worn devices (range from published body-area-network studies; measure ours).
2. **The board is tiny.** A chip antenna needs a ground plane of roughly a quarter wavelength (≈ 30 mm at 2.45 GHz) along one edge to work as specified. The band PCB is ≈ 20–25 mm wide.
3. **The battery is a metal plate** a few mm away.

So the antenna has to be chosen, placed and tuned for **the device on a wrist**, not on a bench.

---

## 2. Options

| Option | Size | Pros | Cons |
|---|---|---|---|
| **Ceramic chip antenna**, e.g. Johanson 2450AT18A100 | 3.2 × 1.6 × 1.3 mm (EIA 1206) | Small, documented. 0 dBi typ, 74 % efficiency on the eval board | Needs a corner clearance and a ground plane bigger than ours; must be retuned |
| **PCB trace antenna** (meandered IFA) | ≈ 5 × 12 mm board edge | Zero BOM cost, tunable by trimming | Uses board area along one edge, which is the scarcest area here |
| **Booster / "ground-plane-excited" chip** (e.g. Ignion mXTEND class) | ≈ 7 × 3 mm | Uses the ground plane as the radiator, made for small boards | Matching network more complex; vendor design support needed |
| **Metal enclosure part or flex as the radiator** | 0 extra area | Best efficiency if the housing has metal | Needs RF and mechanical co-design; not for P0 |

Johanson 2450AT18A100 data: [Johanson datasheet Rev 4.0](https://www.johansontechnology.com/docs/3827/Antenna-2450AT18A0100001E-Rev4.0.pdf), summary on [everythingrf](https://www.everythingrf.com/products/all-antennas/johanson-technology/741-65-2450at18a100). Its recommended placement is a PCB corner.

**Recommendation for P0:** a chip antenna at the board end **furthest from the battery**, pointing out of the band and away from the wrist. Put a 3-element **π matching network** (0402 footprints) right at the feed. Fit a ceramic and a booster type on two variants of the first spin if the board allows it. Antenna choice is the classic "only the measurement knows" item.

---

## 3. Layout rules

- **Clearance:** follow the chosen antenna's own datasheet. Typically a copper-free area of a few mm around the antenna on **all layers**, at a board corner or edge. Don't use a generic rule.
- **Ground:** the ground plane is half of the antenna. Keep it solid and continuous back from the clearance, with stitching vias around the edge.
- **Feed:** 50 Ω grounded coplanar waveguide from the SoC's matching to the antenna match, as short as possible. With a 4-layer 0.8 mm board and ~0.1 mm L1–L2 prepreg, a 50 Ω microstrip is only ≈ 0.18–0.2 mm wide. Get the fab's impedance calculator to confirm.
- **SoC matching:** keep the Nordic reference matching network between the RF pin and the 50 Ω line exactly as in the reference layout. The antenna match is a **separate**, second network.
- **No metal near the clearance:** no battery, LRA, screws, pogo contacts or display FPC.
- **Noisy sources:** keep the buck inductors and the OLED charge-pump caps away from the antenna end.

---

## 4. Tuning procedure

1. **Bare board, free space.** VNA, a pigtail soldered at the match (cut trace or U.FL test footprint). Tune the π network for S11 ≤ −10 dB across 2400–2483.5 MHz.
2. **In the housing, on a wrist phantom** (or a real wrist with the VNA cable dressed along the arm). Expect resonance to drop by tens of MHz. Re-tune the π network values; the PCB doesn't change. Common practice is to **tune slightly high in free space** so the body pulls it back into band.
3. **Lock the values** for the build and record S11 on 5 boards to see the spread.
4. **Radiated check:** measure TRP, or as a proxy, RSSI at 1 m and 3 m from a reference receiver in 4 orientations, with the band on a wrist. Compare with a known good nRF DK.

---

## 5. Link budget

| Item | Value |
|---|---|
| TX power | 0 dBm default. nRF54L15 can go to +7/+8 dBm |
| Antenna + body loss (on wrist) | −10 dB (planning value) |
| Phone RX sensitivity, 1M PHY | ≈ −90 to −95 dBm (typical phone, unverified) |
| Path loss at 10 m, 2.45 GHz, free space | ≈ 60 dB |
| Extra margin for the body between band and phone | 10–20 dB |
| **Received at 10 m, 0 dBm** | 0 − 10 − 60 − 15 = −85 dBm → **≈ 5 dB margin over −90 dBm, tight** |

**Conclusion:** at 0 dBm, a pocket-to-wrist link is fine, but across a room with the body in the way it's marginal. Plan on **+4 to +8 dBm** for reconnect and sync. This is one place the nRF54L15's higher maximum power earns its keep: 4 dB ≈ 1.6× range. Bursts are short, so the battery cost is small.

---

## 6. SAR / RF exposure

- At ≤ 10 mW (+10 dBm) and low duty cycle, a BLE wearable normally falls under the low-power exemption thresholds (FCC §1.1307(b)(3), EU EN 62479).
- Confirm with the test lab at pre-scan. Don't assume, because the wrist is a limb (extremity limits are higher).

## 7. Open items

- Pick 2 antenna types for the first spin. Ask Johanson and Ignion for application support on a ≈ 22 × 35 mm board.
- Get the housing material early. A painted metal coating or carbon-filled plastic near the antenna is a show-stopper.
- Decide whether the pogo contacts can sit at the other end from the antenna. They should.
