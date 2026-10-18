# Iteration 1 - approved sensor-test PCB

Decision approved by the project owner: **2026-10-18**.

This is the current implementation baseline for the first custom PCB. It supersedes the earlier full-wearable component recommendations for this iteration. The original client brief and the nine R&D branches remain background for later revisions.

## Objective and boundaries

Build a USB-powered custom PCB to acquire red/infrared optical waveforms, develop and evaluate heart-rate and SpO2 estimates, measure skin-temperature trends, and check basic USB/BLE communication. A board larger than the intended finished band is acceptable.

Use a solder-down ESP32-C3 module on our PCB, not a Pico or another complete development board. Begin with stationary optical measurements. A successful finger test does not establish on-wrist or motion performance. The MAX30102 supplies samples, not a validated SpO2 result; calibration and reference comparisons remain necessary. Skin temperature is not core body temperature.

The component choices and scope below are approved. This is not a fabrication-ready schematic, a procurement-qualified BOM or evidence of tested hardware. Current stock, price, lead time, ordering suffixes and latest manufacturer specifications have not been verified. Support-component counts and values must be completed in schematic capture.

## Selected components

| Function | Selected part / specification | Quantity | Decision and rationale |
|---|---|---:|---|
| Controller, flash and radio module | ESP32-C3-MINI-1-N4 | 1 | Solder-down module with 4 MB flash, BLE, Wi-Fi and native USB Serial/JTAG. Reduces clock/RF implementation work so this iteration can focus on sensing. Keep Wi-Fi disabled by default. |
| Optical acquisition | MAX30102EFD+T | 1 | Integrated red/IR LEDs, photodetector and acquisition electronics. Use raw samples for HR/SpO2 development. No external optical AFE, LEDs or photodiodes are fitted. |
| Skin-temperature sensor | MAX30208CLB+ | 1 | Shares the 1.8 V sensor-side I2C bus. Place on a thermally isolated skin-facing area with local decoupling. |
| Main 3.3 V supply | AP2112K-3.3TRG1 | 1 | USB 5 V to 3.3 V for the module and optical LED supply. The 600 mA regulator rating is not a guarantee of available continuous board current: verify input-power limits, transients and thermal dissipation. |
| Sensor 1.8 V supply | TLV75518PDBVR | 1 | 3.3 V to 1.8 V for MAX30102 core and MAX30208. |
| Open-drain interface translation | BSS138-7-F | 3 | SDA, SCL and MAX30102 INT between the 1.8 V and 3.3 V domains, with pull-ups on both sides. Start I2C at 100 kHz; verify low levels, rise time and startup behavior. |
| USB-C connector | GCT USB4105-GF-A | 1 | USB 2.0 data and power. Match the exact manufacturer footprint and mechanical drawing. |
| USB ESD protection | USBLC6-2SC6 | 1 | Data-line ESD protection near the connector. Confirm reference connection and routing. |
| Reset control | Normally open tactile switch | 1 | Pull ESP32 EN low for reset. Exact switch MPN/footprint to be selected during capture. |
| Boot control | Normally open tactile switch | 1 | Manual download-mode entry using the module's documented boot-strapping circuit. Exact switch MPN/footprint to be selected during capture. |
| Power indicator | Green LED, 0603 | 1 | Board power indication, with a current-limiting resistor. Keep light away from the optical sensor. |
| Firmware status indicator | LED, 0603 | 1 | Initialization, capture and fault indication. Exact LED MPN and resistor to be selected during capture. |
| UART service access | Unpopulated 1x4, 2.54 mm header footprint | 1 | GND, TX, RX and 3.3 V reference. External adapter is a bench tool. Avoid back-powering through the reference pin. |

MAX30208 is polled on the shared bus in this iteration; its optional GPIO/alarm features do not require another translator. Confirm sensor addresses and configure any address selection explicitly in the schematic and firmware.

## Required supporting circuitry

| Item | Initial requirement |
|---|---|
| USB-C CC resistors | Two separate 5.1 kohm resistors, one on CC1 and one on CC2, for sink/device operation. These do not authorize arbitrary current draw; respect the attached USB source and enumeration limits. |
| Sensor-bus pull-ups | Two pull-ups per translated line; 4.7 kohm is a starting value, not a validated bus calculation. Include SDA, SCL and optical INT. |
| Module startup network | EN pull-up/RC and boot-strapping resistors per the exact ESP32-C3 module reference circuit. Keep sensor/indicator assignments clear of boot, USB and service pins. |
| Regulator capacitors | Input/output capacitance, ESR, voltage rating and layout per each regulator datasheet. Account for ceramic-capacitor DC-bias derating. |
| Local supply decoupling | At both sensors and the module, with bulk capacitance for module activity and optical pulses. Verify the MAX30102 LED-supply minimum during load steps. |
| USB series-resistor footprints | Follow Espressif's native USB reference design; finalize values and routing at schematic/layout review. |
| LED resistors | One per indicator, selected for modest current and visibility. |
| Test points | USB 5 V, 3.3 V, 1.8 V, GND, SDA, SCL, optical INT and EN. Provide practical current-measurement access. |

No external USB-to-UART IC is needed for the main logging path because the selected module exposes native USB Serial/JTAG. This interface is not SWD; use ESP32-compatible USB/JTAG/UART development tools.

## Power and communication architecture

```text
USB-C 5 V
    |
    +-- AP2112K, 3.3 V --+-- ESP32-C3-MINI-1-N4
                         +-- MAX30102 VLED+
                         +-- TLV75518, 1.8 V --+-- MAX30102 VDD
                                              +-- MAX30208 VDD

ESP32 I2C (3.3 V) <--> open-drain translation <--> sensor I2C (1.8 V)
ESP32 GPIO       <--- translated MAX30102 INT
ESP32 USB        <--> ESD protection <--> USB-C <--> computer logging
```

Use the sensor datasheets to verify each pin's permitted voltage and power sequencing. Do not connect MAX30102 core VDD to 3.3 V. The 3.3 V regulator's thermal rise and supply noise must not corrupt the temperature or optical measurements.

## Flash decision

**No external flash IC or reserved external-flash circuit in Iteration 1.** The N4 module contains 4 MB flash shared by firmware, any OTA slots, configuration and optional logs. It is not 4 MB of unrestricted logging space.

Stream raw optical and temperature data to a computer through USB. Internal flash may store settings and short logs after a partition and endurance budget is defined. Larger standalone or overnight raw recording is a later requirement, not a promise of this board.

## Explicitly deferred

- Battery, charger/fuel gauge, nPM1300, reversible pogo charging and charging protection.
- OLED, display optics and display power switching.
- Haptic driver and actuator.
- IMU, auxiliary accelerometer, pressure sensor and vent.
- External NOR flash and NFC reader/tag circuitry.
- MAX86141, separate SFH7016 emitter and VEMD8080 detectors.
- Final wearable dimensions, multi-day battery life, waterproofing and production certification.

BLE is available for basic testing. Neither BLE operation nor the firmware's power consumption has yet been demonstrated on this design. No claim of final wearable suitability is made from the ESP32 selection alone.

## Placement requirements

- Put the module at a board edge and implement its antenna keepout on all required layers; respect clearances to metal and any fixture.
- Leave the MAX30102 optical face accessible for controlled finger and wrist contact. Provide an opaque gasket/light barrier; do not cover it with an IR-blocking window or conformal coating.
- Put MAX30208 on a skin-facing tab/island or another deliberately isolated thermal path. Keep regulator/module heat and optical illumination away from it. Board temperature alone is not a skin-temperature measurement.
- Keep USB protection close to the connector and regulator loops compact. Route optical supply decoupling to limit LED-pulse disturbance.
- Allow space for probing, fixtures and service access. The historical 35 x 25 mm pod estimate is not a fixed PCB limit for this iteration.

## Bring-up and acceptance evidence

1. Review exact datasheets, ordering codes, footprints, rail tolerances, source-current budget and regulator thermal behavior before fabrication; complete the passive BOM and ERC/layout reviews.
2. Power from a current-limited source and verify 3.3 V/1.8 V rails, startup and regulator temperature before enabling optical pulses or wireless traffic.
3. Demonstrate USB programming/logging and manual boot/reset recovery. Verify both I2C sensors and check translated signal levels/rise times.
4. Capture timestamped red/IR samples, optical settings and FIFO/gap status on the computer. Confirm repeatable stationary waveforms with controlled contact and ambient light.
5. Compare HR with a suitable reference and report error and valid-data coverage. Record provisional SpO2 repeatability/reference agreement without claiming validated low-saturation or clinical accuracy.
6. Compare temperature response with a reference and repeat with the radio/processor active to quantify internal-heating bias.
7. Test basic BLE transfer separately and while recording optical data; check for sample loss, rail disturbance and thermal effects.

The next deliverable is the schematic and completed BOM for this approved baseline. No hardware measurements, clinical validation or fabrication approval are recorded by this decision.

## Manufacturer verification starting points

These are reference leads, not current stock or procurement evidence:

- [Espressif ESP32-C3 documentation](https://www.espressif.com/en/products/socs/esp32-c3/resources)
- [Analog Devices MAX30102](https://www.analog.com/en/products/max30102.html)
- [Analog Devices MAX30208](https://www.analog.com/en/products/max30208.html)
- [Texas Instruments TLV755P](https://www.ti.com/product/TLV755P)
- [ST USBLC6-2](https://www.st.com/en/protections-and-emi-filters/usblc6-2.html)

Confirm AP2112K and BSS138 ordering information with Diodes Incorporated and the USB4105 drawing with GCT. Record authorized-distributor stock and price checks when procurement is actually performed.
