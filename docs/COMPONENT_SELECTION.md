# Component Selection

**Project:** HealthOS Band  
**Hardware stage:** Iteration 1 - functional sensor prototype  
**Decision date:** 18 October 2026  
**Status:** Owner-approved architecture; draft for client review. Datasheet, schematic and procurement verification pending

## 1. Purpose of this prototype

The first HealthOS PCB will establish a working platform for **heart-rate sensing, SpO2 algorithm development, skin-temperature measurement and basic communication**.

It will be a custom, USB-powered PCB using a solder-down ESP32 module. The board may be larger than the eventual wearable so that its circuitry can be probed, debugged and modified easily. Miniaturization, battery runtime, waterproofing and the complete wearable feature set will be addressed after the sensing platform has been evaluated.

The immediate objectives are to:

- Acquire repeatable red and infrared optical waveforms.
- Develop heart-rate and SpO2 estimates from those waveforms and compare them against suitable references.
- Measure temperature response and assess a skin-facing thermal arrangement.
- Record raw data on a computer for analysis.
- Verify firmware loading, recovery, sensor communication and basic BLE data transfer.

These objectives define a development platform, not a medically validated device. An optical sensor supplying data, or an algorithm displaying an SpO2 number, does not by itself establish measurement accuracy.

## 2. Selection summary

| Function | Selected component | Quantity | Main reason for selection |
|---|---|---:|---|
| Controller, memory and wireless | ESP32-C3-MINI-1-N4X | 1 | Integrated module simplifies processor/RF implementation and provides USB, BLE and 4 MB flash. |
| Optical sensing | MAX30102EFD+T | 1 | Integrates red/IR emitters, detector and acquisition electronics for an initial HR/SpO2 platform. |
| Temperature sensing | MAX30208CLB+ | 1 | Digital contact-temperature sensor suitable for skin-temperature trend experiments. |
| Main 3.3 V regulator | AP2112K-3.3TRG1 | 1 | Simple USB-to-3.3 V supply for the ESP32 module and optical LED circuit. |
| Sensor 1.8 V regulator | TLV75518PDBVR | 1 | Provides the required low-voltage sensor domain. |
| Interface translation | BSS138-7-F | 3 | Open-drain translation for SDA, SCL and optical INT between the voltage domains. |
| USB connector | GCT USB4105-GF-A | 1 | USB-C power and native USB data connection. |
| USB ESD protection | USBLC6-2SC6 | 1 | Protects the USB data interface during handling and connection. |
| Manual controls | Normally open tactile switches | 2 | Reset and firmware-download recovery. |
| Visual indication | 0603 LEDs | 2 | Separate power and firmware-status indication. |
| Service access | Unpopulated 1x4, 2.54 mm UART header footprint | 1 | Backup serial programming/logging and convenient bench access. |
| Supporting circuitry | Resistors, capacitors and test points | As required | Supply stability, USB-C configuration, startup reliability, signal integrity and testability. |

Exact switch/LED part numbers and the complete passive BOM will be selected during schematic development. Quantities above describe the planned functional circuit; they are not a substitute for a checked schematic BOM.

## 3. Component decisions and technical rationale

### 3.1 ESP32-C3-MINI-1-N4X - controller and wireless module

**Role in the system**

The ESP32 will configure both sensors, read optical samples and temperature data, manage timestamps and buffering, run initial processing, and transfer measurements to a computer or phone.

The selected N4 module includes **4 MB flash** and supports **BLE, Wi-Fi and native USB Serial/JTAG**. It is a solder-down component mounted on our custom PCB, not a complete development board.

**Why it was selected**

- It provides sufficient capability for sensor acquisition, buffering and initial HR/SpO2 processing.
- Its native USB interface provides a direct programming and computer-logging path.
- BLE allows wireless communication to be evaluated without adding another radio device.
- The module integrates the processor's flash, clock and RF supporting circuitry, reducing first-board implementation work.
- A module is appropriate because this iteration allows more board area in exchange for easier development.

**Connections and implementation**

- Supply from the regulated 3.3 V rail.
- Communicate with both sensors over a shared I2C bus through the planned voltage-domain interface.
- Receive the MAX30102 interrupt on a dedicated input.
- Connect native USB to the USB-C connector through the ESD/routing network.
- Provide reset, boot-mode control, status indication and UART service access.

**Conditions to verify**

The exact module footprint, GPIO exposure, boot-strapping requirements, USB routing and antenna keepout must be checked. Place the module at a suitable PCB edge and keep its antenna area clear of prohibited copper and nearby metal.

Wi-Fi will remain disabled by default. This selection does not establish that ESP32 power consumption will meet the final band's battery-life target; that decision needs measured workload and power data.

### 3.2 MAX30102EFD+T - integrated optical sensing

**Role in the system**

MAX30102 integrates **red and infrared LEDs, a photodetector, analog acquisition circuitry, an ADC and a sample FIFO**. The controller reads optical samples through I2C and processes them to develop heart-rate and SpO2 estimates.

**Why it was selected**

- Integration removes the need to design a separate optical AFE, emitter and photodiode arrangement for the first board.
- Red and infrared channels provide the measurement inputs needed for SpO2 development and stationary pulse detection.
- The digital interface and FIFO support continuous capture while the controller handles logging and communication.
- It creates a simpler platform for testing acquisition and algorithms before investing in a custom optical layout.

**Connections and implementation**

- Core VDD connects to the 1.8 V sensor rail.
- VLED+ connects to the 3.3 V optical LED supply, with local pulse-current decoupling.
- SDA and SCL connect to the shared sensor-side I2C bus.
- The interrupt output connects to the ESP32 through the planned open-drain translation circuit.
- Ground and power-ground connections follow the package and recommended layout instructions.

**Conditions to verify**

The core must not be powered directly from 3.3 V. Verify supply limits, pin voltage tolerances, LED-current settings, sampling rate, pulse width, FIFO operation and decoupling requirements together.

The optical face must remain accessible to the measurement site. Provide controlled contact and an opaque barrier against ambient light and indicator LEDs. Shared optical windows must transmit the required red and infrared wavelengths.

MAX30102 has no green emitter. Initial evaluation will therefore emphasize stationary measurements. A successful finger demonstration does not establish wrist performance, motion tolerance or clinical SpO2 accuracy. Calibration and reference comparisons remain separate engineering tasks.

### 3.3 MAX30208CLB+ - skin-temperature sensing

**Role in the system**

MAX30208 is a digital contact-temperature sensor. It measures its own die temperature; the mechanical and thermal arrangement must couple that die to the intended skin-contact surface.

**Why it was selected**

- It supports the required temperature-trend experiments without introducing a separate analog measurement chain.
- Its I2C interface allows it to share the optical sensor's bus.
- It can operate from the planned 1.8 V sensor rail, subject to final operating-margin checks.
- It provides a suitable basis for evaluating thermal response and internal-heating bias before designing the final enclosure.

**Connections and implementation**

- Connect VDD to 1.8 V with local decoupling.
- Connect SDA/SCL to the shared sensor-side I2C bus.
- Read temperature periodically in firmware; additional alarm/interrupt wiring is not required for the initial implementation.
- Tie GPIO0/GPIO1 to deliberate levels: they set the I2C address at power-up. Confirm the resulting address against the datasheet table.

**Conditions to verify**

Locate the sensor on a skin-facing tab, island or equivalent thermal structure, away from the ESP32, regulators and optical heat sources. The thermal path to the skin should be stronger than the path to the main PCB.

Sensor accuracy alone does not establish skin-temperature accuracy. Evaluate contact quality, response time, ambient influence and the temperature shift caused by processor/radio activity. The output is intended for skin-temperature trends, not core body-temperature measurement.

### 3.4 AP2112K-3.3TRG1 - main 3.3 V regulator

**Role in the system**

This regulator converts USB 5 V into the main 3.3 V rail. That rail supplies the ESP32 module, MAX30102 LED supply, indicator/interface circuitry and the input of the 1.8 V regulator.

**Why it was selected**

- A linear regulator keeps the first USB-powered circuit simple.
- It requires relatively few supporting components.
- It avoids adding a switching power converter while the initial optical and thermal measurements are being established.

**Conditions to verify**

The device's 600 mA rating is not a guarantee of safe continuous output on this PCB. Confirm load transients, dropout, capacitor requirements, USB source limits and thermal dissipation.

Approximate dissipation is:

```text
Regulator power loss = (input voltage - output voltage) x output current
```

For example, 5 V to 3.3 V at 200 mA dissipates approximately **0.34 W**, excluding quiescent losses. This example is not a measured board-current figure. Keep the regulator away from the temperature-sensing area and verify that the selected package/copper arrangement can dissipate the actual heat.

If the completed power budget fails these checks, the supply design must be revised before PCB fabrication.

### 3.5 TLV75518PDBVR - 1.8 V sensor regulator

**Role in the system**

This regulator converts the main 3.3 V rail into 1.8 V for the MAX30102 core and MAX30208.

**Why it was selected**

- It establishes a sensor supply compatible with the planned components.
- It separates the core-supply voltage requirement from the ESP32 and optical LED supply.
- It avoids applying the controller's 3.3 V rail indiscriminately to sensor-core pins.

**Conditions to verify**

Check the exact package pinout, enable connection, input/output capacitor requirements, output tolerance and startup behavior. Keep local decoupling at each sensor. Separate voltage rails alone do not eliminate shared-ground noise or LED-pulse disturbances; layout and measurement remain necessary.

### 3.6 BSS138-7-F - open-drain signal translation

**Role in the system**

Three MOSFET circuits are planned for:

1. I2C SDA.
2. I2C SCL.
3. MAX30102 interrupt.

Each has pull-ups to 1.8 V on the sensor side and 3.3 V on the controller side. In the conventional topology, the gate is tied to the low-voltage rail, the source faces the sensor and the drain faces the ESP32.

**Why it was selected**

- It provides a simple, discrete interface between the planned voltage domains.
- It suits open-drain signaling and is accessible for probing and rework.
- It keeps sensor-bus operation at 1.8 V while the controller operates at 3.3 V.

**Conditions to verify**

Begin at 100 kHz I2C and verify MOSFET operation at the chosen gate voltage, low-level voltage, pull-up current, bus capacitance and rise time. Confirm the interrupt's output type and behavior when either rail is absent.

The MAX30208 supply range is 1.7-3.6 V, so it does not need a 1.8 V bus. The open question is the MAX30102 SDA/SCL/INT pin rating; if 3.3 V pull-ups are permitted, the translators can be removed.

This topology is not a general-purpose translator for push-pull signals. The exact sensor pin specifications may permit simpler direct connections; any removal of a translator must be justified from those specifications and documented during schematic review.

### 3.7 GCT USB4105-GF-A - USB-C connector

**Role in the system**

USB-C supplies board power and connects the ESP32's native USB interface to the development computer.

**Why it was selected**

- One connector supports power, firmware access and data recording.
- Native ESP32 USB avoids the need for a separate USB-to-UART converter in the main interface.
- The connector provides a practical development connection for repeated bench use.

**Conditions to verify**

Check the exact mechanical drawing and footprint. Connect the duplicated USB 2.0 data contacts correctly, and fit separate 5.1 kohm resistors from CC1 and CC2 to ground for sink/device operation.

These resistors do not provide USB Power Delivery negotiation or permission to draw arbitrary current. Startup current, input capacitance and operating load must suit the actual USB source and enumeration/current requirements.

### 3.8 USBLC6-2SC6 - USB ESD protection

**Role in the system**

This device provides electrostatic-discharge protection for the USB data interface.

**Why it was selected**

The prototype will be handled and connected to cables frequently. Dedicated protection reduces the risk of a discharge reaching the ESP32's USB pins directly.

**Conditions to verify**

Follow the manufacturer's line, VBUS-reference and ground connections. Place the device close to the connector with a short ground-return path. It is a shunt protection device, not a USB converter or protocol interface. Component selection alone does not establish the finished board's ESD performance.

### 3.9 Reset and boot buttons

**Role and reason for selection**

Two normally open momentary switches provide:

- Manual reset through the ESP32 enable/reset circuit.
- Manual firmware-download entry using the documented boot-strapping sequence.

These controls provide a recovery path during early firmware development, including when the application does not start correctly.

The complete pull-up, strap and reset-timing network will follow the exact module reference design. Select the physical switches during schematic/mechanical development and ensure they remain accessible in the test fixture.

### 3.10 Power and firmware-status LEDs

**Role and reason for selection**

- A green power LED confirms the presence of board power.
- A separately controlled status LED indicates initialization, data capture or fault states.

Each LED requires a current-limiting resistor. Use modest current, define the status LED's reset behavior and avoid assigning it to a pin that compromises boot configuration. Position or shield both LEDs so their light cannot contaminate the optical measurement.

### 3.11 UART service header and test points

**Role and reason for selection**

An unpopulated 1x4, 2.54 mm header footprint provides GND, board TX, board RX and a 3.3 V reference for backup serial access. An external adapter is a development tool rather than another populated interface IC.

The adapter must use compatible 3.3 V logic. Avoid connecting a second power source through the reference pin while USB powers the board.

Provide labeled test points for USB 5 V, 3.3 V, 1.8 V, GND, sensor SDA/SCL, optical interrupt and EN. Where practical, expose both sides of the translators and provide a means of measuring sensor supply current. This allows power, communication and reset faults to be measured directly.

### 3.12 Supporting resistors and capacitors

| Supporting circuit | Purpose |
|---|---|
| USB-C CC resistors | Establish sink/device connection behavior. |
| Sensor-bus pull-ups | Define valid idle-high levels and bus rise time on both voltage domains. |
| Module enable/boot components | Establish reliable startup and recoverable download mode. |
| LED series resistors | Limit indicator current. |
| Regulator input/output capacitors | Meet regulator stability and transient requirements. |
| Sensor/module local decoupling | Reduce local supply disturbance and provide short current-return paths. |
| Bulk capacitance | Support processor/radio activity and optical pulse loads, within USB inrush constraints. |
| USB series-resistor footprints | Allow implementation of Espressif's specified USB reference network. |

Final values, package sizes, voltage ratings and quantities will come from the schematic, manufacturer recommendations and calculated operating conditions. Ceramic-capacitor effective capacitance must account for DC-bias derating.

## 4. How the components work together

```text
USB-C 5 V
    |
    +-- AP2112K: 3.3 V --+-- ESP32-C3 module
                         +-- MAX30102 LED supply
                         +-- TLV75518: 1.8 V --+-- MAX30102 core
                                              +-- MAX30208

ESP32 I2C <--> voltage-domain interface <--> MAX30102 + MAX30208
ESP32 input <-- translated optical interrupt <-- MAX30102
ESP32 native USB <--> ESD/routing network <--> computer
ESP32 BLE <--> phone, during wireless testing
```

All circuitry shares a common electrical ground reference. Component placement and return-current routing must limit the influence of radio/LED activity on sensing. Optical contact, thermal contact and RF antenna clearance are part of the design, not details to be postponed until after routing.

## 5. Why external flash is excluded

The selected ESP32 module already contains **4 MB flash**. That storage is shared by firmware, any OTA partitions, configuration and optional logs; it is not all available for raw sensor recording.

For this iteration:

- Store firmware and settings in the module's flash.
- Permit short logs only after defining the partition and write-endurance budget.
- Stream long raw captures to the computer over USB.

A separate flash IC would add circuitry and firmware work without solving an approved first-iteration requirement. Revisit it if later versions need substantial autonomous recording while disconnected from a computer or phone.

## 6. Features deferred to later iterations

| Deferred item | Reason for deferral |
|---|---|
| Battery, charging and fuel gauging | USB power is sufficient for initial sensor validation and removes battery-management variables. |
| OLED and display optics | Computer logging provides better access to waveforms and diagnostics during development. |
| Haptic driver and actuator | Not necessary to establish the initial sensing data path. |
| IMU and motion algorithms | Initial tests are stationary. Add motion sensing when motion-performance evaluation becomes a defined objective. |
| Pressure sensor and vent | Floors/elevation sensing is outside the first measurement scope. |
| External flash | Module storage plus USB logging covers the initial requirement. |
| NFC | No first-iteration function requires it. |
| Final enclosure size and water resistance | These require a later mechanical design and completed sensing/RF evaluation. |

These features remain possible future work. Their deferral does not redefine the longer-term HealthOS product concept.

## 7. What must be checked before ordering and fabrication

The architecture and component direction are approved. The following engineering work remains:

1. **Datasheet review:** exact ordering variants, operating limits, pin tolerances, power sequencing, bus addresses and package instructions.
2. **Schematic completion:** regulator enables, startup/boot circuits, USB implementation, all passive values, unused-pin handling and final GPIO allocation.
3. **Footprint review:** independent comparison of symbols and footprints against manufacturer drawings, including connector and optical orientation.
4. **Power and thermal budget:** simultaneous loads, USB current restrictions, supply droop, regulator dissipation and temperature-sensor bias.
5. **Physical definition:** optical gasket/contact, temperature thermal path, antenna clearance and fixture/debug access.
6. **Procurement review:** authorized-source availability, exact MPN, order quantity, price, lead time and lifecycle status. Current availability is not claimed by this document.
7. **Design verification:** schematic/ERC review followed by PCB layout, DRC, assembly and mechanical checks before fabrication.

Any substitution affecting voltage, interface, footprint, firmware or optical behavior must be reviewed explicitly rather than treated as an automatic equivalent.

## 8. Expected outcome of Iteration 1

A successful first board will be reliably powered, programmed and recovered; communicate with both sensors; record timestamped raw data without unexplained gaps; and support initial HR, SpO2 and temperature evaluations against appropriate references.

Results must distinguish demonstrated behavior from estimates and future goals. The first prototype is intended to generate the evidence needed for the next hardware revision, rather than establish production readiness or clinical accuracy.
