# Activity Outputs — Steps, Distance, Active Minutes, Floors, Activity Class

Brief §4.2:
- Step count
- Estimated distance using step length and optional phone GPS
- Active minutes and inactivity periods
- Floors climbed and relative elevation change
- Automatic detection of broad activity classes: walking, running, cycling, stair climbing, inactivity and generic workout
- "Confidence handling: uncertain activities should be reported as generic activity or require user confirmation instead of being assigned a false precise label."

---

## 1. Steps

- **Source:** the BMI270's on-chip step counter (base/wearable config) runs in the sensor at near-zero CPU cost (sensors MOTION_BMI270).
- **Firmware post-processing:**
  - Drop step bursts shorter than ≈ 8–10 consecutive steps. This is the standard trick against false steps from hand-waving and typing.
  - Drop steps while the band is off-wrist or charging.
- **Validation:** count steps by hand or from video, 500+ steps per condition. Report % error for each condition separately.
  - Conditions: walk slow / normal / fast, run, stairs, pushing a trolley (arm still, a known failure), desk work (false steps).
  - Wrist devices typically do worst when the arm is still or carrying something; report those cases honestly.

## 2. Distance

| Method | Accuracy | When |
|---|---|---|
| Step count × step length from height (common heuristic: ≈ 0.413 × height for women, 0.415 × height for men) | rough; depends on pace | default |
| Step length scaled with cadence (longer steps at higher cadence) | better across paces | after a short calibration |
| **Calibrated from phone GPS** (P1 GPS feature): fit the user's step-length vs cadence curve from outdoor walks/runs | best | after the first GPS sessions |

The calibration is stored in the user profile on the phone (brief §4.6) and synced to the band.

## 3. Active minutes and inactivity

- **Intensity per minute** comes from accelerometer vector-magnitude counts, plus HR when available.
- **Active minute:** counts above a moderate threshold, **or** HR above ≈ 50–60 % of heart-rate reserve.
- **Inactivity:** no steps and counts below a sedentary threshold for ≥ 50–60 min while awake. This can trigger an optional "move" reminder (haptic + icon).
- **Calibration:** set the thresholds against a reference on 10–20 people — either a research-grade accelerometer or indirect calorimetry (METs).

## 4. Floors

See sensors PRESSURE_BMP390 §2: a floor counts when there's a ≥ 3 m rise during a step bout, at a plausible climb rate. Count downward floors separately, for elevation loss.

## 5. Activity classification with confidence

### Classes and features (5–10 s windows)

| Class | Key features |
|---|---|
| Inactive / still | very low accelerometer variance, no steps |
| Walking | cadence 80–125 steps/min, moderate vertical acceleration |
| Running | cadence > 140, high peak acceleration, high HR |
| Stairs | walking cadence plus pressure slope (±0.1–0.4 m/s) |
| Cycling | few or no steps, rhythmic handlebar vibration, steady raised HR |
| Generic workout | raised HR with irregular motion, and none of the above is confident |

### Model options

| Option | Size | Accuracy | Notes |
|---|---|---|---|
| Rule-based thresholds | < 5 KB | fine for walk / run / still | brittle for cycling |
| **Small decision tree / random forest** on hand-made features | 10–50 KB | good on broad classes (published results) | **P0 recommendation** |
| Tiny CNN (TensorFlow Lite Micro / Edge Impulse) | 20–100 KB flash, tens of KB RAM | best, given enough data | P1, once our own labelled data exists |

### Public datasets to start from

- **WISDM** — phone + watch accelerometer, many activities.
- **HHAR** — the same activities recorded on many different devices.
- **PAMAP2** — wrist, chest and ankle IMUs plus HR.

These are only a starting point. Our wrist placement and sampling differ, so the model must be retrained on our own labelled data from P0.

### Confidence → "generic" (the brief's rule)

1. The model outputs a probability for each class.
2. Show a specific label only if p ≥ a threshold (e.g. 0.8) **and** it stays above it for ≥ 2–3 minutes.
3. Otherwise:
   - if HR is raised, show **"Workout"** (generic);
   - if not, show no label.
4. If a generic workout lasts > 10 min, the app asks: "Were you cycling?"
5. Save the user's answers as **new labelled data**. This builds the P1 dataset for free.

## 6. Plan for collecting labelled data

| Step | What |
|---|---|
| 1 | Lab protocol, 20 people. 5 min each of: sit, stand, walk (3 speeds), run, stairs, cycling (ergometer + outdoor), gym circuit. Video plus manual labels |
| 2 | Free-living week, 20 people. App prompts for labels, plus phone GPS |
| 3 | Hold out 25 % of the **people** (not 25 % of the windows) for testing, so the reported accuracy is for users the model has never seen |
