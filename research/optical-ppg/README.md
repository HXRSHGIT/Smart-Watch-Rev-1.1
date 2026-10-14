# R&D — Optical PPG (HR and SpO2)

Branch `rnd/optical-ppg`. Covers brief §4.1 (HR, SpO2), the optical rows of §8, and the optical rows of §13.

| File | What it answers |
|---|---|
| [PPG_FRONTEND.md](PPG_FRONTEND.md) | Verified part data; logic level, LED supply, thermal, timing, saturation, assembly; sample rates; register starting plan |
| [OPTICAL_DESIGN.md](OPTICAL_DESIGN.md) | Light paths, barrier and window rules, emitter–detector spacing, window materials, test plan |
| [SPO2.md](SPO2.md) | Ratio-of-ratios, why the wrist is hard, realistic accuracy, skin-tone evidence and FDA study design, validation stages, claim wording |
| [HR_MOTION_ARTIFACT.md](HR_MOTION_ARTIFACT.md) | Motion artifacts, algorithm options, public datasets, P0 accuracy targets, HR zones |

## Key findings

1. **The MAX86141 is a 1.8 V SPI part.** Run the SoC I/O at 1.8 V, so no level shifters are needed.
2. **The LED supply needs ≥ 3.1 V plus green Vf headroom**, so it has to come from VBAT or a boost. Measure the dropout on the bench.
3. **LED heating is negligible** (≈ 3 mW, < 1 K) at even the highest planned PPG setting. Battery is the cost, not heat.
4. **The hardware already supports P1 HRV and respiration:** 100 sps + peak interpolation gives ≈ 1–2 ms beat timing.
5. **Optics decide quality more than the AFE does.** Use separate windows, IR-opaque barriers, a raised dome, and asymmetric spacing (near PD for green, far PD for red/IR). Set the spacing with a test board.
6. **SpO2:** spot and sleep estimates are feasible; medical accuracy isn't a P0 goal. Skin-tone bias is documented (Sjoding 2020), so validate per Monk group + ITA, following FDA's 2025 draft study design.
7. **HR in motion:** the realistic bar is what commercial devices achieve (median error ≈ 2–6 %). Use a TROIKA-style tracker + confidence score, and develop it on IEEE SPC 2015 and PPG-DaLiA before hardware exists.

## Decisions for the client

- Is SpO2 only "estimate during sleep plus spot check", or will they ever want a stronger claim? A stronger claim needs a desaturation lab study (cost and time).
- Which skin-tone coverage is required in their internal validation?

## Next experiments

1. Spacing test board on a MAX86141 EVKIT: perfusion index vs distance, 10 people.
2. PVLED dropout sweep.
3. Algorithm work on public datasets now; on own data from P0.

Done by Harsh Thakur.
