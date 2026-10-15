# Calories (Energy Expenditure) — Estimate Only

Brief §4.2: "Resting, active and total calorie estimates." "Calories are not directly measured. The algorithm will combine heart rate, motion, duration, user profile and activity type. Calorie values must be labelled as estimates."

---

## 1. How accurate are wrist devices?

**Shcherbina et al., J Pers Med 2017** tested 7 wrist devices on 60 people:

- Heart rate was reasonably accurate.
- Calorie (energy expenditure) error was large: median error ranged from 27 % to 93 % by device, and **no device was better than 20 %**.

Sources: [PubMed](https://pubmed.ncbi.nlm.nih.gov/28538708/), [Stanford news](https://med.stanford.edu/news/all-news/2017/05/fitness-trackers-accurately-measure-heart-rate-but-not-calories-burned.html).

That is the state of the art for consumer wrist devices, so the brief is right to require "label as estimates".

## 2. Model

```
Total = Resting (BMR) + Active (HR- or MET-based) [+ ~10 % thermic effect of food, optional]
```

### 2.1 Resting — Mifflin-St Jeor BMR (1990)

```
BMR_kcal/day = 10·weight_kg + 6.25·height_cm − 5·age + s
s = +5 (male), −161 (female)
```

- Spread evenly over 24 h as the resting component.
- Weight, height, age and sex come from the user profile in the app (§4.6).

### 2.2 Active — two methods, chosen minute by minute

**(a) HR-based (Keytel et al., J Sports Sci 2005).** Use only when HR is clearly raised: roughly > 90–100 bpm, or > 40 % of HR reserve.

```
male:   EE_kJ/min = −55.0969 + 0.6309·HR + 0.1988·weight_kg + 0.2017·age
female: EE_kJ/min = −20.4022 + 0.4472·HR − 0.1263·weight_kg + 0.0740·age
kcal/min = kJ/min ÷ 4.184
```

Below that HR range the equation is unreliable, so don't use it at rest.

**(b) Motion/MET-based.** The activity class (ACTIVITY.md) is mapped to a MET value from the **Compendium of Physical Activities** (Ainsworth et al., updated 2024).

```
kcal/min ≈ MET × weight_kg × 3.5 / 200
```

For walking and running, scale the MET with the speed estimated from cadence.

**Per-minute rule:**

| Situation | Method |
|---|---|
| Raised HR, high confidence | (a) HR-based |
| Clear activity class but low HR (e.g. slow walking) | (b) MET-based |
| Anything else | resting component only |

For "active calories", subtract the resting energy from (a) or (b), so the same minute isn't counted twice.

## 3. Personalisation (P1)

- **Fitness level** changes the HR-to-energy relationship. VO2max-aware models (e.g. Keytel's VO2max variant) reduce the error when VO2max is known.
- VO2max can be estimated from HR and running pace later.
- **Resting HR** measured during sleep improves the HR-reserve thresholds.

## 4. Validation

| Reference | Use |
|---|---|
| Indirect calorimetry (metabolic cart, VO2 / VCO2) | Gold standard for active calories in a lab protocol (walk, run, cycle) |
| Doubly-labelled water | Total calories over 1–2 weeks. Expensive; research only |

**P0 plan:**
- 10–20 people, one lab session each with a metabolic cart.
- Report error per activity and overall.
- Realistic target: **no worse than the commercial devices in the published studies**.

## 5. User-facing wording

> "Calories are an estimate based on your heart rate, movement and profile. They can differ from your actual energy use by a large margin, especially during strength training."

Round displayed values to the nearest 10 kcal. Exact-looking numbers suggest accuracy that isn't there.
