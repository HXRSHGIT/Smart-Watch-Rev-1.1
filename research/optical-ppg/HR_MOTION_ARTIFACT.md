# Heart Rate Under Motion

Brief §4.1:
- "Continuous and resting heart-rate measurement."
- "Workout heart rate and configurable heart-rate zones."
- "Time synchronization across PPG, motion and other sensors where required for motion-artifact reduction."

---

## 1. The problem

During walking or running:

- **Arm swing changes blood volume** under the sensor and moves the sensor against the skin.
- **That artifact is periodic, at the cadence** (≈ 1.5–3 Hz). That's the same band as heart rate (1–3.3 Hz).
- When cadence and HR are close, a plain spectral peak picker **locks onto the cadence**. That's the classic "HR equals step rate" failure.

Bent et al. 2020 measured six commercial wearables against ECG: absolute HR error during activity was **≈ 30 % higher** than at rest ([PubMed](https://pubmed.ncbi.nlm.nih.gov/32047863/)). Shcherbina et al. 2017 (7 devices, 60 people) found median HR error **1.8 % (cycling) to 5.5 % (walking)** ([PubMed](https://pubmed.ncbi.nlm.nih.gov/28538708/)). **Those numbers are the realistic bar.**

## 2. Methods

| Method | Idea | Cost on the band |
|---|---|---|
| **Spectral subtraction + tracking** (TROIKA, Zhang et al., IEEE TBME 2015) | Use the accelerometer spectrum to remove cadence peaks from the PPG spectrum, then track HR across windows with continuity constraints | FFT of 8 s windows every 2 s. Small for an M33 |
| **Adaptive filter** (LMS/RLS with accel as reference) | Subtract the motion-correlated part in the time domain | Very cheap |
| **Wiener / phase-vocoder variants** (e.g. WFPV) | Frequency-domain filtering + phase-vocoder refinement | Moderate |
| **Small neural networks** (CNN on PPG + accel windows) | Learned from labelled data | Needs a dataset and quantisation (TFLM). Highest accuracy in the literature but data-hungry |

**P0 recommendation:**

1. Use green PPG at 50–100 sps, plus accel at the **same** timestamps (sensors TIME_SYNC).
2. Run a TROIKA-style spectral tracker with an accel-cadence notch, plus a **confidence score** (peak prominence and agreement between the two photodiodes).
3. When confidence is low, **hold the last good value** and mark it as estimated (brief §4.2 confidence handling).
4. The gyro isn't needed for the HR algorithm. Accel is the standard reference.

## 3. Public datasets for development

| Dataset | Content | Use |
|---|---|---|
| **IEEE Signal Processing Cup 2015** | 2-channel wrist PPG + 3-axis accel + ECG, 12 subjects running on a treadmill | The classic benchmark that TROIKA was published on |
| **PPG-DaLiA** (Reiss et al., Sensors 2019) | Wrist PPG (Empatica E4) + accel + ECG, 15 subjects, daily-life activities, ≈ 2.5 h each | Realistic everyday motion; most used modern benchmark |
| **WESAD** (Schmidt et al. 2018) | Wrist + chest sensors, stress/affect protocol | Stress/HRV work for P1 |

Use these to build and score the algorithm **before** P0 hardware arrives. Then collect our own data (the E4's optics differ from ours).

## 4. Accuracy targets for P0 validation (proposed)

| Condition | Reference | Target MAE |
|---|---|---|
| Rest, seated | ECG chest strap | ≤ 2 bpm |
| Sleep | ECG (Holter or chest strap) | ≤ 2 bpm |
| Walking 5 km/h | ECG chest strap | ≤ 5 bpm |
| Running 8–10 km/h | ECG chest strap | ≤ 8 bpm |
| Cycling (ergometer) | ECG chest strap | ≤ 5 bpm |
| Gym (weights, wrist flexion) | ECG chest strap | report only. Known worst case for all wrist PPG |

Also report the **percentage of time with a valid (high-confidence) HR**, not just MAE on the valid parts. Otherwise a device that just refuses to output during exercise looks accurate.

## 5. HR zones

- **Zones:** % of HRmax (age-predicted, e.g. 208 − 0.7 × age, or user-entered) or % of HR reserve (Karvonen, needs resting HR, which the band measures during sleep).
- **Configuration:** set in the app and synced (brief §4.6).
- **Zone feedback:** display + haptic only when confidence is high. A wrong "zone 5!" buzz is worse than none.
