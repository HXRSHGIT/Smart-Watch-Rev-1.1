# R&D — Validation, Compliance and Mechanical

Branch `rnd/validation`. Covers brief §13 (acceptance gates), §14 (success criteria), §15 (phases) and the mechanical side of §2.

| File | What it answers |
|---|---|
| [TEST_PLAN.md](TEST_PLAN.md) | Every §13 bullet as a test with method, pass criterion, stage, and a link to the detailed branch; rough schedule |
| [COMPLIANCE.md](COMPLIANCE.md) | Wellness vs medical line; radio, safety, battery, skin contact, water, environment and privacy rules per market |
| [MECHANICAL_STACKUP.md](MECHANICAL_STACKUP.md) | Pod size, vertical stack, footprint allocation, PCB technology, weight |

## Key findings

1. **The §13 gates map to 25 concrete tests.** About half need people on the wrist with reference equipment (ECG strap, finger oximeter, actigraph, metabolic cart). Book these early.
2. **Several pass criteria aren't in the brief.** They're proposed here and marked (P); the client approves them.
3. **The wellness position depends on claims, not hardware.** Phrase SpO2, temperature and HRV/recovery as estimates and trends everywhere, including marketing.
4. **Water target should be at least IPX7** for a band worn 24/7. Swimming (5 ATM) is a separate decision that drives the vent and sealing.
5. **Pod ≈ 35 × 25 × 9–11 mm.**
   - The battery sets the thickness.
   - The LRA needs its own pocket beside the battery.
   - The board must be thin (0.6–0.8 mm) HDI.
6. **EU Battery Regulation 2023/1542** may affect a sealed band from 2027. Check early.

## Decisions for the client

- Launch markets.
- Water target.
- Final claims list.
- Approve or change the proposed pass criteria.

Done by Harsh Thakur.
