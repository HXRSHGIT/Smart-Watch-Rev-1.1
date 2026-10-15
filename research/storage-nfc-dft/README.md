# R&D — Storage, NFC and Test Access

Branch `rnd/storage-nfc-dft`. Covers brief §4.6 (storage, SWD, production test), the flash and NFC rows of §8, and the programming rows of §13.

| File | What it answers |
|---|---|
| [FLASH_STORAGE.md](FLASH_STORAGE.md) | Flash part, data per day, offline days, raw-capture limits, filesystem, encryption |
| [NFC_ACTIVE.md](NFC_ACTIVE.md) | What the ST25R210 would be for, what it costs, passive NFCT alternative |
| [DFT_PROGRAMMING.md](DFT_PROGRAMMING.md) | SWD connector, debug lock/recover, test points, factory flow |

## Key findings

1. **Swap the W25Q32RV (3 V only) for the Macronix MX25R3235F** (1.65–3.6 V, 0.35 µA deep power-down, same 2 × 3 mm class). Required by the 1.8 V digital domain.
2. **Summaries are ≈ 80 KB/day**, so a 3 MB log holds ≈ 37 days offline.
3. **Raw engineering capture is ≈ 4–6 MB/hour**, so 4 MB holds < 1 hour. Engineering units should take the 64 Mbit MX25R6435F, compression and phone streaming.
4. **Drop the active NFC reader.** No P0/P1 feature needs it, and it would add a ≈ 400 mA peak. Use the SoC's free NFCT tag for tap-to-pair if space allows.
5. **SWD:** TC2030-NL for development, plus round pads for the production fixture. Never set ERASEPROTECT on engineering units, because it makes recovery impossible.

## Decisions for the client

- What should NFC do, if anything?
- Production: allow factory recovery (ERASEPROTECT off) or lock forever?

## Next experiments

1. Flash power-fail test (200 random pulls) on the FCB log.
2. Build the factory self-test firmware early. It doubles as the P0 bring-up tool.

Done by Harsh Thakur.
