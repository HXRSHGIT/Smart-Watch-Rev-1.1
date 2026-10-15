# P1 Features — What They Need and What Not to Claim

Brief §5:
- HRV trends after beat-to-beat timing quality is validated
- Respiratory-rate estimation during sleep
- Recovery/readiness and stress estimates
- More exercise categories, from labelled user data
- Phone-assisted GPS routes and pace
- Fall-event research, with no emergency claim
- User-configurable reminder icons and vibration patterns
- Data export and user-controlled deletion

---

## 1. HRV trends

- **Metric:** RMSSD (root mean square of successive differences between beats), computed **during sleep only**, in stable 5-minute windows. Report the nightly median.
- **Timing quality:** RMSSD at rest is often only tens of milliseconds, so beat-timing error has to be well below that.
  - Use 100 sps + peak interpolation (≈ 1–2 ms).
  - Reject windows with motion, low signal quality, or ectopic-like intervals (differing by > 20 % from their neighbours).
- **Validation gate (brief: "after beat-to-beat timing quality is validated"):**
  - Overnight comparison with ECG R-R intervals (chest strap or Holter).
  - Report per-beat timing error and RMSSD agreement (Bland-Altman).
  - Ship only when agreement is within a pre-set limit.
- **Trend, not absolute:** show HRV as a deviation from the user's own baseline. HRV varies hugely between people.

## 2. Respiratory rate (sleep)

- **Three ways breathing shows up in PPG:**
  - respiratory-induced **intensity** variation (baseline);
  - **amplitude** variation;
  - **frequency** variation (respiratory sinus arrhythmia in the beat intervals).
- **How to combine them:** estimate the rate from each of the three and fuse them. Charlton et al. (Physiol Meas 2016) benchmarked many such algorithms on ECG and PPG; use their findings to choose the method.
- **When:** sleep only, still windows, reported as a nightly average. Typical adult sleeping rate is ≈ 12–20 breaths/min.

## 3. Recovery / readiness / stress

These are **composite scores**, not measurements. A typical recipe:

```
readiness = f( HRV vs baseline, resting HR vs baseline, sleep duration vs need,
               skin-temp deviation, previous day's training load )
```

- **Any weighting is a product decision** and must be disclosed as such.
- **Stress (daytime):** HRV is noisy while awake and moving. Daytime stress scores should only use still periods, and should be labelled "body stress estimate".
- **No health claims:** never tie a score to illness detection (that would fall outside the wellness position, see validation COMPLIANCE).

## 4. More exercise categories

These come from the labelled-data loop in ACTIVITY.md §5–6. Users confirm their "generic workouts", and that grows the dataset. Retrain the model, ship it via DFU, and measure on held-out users.

## 5. Phone-assisted GPS

- The phone records the route and pace. The band adds HR and cadence.
- The band never needs a GPS receiver.
- **Side benefit:** GPS sessions calibrate the step-length model (ACTIVITY.md §2).

## 6. Fall events — research only

- **Detection approach:** free-fall phase, then impact (high peak acceleration), then lying still / orientation change.
- **Accelerometer setting:** needs ±16 g and ≥ 100 Hz in the detection window.
- **Main risk:** false positives from sitting down hard, dropping the arm, sports.
- **Brief's rule:** research only, **no emergency claim**. A product that implies it calls for help when it can't creates real safety and liability risk. If emergency alerting is ever wanted, it is a separate, regulated-grade project.

## 7. User-configurable icons and patterns

- **Icons:** store 1-bit icons (e.g. 32×32 = 128 bytes each) in the external flash "spare" partition. Sync from the app.
- **Haptic patterns:** DRV2605L sequences (a few bytes each).
- **Hardware impact:** none.

## 8. Data export and deletion

- **Export:** the app exports the user's data (CSV/JSON).
- **Delete on the band:** erase the summary log partition and the bonds; factory-reset the keys.
- **Delete in the cloud:** if a cloud exists, delete there too.
- **Privacy law:** relevant to GDPR / India DPDP Act-style obligations (see validation COMPLIANCE).
