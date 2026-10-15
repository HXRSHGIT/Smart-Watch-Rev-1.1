# Reversible Two-Contact Pogo Charging

Brief §4.7: "Protected, reversible two-contact pogo charging input." "Safe behavior with reversed pogo orientation, contact bounce, shorts and poor contact resistance."
Brief §4.6: "Pogo charging contacts are not required to provide consumer USB data."

---

## 1. Why reversible

With two round pads, the user can drop the band on the dock either way round. The band must therefore accept **+5 V on either pad**.

## 2. Options to fix orientation

| Option | Loss at 150 mA | Parts | Comment |
|---|---|---|---|
| Schottky diode bridge (4 diodes) | 2 × Vf ≈ 0.6–0.8 V | 4 small diodes or 1 bridge array | Simple, but VBUS at the nPM1300 can drop below its 4.0 V start threshold when the dock is at 5.0 V minus cable and contact loss |
| MOSFET ("active") bridge | ≈ 2 × I × RDS(on), tens of mV | 2 N + 2 P FETs, or an integrated active bridge | Low loss, more parts |
| **ST OCVPB21-13F6** (brief's candidate) | Datasheet value needed | 1 WLCSP-13, 0.4 mm pitch | Integrated rectifier bridge, ±15 kV contact ESD, OVP to ±13 V, adjustable OCP 100–500 mA, controlled inrush ([ST](https://st.com/resource/en/datasheet/ocvpb21-13f6.pdf), [ST product page](https://www.st.com/ja/protections-and-emi-filters/ocvpb21-13f6.html)) |

**Check with the OCVPB21 datasheet:** the voltage drop of its bridge at the planned charge current. nPM1300 VBUS must **start above 4.0 V** and keep **above ≈ 3.6 V** (≈ 400 mV hysteresis) ([Nordic DevZone](https://devzone.nordicsemi.com/f/nordic-q-a/121139/npm1300-vbus-running-on-4v/533730)).

**Budget from a 5.0 V dock:**
- 2 pogo contacts ≈ 2 × 50 mΩ;
- dock cable ≈ 0.1–0.3 Ω;
- the bridge drop.

At 150 mA the contacts and cable cost ≈ 50 mV. So the bridge may drop ≈ 0.8 V and still leave > 4.0 V. **Use a 5.0–5.2 V dock supply**, not a "5 V-ish" USB port through a thin cable.

**Recommendation:** keep the OCVPB21. It covers orientation, ESD and over-current in one 13-bump part. Its data-mux half goes unused because the brief drops USB data. Compare it with ST's OCVPB22-14F6 sibling before freeze ([ST](https://www.st.com/en/protections-and-emi-filters/ocvpb22-14f6.html)).

**Limit to note:** the OCVPB21 is rated **−30 to +65 °C**. That's fine for charging indoors, but write it into the product spec.

---

## 3. Fault cases from the brief

| Case | What happens | Design answer |
|---|---|---|
| Reversed orientation | Bridge re-routes | OCVPB21 |
| Contact bounce while docking | VBUS toggles fast; charger restarts | OCVPB21 controlled inrush + nPM1300 VBUS hysteresis. Add firmware debounce (≥ 500 ms) before showing "charging" |
| Short across the pads (wet dock, coin, metal strap clasp) | Dock sees a short. The band's pads must not short the cell | Cell never reaches the pads: the bridge and charger are one-way. Check bridge reverse leakage. Dock needs its own current limit |
| Overvoltage (wrong adapter, 9–12 V) | | OCVPB21 OVP to ±13 V. nPM1300 VBUS operating max is 5.5 V, so the OVP threshold must sit below that (check the OCVPB21 OVP trip level) |
| Poor contact resistance (dirt, wear) | VBUS sags → slow or stop-start charge | nPM1300 VBUS current limit + charger adapts. Firmware warns "clean contacts" if VBUS flaps > N times/min |
| ESD on exposed pads | ±8 kV contact / ±15 kV air during use | OCVPB21 rated ±15 kV contact on the bridge inputs |

---

## 4. Sweat and corrosion — the long-term risk

The pads are exposed to sweat (salty, slightly acidic) all day.

- **Don't put any DC bias on the pads while worn.** With the bridge input floating when undocked, the pads carry no voltage, so there's no electrolytic corrosion cell. **Verify** with the band powered: measure pad-to-pad and pad-to-GND voltage and leakage.
- **Pad finish:** hard gold over nickel on the band-side contacts (≥ 0.75 µm Au is the usual wear-grade figure; confirm with the contact vendor). Alternatively, stainless-steel pins insert-moulded into the housing (common in fitness bands).
- **Seal:** the pad-to-housing seal is part of the IP rating. Test it in validation (IPX7/IPX8 + artificial sweat per ISO 3160-2 / EN 1811 style tests, see validation/COMPLIANCE.md).

---

## 5. Charge settings

- **Charge current:** set by the cell datasheet, typically 0.5–1C. For 150 mAh that's **75–150 mA**: about 2 h at 0.5C, about 1–1.5 h at 1C to ~100 %.
- **Termination:** 4.20 V, or 4.35 V for an HV cell. The nPM1300 supports 3.50–3.65 and 4.00–4.45 V in 50 mV steps.
- **JEITA:** the nPM1300 reduces current or voltage with the NTC. Charge only between 0 and 45 °C (typical Li-ion; take the cell's numbers).
- **NTC:** 10 kΩ in the pack, wired to the nPM1300 NTC pin (supports 10 k / 47 k / 100 k). The NTC must sit on the cell, not on the PCB.
- **Heat:** linear charging dissipates (VBUS − VBAT) × I ≈ (4.6 − 3.7) × 0.15 ≈ **0.14 W** in the nPM1300. That's small, but it sits next to the skin-temperature sensor. **Ignore skin temperature while charging** (the band is off-wrist anyway).

## 6. Bench tests (§13 "pogo orientation, contact resistance, charging current and temperature")

1. Dock 100× in each orientation. Charge must start every time within 1 s.
2. Insert 0.5 / 1 / 2 Ω in series to emulate dirty contacts. Charge should continue at reduced current with no stop-start loop.
3. Apply 9 V and 12 V to the pads: no damage, OVP latches.
4. Short the pads while undocked and worn: no current from the cell.
5. Thermal camera during a full charge: hottest point < 45 °C at 25 °C ambient (proposed limit).
