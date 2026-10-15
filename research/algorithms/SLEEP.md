# Sleep — Detection, Duration, Interruptions, HR Trend

Brief §4.3:
- Sleep start and wake detection.
- Total sleep duration and interruptions.
- Resting heart-rate trend during sleep.
- Motion-based sleep quality indicators.
- "Hardware support for later respiratory-rate, HRV and sleep-stage algorithms, without claiming these are validated in the first prototype."

---

## 1. P0 method — actigraphy + heart rate

### 1.1 Sleep or wake, per 30 s or 60 s epoch

**Classic actigraphy scoring** (both designed for wrist actigraphs, both cheap enough to run on the band):

- **Cole-Kripke** (Sleep, 1992) — a weighted sum of activity counts over a window of a few minutes either side.
- **Sadeh** (Sleep, 1994) — uses the mean, standard deviation and counts of activity.

**Known weakness:** actigraphy detects sleep well but **misses quiet wake**. Someone lying still while awake gets scored as asleep. This is the main reason every motion-only tracker overestimates sleep.

**Adding heart rate fixes part of it:**
- HR falls during sleep, so HR below the evening baseline supports "asleep".
- Short HR rises (> 10 bpm) mark arousals.

### 1.2 Finding the sleep period

1. **Main sleep period:** the longest block of "sleep" epochs, allowing short wake gaps (< 20–30 min).
2. **Sleep onset:** the first sustained sleep (≥ 10–15 min) in that block.
3. **Wake time:** the last sustained sleep epoch.
4. **Naps:** separate daytime blocks of ≥ 20 min, reported as naps.

### 1.3 Outputs

| Output | Definition |
|---|---|
| Time in bed (estimate) | From the start of low activity to the final rise |
| Total sleep time | Sum of sleep epochs in the sleep period |
| Interruptions | Wake bouts of ≥ 2–5 min inside the sleep period |
| Sleep efficiency | Total sleep ÷ time in bed |
| Restlessness (motion quality indicator) | % of epochs with movement during the sleep period |
| Resting HR (night) | Lowest stable 5-min average HR during sleep, tracked across nights |

## 2. Is the hardware ready for P1? (brief requirement)

| P1 algorithm | What it needs | How this design provides it |
|---|---|---|
| HRV (RMSSD) at night | Beat-to-beat intervals with ≈ 1–2 ms timing | 100 sps green PPG + peak interpolation (optical-ppg PPG_FRONTEND §3) |
| Respiratory rate | Breathing modulates the PPG baseline, amplitude and beat intervals at 0.1–0.5 Hz | Any rate ≥ 25 sps |
| Sleep staging (light / deep / REM) | HR, HRV, motion, respiration, ideally skin temperature, plus a model trained on polysomnography (lab sleep study) data | All sensors present; sampling is sufficient |
| Raw nights for training | Storage + upload | 64 Mbit engineering flash + phone streaming (storage-nfc-dft) |

**No P1 algorithm needs a hardware change**, provided P0:
- keeps 100 sps PPG at night, and
- logs beat intervals (≈ 58 KB/night, see storage-nfc-dft FLASH_STORAGE).

## 3. Validation

| Stage | Reference | Notes |
|---|---|---|
| P0 | Research actigraph on the other wrist + sleep diary, 20 people × 7 nights | Checks sleep onset, wake time and total sleep. Cheap |
| P0/P1 | **Polysomnography** (sleep lab), 15–30 nights | Epoch-by-epoch sensitivity, specificity and accuracy. Needed before any sleep-stage claim |

Consumer sleep trackers have already been compared against polysomnography in published studies (e.g. Chinoy et al., Sleep 2021, seven consumer devices). Reuse that study design: epoch-by-epoch comparison and Bland-Altman plots for total sleep time.

## 4. Wording

> "Sleep times and interruptions are estimated from movement and heart rate."

Don't show sleep stages until they have been validated against polysomnography (brief §4.3).
