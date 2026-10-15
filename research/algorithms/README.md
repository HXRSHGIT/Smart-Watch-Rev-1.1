# R&D — Algorithms (Activity, Calories, Sleep, P1)

Branch `rnd/algorithms`. Covers brief §4.2 (fitness outputs), §4.3 (sleep), §5 (P1) and the "characterized against suitable references" part of §14.

| File | What it answers |
|---|---|
| [ACTIVITY.md](ACTIVITY.md) | Steps, distance, active minutes, floors, activity classes with confidence → "generic", plan for collecting labelled data |
| [CALORIES.md](CALORIES.md) | How bad wrist calorie estimates are (published evidence), BMR + Keytel + MET model, validation, wording |
| [SLEEP.md](SLEEP.md) | Actigraphy + HR sleep detection, outputs, hardware readiness for P1, validation stages |
| [P1_FEATURES.md](P1_FEATURES.md) | HRV, respiratory rate, readiness/stress, GPS, falls (research only), icons, export/delete |

## Key findings

1. **Steps:** use the BMI270's on-chip step counter, plus a firmware filter that drops short bursts.
2. **Distance:** improves a lot once phone-GPS calibration is in place.
3. **Activity classification:** a small decision-tree model for P0.
4. **Confidence rule:** show a specific label only when the model is confident for ≥ 2–3 min. Otherwise show "Workout", and ask the user. Their answers become free labelled data.
5. **Calories are the weakest output industry-wide.** Published median errors are 27–93 % (Shcherbina 2017). Use BMR + Keytel (raised HR) + MET (motion). Always label as an estimate and round to 10 kcal.
6. **Sleep:** actigraphy (Cole-Kripke / Sadeh) + an HR drop. Expect sleep to be overestimated during quiet wake. No sleep stages until validated against polysomnography.
7. **P1 needs no hardware change** if P0 keeps 100 sps PPG at night and logs beat intervals.
8. **Fall detection stays research-only**, with no emergency claim (brief §5).

## Decisions for the client

- Which outputs ship at P0, and which are hidden until validated?
- Budget for the reference studies: metabolic cart (calories), polysomnography (sleep), ECG (HR/HRV).

## Next steps

1. Prototype the HR tracker and activity classifier on public datasets (IEEE SPC 2015, PPG-DaLiA, WISDM, PAMAP2) before P0 hardware arrives.
2. Write the lab protocols (activity, calorimetry, sleep) so data collection starts as soon as P0 works.

Done by Harsh Thakur.
