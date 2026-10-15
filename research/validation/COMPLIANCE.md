# Compliance Map — What Applies to a Consumer Wellness Band

The brief says "ESD, EMC pre-compliance, thermal, sweat, corrosion and water-resistance testing appropriate to the approved product target" (§13). It also says "production release requires stronger evidence" (§13), and "no one describes the design as production-ready without evidence" (§14).

This file lists what a BLE wrist band with a Li-ion cell, skin contact and health-style outputs normally has to meet. **Confirm every item with an accredited test lab for the actual launch markets.** The client hasn't named the markets yet.

---

## 1. Wellness vs medical device — the most important line

The band shows heart rate, SpO2, skin temperature, sleep and "recovery". Whether it's a medical device is decided by its **intended purpose and claims**, not by the sensors inside.

| Market | Rule | Stays "wellness" if… |
|---|---|---|
| USA | FDA "General Wellness: Policy for Low Risk Devices" guidance | Claims are general fitness or wellness only (e.g. "track your sleep", "see your activity"), with no diagnosis, treatment or disease claims, and low risk |
| EU | MDR (EU) 2017/745 | Manufacturer's intended purpose isn't medical (no diagnosis, monitoring or prediction of disease) |
| India | Medical Devices Rules 2017 (CDSCO) | Same principle: no medical claims |

**What this means for the product:**

- **SpO2:** "blood-oxygen estimate for wellness". **Never** "detects low oxygen", "screens for sleep apnea" or "COVID".
- **Temperature:** "skin temperature trend". **Never** "fever detection".
- **HRV / recovery:** "readiness estimate". **Never** "detects illness or stress disorders".
- **Falls:** research only. No emergency feature (brief §5).
- **Marketing, app text and the website** must follow the same rules. Claims anywhere count.

The brief's §3 already sets this direction ("presented as estimates").

## 2. Radio

| Market | Requirement |
|---|---|
| USA | FCC Part 15 Subpart C (§15.247, 2.4 GHz digital transmission) for the BLE radio + Part 15 Subpart B for unintentional emissions. Equipment authorisation (certification) through a TCB |
| EU / UK | Radio Equipment Directive 2014/53/EU (UK: Radio Equipment Regulations 2017): EN 300 328 (2.4 GHz radio), EN 301 489-1 / -17 (EMC for radio), EN 62368-1 (safety), EN 62479 or EN 50663 (RF exposure for low-power devices) |
| India | WPC Equipment Type Approval (ETA) for 2.4 GHz devices |

**Shortcut:** a pre-certified BLE **module** would reduce radio testing, but it doesn't fit this board size. With a chip-down nRF design, the full radio tests are needed. Budget for them.

## 3. Product safety

| Item | Standard |
|---|---|
| Electrical / fire / thermal safety | IEC / EN 62368-1 (audio/video, information and communication technology equipment), including touch-temperature limits for parts in prolonged skin contact |
| Battery cell / pack | IEC 62133-2 (Li-ion safety, portable) |
| Battery transport | UN 38.3 test summary (needed to ship the product by air) |
| India | BIS Compulsory Registration Scheme: smart watches and Li-ion cells / batteries are covered. Confirm the current product list and standard numbers with BIS before launch |

## 4. Skin contact

| Item | Standard / rule |
|---|---|
| Biocompatibility of skin-contact materials (strap, back housing, windows, pogo pads, temperature pad) | ISO 10993-1 framework. For intact-skin, prolonged contact this typically means cytotoxicity (-5), sensitisation (-10) and irritation (-23). Usually covered by **supplier material reports** plus the final-part test |
| Nickel release (EU) | REACH Annex XVII entry 27: limits for nickel release from parts in prolonged skin contact, tested per EN 1811. Important for stainless pogo pads and the temperature contact |
| Restricted substances | RoHS (EU 2011/65/EU), REACH SVHC declaration |

## 5. Water and dust

| Option | Standard | Meaning |
|---|---|---|
| IPX7 | IEC 60529 | 1 m immersion for 30 min. Rain, washing, shower |
| IPX8 | IEC 60529 | beyond IPX7, at conditions the manufacturer states |
| Water-resistant watch (e.g. 5 ATM) | ISO 22810:2010 | Swimming-grade claims |

**Recommendation:** a 24/7 band is worn in the shower. **Make IPX7 the minimum target.** Decide early whether swimming is a goal, because it drives the vent choice (sensors PRESSURE_BMP390) and the window and pogo sealing.

## 6. Environment and end of life (EU)

| Item | Note |
|---|---|
| WEEE | Take-back and labelling |
| EU Battery Regulation (EU) 2023/1542 | New rules for portable batteries, including end-user removability and replaceability requirements from 2027, with limited exceptions (e.g. for devices designed for wet environments). **Check early** how it applies to a sealed band. It can affect the mechanical design |

## 7. Privacy (because the data is health-like)

| Market | Law |
|---|---|
| EU | GDPR (health data is a special category) |
| India | Digital Personal Data Protection Act 2023 |
| USA | State laws, plus FTC Health Breach Notification Rule for health apps |

Design support already in the plan: encrypted log at rest, authenticated BLE, user export and deletion (algorithms P1_FEATURES §8).

## 8. When to do what

| Phase | Compliance work |
|---|---|
| P0 prototype | Pre-scan EMC and radio at a lab; ESD; thermal; internal water tests. Collect supplier material and cell reports |
| Rev C | Fix findings; full pre-compliance |
| Pilot | Formal certification: FCC, RED, WPC/BIS for the chosen markets; IEC 62368-1, IEC 62133-2 and UN 38.3 reports; ISO 10993 tests on the final parts |

## 9. Questions for the client

1. Launch markets (US / EU / UK / India / others)?
2. Water target: shower-proof (IPX7) or swim-proof (5 ATM)?
3. Final claims list for every output (to keep the wellness position).
