# Active NFC (ST25R210) — Keep or Drop?

Brief §8: "Active NFC — ST ST25R210 — Conditional on an approved active-reader use case and measured power/range."
Brief §4.7: power modes must coordinate "… optical pulses and NFC."

---

## 1. What an active reader would let the band do

An **active reader** generates its own 13.56 MHz field. It lets the band *read or write* cards and tags. A **passive tag** lets a phone or reader *read the band*. The two are different features.

| Possible use | Needs an active reader? | Realistic on a band? |
|---|---|---|
| Tap phone to pair (NFC OOB pairing) | **No**, a passive tag is enough | Yes |
| Phone reads a "band ID" or opens the app | **No**, passive tag | Yes |
| Band reads a gym-equipment tag to start a workout | Yes | Possible, niche |
| Band reads medicine-box tags ("did you take it") | Yes | The brief explicitly says the band doesn't confirm actions (§4.4) |
| Door / access control (ST markets the ST25R210 as Aliro-ready) | **No**: here the band is the *credential*, which is card emulation, which needs a secure element. A reader isn't what's needed | Out of scope for a wellness band |
| Contactless payment | No, needs a secure element plus a payment network | Out of scope |

**None of the brief's P0 or P1 features need an active reader.**

## 2. Costs if it stays

| Cost | Value | Basis |
|---|---|---|
| IC area | UQFPN-28, 4 × 4 mm + ≈ 10 passives (matching, EMC filter) | [ST](https://www.st.com/en/nfc/st25r210.html) |
| RF output | up to 1.6 W | ST |
| Peak battery current | ≈ 400 mA at 1.6 W out from a 4 V cell, ignoring losses (derived). Lower power settings are possible, but range drops | derived |
| Antenna | 13.56 MHz loop. On a ≈ 20 × 30 mm band, a few turns on a flex with a **ferrite sheet** between the coil and the battery are needed, or the battery's metal kills the field | general NFC practice |
| Range | single-digit cm with a small coil (estimate) | to measure |
| Power while idle | LPCD (low-power card detection) polling, µA–tens of µA depending on interval (unverified) | ST |
| Firmware | RFAL stack + protocol handling | ST |

The peak current alone is two to three times the coordinated peak budget in power-battery PEAK_LOAD.md.

## 3. Cheaper alternative already on the SoC

Both the nRF5340 and the nRF54L15 have an **NFCT** peripheral, an NFC-A **tag** (passive, field-powered).

- **BOM cost:** 2 pins + a small antenna coil + 1–2 tuning caps.
- **Battery cost:** ~0 µA, because the reader's field powers it.
- **What it enables:**
  - **tap-to-pair:** NFC OOB pairing gives MITM-protected pairing even on the Stealth variant where digits may be hard to read;
  - "tap band on phone to open the app".

## 4. Recommendation

1. **Remove the ST25R210 from P0.** Don't reserve board area for it.
2. **Add an optional passive NFCT antenna footprint**, with a decision at layout based on space. It's the cheap route to tap-to-pair.
3. If the client later names a reader use case, revisit it as a separate design: dedicated antenna on flex + ferrite, ≈ 400 mA peak path from VSYS, range test on a wrist.

## 5. Question for the client

> "What should the band do with NFC? If it's 'tap to pair' or 'tap to open the app', the chip already does that for free. If it's reading other tags, which ones and why?"
