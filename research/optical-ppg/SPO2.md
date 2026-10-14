# SpO2 on the Wrist — Method, Limits, Validation, Claims

Brief §4.1: "Spot SpO2 measurement and power-managed periodic sampling during selected sleep periods."
Brief §3: SpO2 "must be presented as estimates."
Brief §13: "SpO2 evaluation against an appropriate reference across realistic conditions."

---

## 1. Principle

- **What's measured:** oxygenated and deoxygenated haemoglobin absorb red (≈ 660 nm) and infrared (≈ 940 nm) light differently. Each wavelength gives a pulsatile part (AC, from arterial blood) on top of a steady part (DC, tissue + venous).
- **Ratio of ratios:**

```
          AC_red / DC_red
    R = ───────────────────
          AC_ir  / DC_ir

    SpO2 ≈ a − b·R        (or a quadratic a + b·R + c·R²)
```

- **Calibration:** **a, b, c are not physics constants.** They depend on the optics: LED wavelengths, spacing, window, skin site. They must be **found empirically** on this exact hardware, against arterial blood (SaO2) or at least a reference finger oximeter.

## 2. Why the wrist is hard

| Issue | Effect | Mitigation |
|---|---|---|
| **Low perfusion** at the wrist (reflectance, not transmission through a finger) | Red/IR AC is small, often < 1 % of DC → noisy R | Longer averaging (30–60 s windows), larger red/IR spacing (OPTICAL_DESIGN §3), stillness gating |
| **Motion** | Corrupts AC far more than the HR algorithm can tolerate | Measure only when the accelerometer says still. The brief's "sleep periods" and "spot" modes fit this naturally |
| **Venous pulsation, pressure from strap** | Shifts R | Consistent strap fit. Reject windows with an abnormal red/IR waveform shape |
| **Temperature** | Red LED output −0.7 %/K, centroid shifts 0.18 nm/K ([SFH 7016 DS](https://look.ams-osram.com/m/566c673078988944/original/SFH-7016.pdf)) | Calibrate over skin-temperature range. Log the MAX30208 reading alongside each SpO2 window |
| **Skin pigmentation** | See §4 | Study design + auto-ranged LED current |
| **Ambient light** | Adds DC | ALC + light seal |

## 3. Realistic accuracy

- **Medical bar:** finger pulse oximeters cleared for medical use are tested to ISO 80601-2-61. The usual accuracy figure is **Arms ≤ 4 %** over 70–100 % SaO2 (ISO's maximum; FDA has historically expected tighter values). **This product isn't claiming that.**
- **What's realistic here:** for a reflective wrist device in a wellness product, the honest targets are **trend and spot estimates at rest, best during sleep**. Expect accuracy to degrade at low saturation and with motion. Set the internal target only after the first calibration study.

### Wording the client can use (§3 "presented as estimates")

> "Blood-oxygen estimate. Not a medical device. Not for diagnosing or monitoring any disease. Readings can be affected by movement, fit, skin temperature and skin tone."

## 4. Skin tone — a known, documented problem

- **Sjoding et al., NEJM 2020:** among patients whose pulse oximeters read 92–96 %, arterial saturation was below 88 % in **11.7 % of Black patients vs 3.6 % of White patients** in the Michigan cohort. That's about three times the rate of hidden low oxygen (occult hypoxemia). ([summary, AHRQ PSNet](https://psnet.ahrq.gov/issue/racial-bias-pulse-oximetry-measurement))
- **FDA draft guidance, January 2025** (for medical pulse oximeters):
  - ≥ 150 participants;
  - ≥ 25 % with darker skin;
  - skin tone recorded with **both** the **Monk Skin Tone (MST) scale** (subjective) **and** the **Individual Typology Angle (ITA)** measured with a colorimeter (objective).
  
  ([TCTMD news](https://www.tctmd.com/news/fda-issues-draft-guidance-improving-skin-tone-disparities-pulse-oximeters), [draft PDF via HHS](https://www.hhs.gov/guidance/sites/default/files/hhs-guidance-documents/FDA/pulse-oximeters-for-medical-purposes-draft-guidance_0.pdf.pdf))
- **Heart rate is different:** Bent et al., npj Digital Medicine 2020, found **no significant HR accuracy difference across skin tones**. It did find **activity raised absolute error by ~30 %** against rest. ([PubMed](https://pubmed.ncbi.nlm.nih.gov/32047863/))

**Even as a wellness product**, follow the FDA study design for internal validation:

- record MST + ITA;
- report SpO2 error **per skin-tone group**;
- don't ship a feature whose error is materially worse for darker skin.

This protects users and the client's reputation.

## 5. Validation plan

| Stage | Reference | Who | What it gives |
|---|---|---|---|
| A. Bench | Optical phantom / simulator for red/IR ratio | none | AFE and timing check only. Phantoms don't validate calibration |
| B. Room-air spot checks | Cleared finger pulse oximeter on the same arm | 20–30 people, all MST groups | Bias near 95–99 %; repeatability; detects gross errors |
| C. Sleep nights | Cleared finger oximeter with logging (overnight) | 10–20 nights | Trend agreement, dropout rate |
| D. Calibration study (desaturation) | Arterial blood gas (SaO2) during controlled hypoxia, 70–100 % | Specialised clinical lab, 150+ for FDA-style | The only way to fit a, b, c properly and know accuracy at low SpO2 |

**For P0:** B and C. Fit a provisional curve from stage B/C and published reflectance data.

**Before any claim beyond "estimate":** budget for D. It's a contracted study at a hypoxia lab with a meaningful cost and lead time. Get a quote.

## 6. Power

Red + IR windows at 100 sps: ≈ 16–31 µA day-average for 48–96 min per night (power-battery model). That's small. **SpO2 cadence is a free choice from a battery standpoint.** The limit is accuracy (stillness windows).
