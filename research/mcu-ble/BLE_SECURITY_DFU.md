# BLE Security, Pairing and Authenticated Firmware Update

Brief §4.6: "Secure pairing and authenticated firmware update over BLE." "Raw or minimally processed sensor data access during engineering validation" (§4.1).

The stack assumed is nRF Connect SDK (Zephyr) on the nRF54L15 recommended in TRADE_STUDY_MCU.md. Notes on the nRF5340 are given where it differs.

---

## 1. Pairing

### 1.1 Method

- Use **LE Secure Connections (LESC)** only (ECDH P-256). This is Security Mode 1 Level 4.
- In Zephyr, `CONFIG_BT_SMP_SC_ONLY=y` refuses legacy pairing.
- Legacy pairing can be cracked passively from a sniffed exchange, so it isn't acceptable for health data.

### 1.2 Which association model

The pairing method depends on what the band can do:

| Model | Needs on band | MITM-protected | Fit |
|---|---|---|---|
| Just Works | nothing | **No** | Rejected: anyone in range can pair during the pairing window |
| **Passkey Display** | display showing 6 digits | Yes | **Recommended.** The 64×32 OLED fits 6 digits in an 8×16 font (48 px wide) |
| Numeric Comparison | display + yes/no input | Yes | Possible with tap-to-confirm on the IMU, but awkward |
| OOB via NFC | NFC tag | Yes | Only if the passive NFCT tag is kept (see storage-nfc-dft) |

**The OLED is what makes MITM-protected pairing possible.** Without it, only Just Works would be left. Note this for the Stealth variant: the digits have to be readable through the dead-front.

### 1.3 Phone behaviour

- **iOS** handles bonding at the system level (Core Bluetooth). An app can't delete a bond; the user removes it in Settings. The band must therefore handle "phone forgot me, band didn't" by allowing re-pairing when the user holds a long-press or does a factory reset.
- **Android** behaviour varies by vendor. The common failure is a stale bond on one side, which gives `GATT_INSUF_AUTHENTICATION` and a reconnect loop. The same recovery path covers it.
- Use **Resolvable Private Addresses** (`CONFIG_BT_PRIVACY=y`), so a passer-by can't track the band by its address.

### 1.4 Bond storage

- Zephyr keeps bonds through the **settings** subsystem in **internal** non-volatile memory: ZMS on nRF54L RRAM, NVS on nRF5340 flash.
- Don't put bonds in external flash. It's an unauthenticated bus, and the bond keys (LTK, IRK) are secrets.
- Limit to 2–4 bonds (`CONFIG_BT_MAX_PAIRED`). Each bond is well under 1 KB.

---

## 2. Authenticated firmware update

### 2.1 Chain

```
phone app ──SMP over GATT──► band (mcumgr img_mgmt) ──► secondary slot
                                                         │
reboot ► MCUboot verifies ED25519 signature + version ───┘ ► copies to primary ► runs
```

- **Bootloader:** MCUboot, built by sysbuild.
- **Transport:** mcumgr SMP over BLE (`CONFIG_MCUMGR_TRANSPORT_BT`). Phone libraries exist: nRF Connect Device Manager for iOS and Android.
- **Restrict SMP to authenticated links.** `CONFIG_MCUMGR_TRANSPORT_BT_PERM_RW_AUTHEN=y` requires an encrypted, MITM-authenticated (bonded) connection. Without it, anyone in range can push an image (it would still fail the signature check, but it can erase the secondary slot and drain the battery).

### 2.2 Signature

- **nRF54L:** ED25519 is the recommended type, set with `SB_CONFIG_BOOT_SIGNATURE_TYPE_ED25519=y`. Public keys go in the **KMU** (hardware key slots) rather than in the bootloader binary, which also allows key revocation ([NCS bootloader configuration](https://nrfconnectdocs.nordicsemi.com/addons/addon-sidewalk/latest/application_development/bootloader_configuration.html)).
- **nRF5340:** ECDSA-P256 or ED25519, with the key compiled into MCUboot.
- **Signing key:** generate the production key offline and keep it out of git and off developer laptops. CI should sign only with a development key, and devices with production bootloaders must reject dev-signed images.

### 2.3 Downgrade (rollback) protection

- On nRF54L, MCUboot downgrade prevention needs **overwrite-only mode** (`SB_CONFIG_MCUBOOT_MODE_OVERWRITE_ONLY=y`) plus `CONFIG_MCUBOOT_DOWNGRADE_PREVENTION=y` in the MCUboot image ([NCS downgrade protection](https://nrfconnectdocs.nordicsemi.com/ncs/latest/nrf/app_dev/bootloaders_dfu/mcuboot_nsib/bootloader_downgrade_protection.html)).
- Hardware (counter-based) downgrade protection had missing dependencies on nRF54L15 in reported NCS versions ([DevZone](https://devzone.nordicsemi.com/f/nordic-q-a/125180/dfu-fw-downgrade-protection/552988)). **Check this on the NCS version picked at freeze.**
- **Trade-off:** overwrite-only means there's **no automatic revert** if a new image fails to confirm. The image must self-test before it calls `boot_write_img_confirmed()`, and a broken release can only be fixed by another update over BLE. If the image can't boot BLE, that means SWD. For P0 engineering units, swap mode with revert is friendlier; switch to overwrite-only plus downgrade prevention for production.

### 2.4 Slot layout (nRF54L15, 1.5 MB RRAM)

| Region | Size (planning) | Notes |
|---|---|---|
| MCUboot | 48 KB | measured size varies with crypto config |
| Primary slot | ≈ 700 KB | application |
| Secondary slot | ≈ 700 KB | same size as primary |
| Settings (bonds, config) | 32 KB | ZMS |
| Spare | remainder | |

Everything fits internally, so **external flash isn't in the update path at all**. On the nRF5340 (1 MB app flash) the secondary slot must go in external flash, and the network core needs its own update image.

### 2.5 Update time

- **Throughput:** with Data Length Extension (251-byte PDUs), ATT MTU 247 and 2M PHY, phones typically sustain **≈ 40–100 KB/s** (iOS is lower than Android; unverified, measure on target phones).
- **Duration:** a 500 KB image takes roughly 5–15 s of transfer, plus the MCUboot copy on reboot.
- **Pre-condition:** require battery > 30 % or charging before accepting an update. An RRAM/flash erase-write at 3.0 V cell voltage with an LED pulse on top is a brown-out risk; see power-battery PEAK_LOAD.md.

---

## 3. Engineering data streaming (§4.1 raw data access)

### 3.1 Data rate

| Stream | Rate | Bytes/sample | B/s |
|---|---|---|---|
| PPG, 2 channels × green (HR) | 100 Hz | 2 × 3 | 600 |
| PPG red + IR (SpO2 runs only) | 100 Hz | 2 × 3 | 600 |
| Accel 3-axis | 100 Hz | 6 | 600 |
| Gyro 3-axis (workout) | 100 Hz | 6 | 600 |
| Pressure + temp | 1 Hz | 6 | 6 |
| Skin temp | 1/60 Hz | 2 | ≈ 0 |
| Timestamps / framing | | | ≈ 100 |
| **Total, worst case** | | | **≈ 2.5 KB/s** |

That's under 5 % of a phone link. Throughput isn't the problem; **radio power** is. Continuous streaming at a 15–30 ms connection interval costs **≈ 0.3–1 mA**, which is days of battery per day of streaming.

### 3.2 Design

- **Engineering mode only:** a GATT service visible only after an authenticated "engineering unlock" write, so it isn't part of the consumer firmware's attack surface.
- **Two modes:**
  1. **Live stream** (notifications, shortest connection interval) for bench work.
  2. **Record-to-flash, then bulk-download.** This is the one that matters for wrist studies: the band logs raw data to external flash (see storage-nfc-dft FLASH_STORAGE.md) and dumps it when the phone connects.
- Frame each packet with a 32-bit sample counter per sensor, not phone receive time, so gaps are visible. See sensors TIME_SYNC.md.

---

## 4. Threat summary

| Threat | Control |
|---|---|
| Passive sniffing of pairing | LESC only |
| MITM during pairing | Passkey Display on the OLED |
| Tracking by address | RPA privacy |
| Malicious firmware | ED25519-signed images, key in KMU |
| Downgrade to a vulnerable version | MCUboot downgrade prevention (production builds) |
| Unauthenticated SMP / DFU | SMP permission = authenticated bonded link |
| Debug-port extraction | APPROTECT/SECUREAPPROTECT enabled in production (see storage-nfc-dft DFT_PROGRAMMING.md) |
| Raw-data service abuse | hidden behind engineering unlock, disabled in release builds |

---

## 5. Prototype tests (feeds §13)

1. Passkey pairing on 2 iOS and 3 Android phones (different vendors). Delete the bond on each side in turn and confirm recovery.
2. DFU of a signed image succeeds. A dev-signed image is rejected by a production bootloader. A lower version is rejected with downgrade prevention on.
3. Pull power (open the pogo/battery) at 10 random points during DFU. The band must always boot into a valid image.
4. Stream engineering data for 30 min. Check sample counters for gaps, and measure average current during streaming.

## Sources

- nRF Connect SDK: [bootloader configuration](https://nrfconnectdocs.nordicsemi.com/addons/addon-sidewalk/latest/application_development/bootloader_configuration.html), [downgrade protection](https://nrfconnectdocs.nordicsemi.com/ncs/latest/nrf/app_dev/bootloaders_dfu/mcuboot_nsib/bootloader_downgrade_protection.html), [SMP server sample](https://nrfconnectdocs.nordicsemi.com/ncs/latest/nrf/samples/dfu/smp_svr/README.html), [nRF54L DFU configuration](https://nrfconnectdocs.nordicsemi.com/ncs/latest/nrf/app_dev/device_guides/nrf54l/dfu_config.html)
- [DevZone: nRF54L15 hardware downgrade protection thread](https://devzone.nordicsemi.com/f/nordic-q-a/125180/dfu-fw-downgrade-protection/552988)
- Bluetooth Core Specification v5.x, Vol 3 Part H (Security Manager)
