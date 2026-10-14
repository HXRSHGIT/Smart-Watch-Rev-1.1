# HealthOS Band — hardware engineer  requirements


## 1. Purpose

HealthOS Band is a lightweight, continuously worn fitness and wellness band inspired by the low-profile form of WHOOP. It adds a very small monochrome display for silent visual reminders and short status information without becoming a conventional smartwatch.

This document defines the intended product, first-prototype scope, candidate architecture, open decisions and required engineering evidence. The professional hardware engineer should independently review the architecture and may replace components or circuit approaches when supported by documented size, power, availability, performance, cost or manufacturing advantages.


## 2. Product concept

The product should remain small, light and comfortable for continuous day-and-night use. It should not have the large face, weight or interaction model of a smartwatch.

Two basic appearances are planned around one electronic platform:

1. **Basic Stealth:** a small OLED hidden behind a matte dead-front window. The front appears dark when the display is off.
2. **Basic OLED:** the same small OLED is visible through a compact capsule-shaped window.

The display should normally remain off. It wakes briefly for reminders, measurements, charging status and selected gestures. Both versions should use the same PCB, firmware interface and display resolution where practical; only the optical cover and industrial design should differ.

## 3. Target user and product position

The first product is a **consumer fitness and wellness band**,  It is intended for users who want continuous health/activity trends, sleep tracking and quiet reminders in a lighter product than a smartwatch.

 Heart rate, SpO2, temperature, sleep, calories and recovery outputs must be presented as estimates until the complete product

## 4. First-prototype requirements — P0

### 4.1 Health sensing

- Continuous and resting heart-rate measurement.
- Workout heart rate and configurable heart-rate zones.
- Spot SpO2 measurement and power-managed periodic sampling during selected sleep periods.
- Skin-temperature trend measurement. The product should distinguish trend tracking from core body-temperature measurement.
- Motion data suitable for activity and sleep algorithms.
- Pressure data suitable for relative altitude, floors climbed and environmental compensation.
- Raw or minimally processed sensor data access during engineering validation.
- Time synchronization across PPG, motion and other sensors where required for motion-artifact reduction.

### 4.2 Fitness and activity outputs

- Step count.
- Estimated distance using step length and optional phone GPS.
- Active minutes and inactivity periods.
- Resting, active and total calorie estimates.
- Floors climbed and relative elevation change.
- Automatic detection of broad activity classes: walking, running, cycling, stair climbing, inactivity and generic workout.

- Confidence handling: uncertain activities should be reported as generic activity or require user confirmation instead of being assigned a false precise label.

Calories are not directly measured. The algorithm will combine heart rate, motion, duration, user profile and activity type. Calorie values must be labelled as estimates.

### 4.3 Sleep outputs

- Sleep start and wake detection.
- Total sleep duration and interruptions.
- Resting heart-rate trend during sleep.
- Motion-based sleep quality indicators.
- Hardware support for later respiratory-rate, HRV and sleep-stage algorithms, without claiming these are validated in the first prototype.

### 4.4 Display and reminders

- Very small monochrome OLED; current evaluation class is 64 × 32 pixels.
- Candidate display size: approximately 14.5 × 11.6 mm module with an active area around 11.2 × 5.6 mm. The engineer must verify the exact orderable module and mechanical interface.
- Short icons and minimal information rather than menus or app-like screens.
- Icons for water, medicine, yoga, gym, study, walking and other scheduled reminders.
- Haptic vibration paired with visual reminders.
- Battery and charging indication.
- Measurement result display for heart rate and SpO2.
- Short goal-progress and workout indicators.
- Simple, low-frame-rate icon animation.
- Display activation by gesture, tap or scheduled event, subject to false-wake and battery testing.
- Display-off state must not back-power the module through communication pins.
- The Stealth cover must be evaluated for off-state appearance, brightness loss, contrast, viewing angle and outdoor readability.

Water, medicine, study, yoga and similar reminders are scheduled or app-triggered. The device is not expected to prove that the user completed the action.

### 4.5 Haptics

- Quiet, clearly perceptible wrist vibration.
- Exact LRA should be selected using enclosure space, resonance, impedance, peak current and mechanical mounting.
- Multiple recognizable vibration patterns for reminders, goal completion, alarms and error/status feedback.

### 4.6 Connectivity, storage and programming

- Bluetooth Low Energy connection to Android and/or iOS; supported phone platforms require owner confirmation.
- Secure pairing and authenticated firmware update over BLE.
- External nonvolatile storage for offline sensor summaries and engineering data when the phone is absent.
- Factory programming, erase, recovery and debug through accessible SWD pads.
- Production test access for critical rails, reset and selected buses.
- Pogo charging contacts are not required to provide consumer USB data.
- Device time, configuration, reminders and user profile synchronize through the phone.

### 4.7 Power and charging

- Single-cell protected rechargeable LiPo battery with a pack NTC.
- Protected, reversible two-contact pogo charging input.
- Battery charging, fuel-gauge support and ship/storage mode.
- Safe behavior with reversed pogo orientation, contact bounce, shorts and poor contact resistance.
- Battery percentage and low-battery states.
- Provisional product goal: at least five days of normal use, with seven days as a stretch goal. The owner must approve the target after battery volume and measurement schedules are modeled.
- No always-on display.
- Power modes must coordinate radio, flash writes, haptics, display, optical pulses and NFC so combined peaks remain within the cell, protection and regulator limits.
- Charging-current and temperature limits must follow the selected cell manufacturer's requirements.

## 5. P1 features — useful after the core prototype

- HRV trends after beat-to-beat timing quality is validated.
- Respiratory-rate estimation during sleep.
- Recovery/readiness and stress estimates.
- Automatic recognition of additional exercise categories after collecting labelled user data.
- Phone-assisted GPS routes and pace for walking, running and cycling.
- Fall-event research; no emergency claim without extensive validation.
- User-configurable reminder icons and vibration patterns.
- Data export and user-controlled deletion through the app.




## 8. Candidate component architecture

The following parts are starting candidates, not mandatory selections:

| Function | Current candidate | Review requirement |
|---|---|---|
| BLE and application controller | Nordic nRF5340-QKAA | Compare against a suitable nRF54 device for area, power, GPIO, SDK maturity, availability and migration cost before schematic freeze. |
| PMIC, charger and fuel gauge | Nordic nPM1300-QEAA | Recalculate every rail and concurrent peak; verify selected battery and charging profile. |
| Optical AFE | Analog Devices MAX86141 | Confirm logic levels, LED supply, timing, optical design and assembly capability. |
| Optical emitter | ams OSRAM SFH7016 | Validate green/red/IR current, thermal rise, window loss and supply. |
| Optical detectors | Two Vishay VEMD8080 | Validate detector spacing, capacitance, saturation, ambient-light behavior and crosstalk. |
| Motion | Bosch BMI270 | Verify orientation, interrupt use, power modes and software support. |
| Pressure | Bosch BMP390 | Provide a waterproof breathable vent and contamination protection. |
| Skin temperature | Analog Devices MAX30208 | Requires a skin-facing thermal path isolated from PCB and battery heat. |
| Haptic driver | TI DRV2605L | Select and validate the exact LRA and mounting. |
| External flash | Winbond W25Q32RVXHJQ | Verify package assembly, firmware support, deep-sleep current and data-retention needs. |
| Active NFC | ST ST25R210 | Conditional on an approved active-reader use case and measured power/range. |
| Pogo-input protection | ST OCVPB21-13F6 | Verify current limit, contact heating, ESD and charging interaction. |
| Display | 0.49-inch 64 × 32 OLED class | Select exact module, color, flex connector, cover stack and power-off topology. |

The engineer should also review whether separate optical, NFC or display rails remain justified after the final duty cycles and battery are known.



## 13. Prototype acceptance gates

Fabrication of prototypes may proceed only after schematic, footprint, mechanical and layout reviews are complete. Production release requires stronger evidence than prototype release.

At minimum, prototype validation should cover:

- Repeatable SWD programming, erase and recovery.
- Correct rail startup, shutdown and fault behavior.
- Sleep current and complete battery-life measurement against the approved usage profile.
- Worst-case simultaneous load testing for optical pulses, radio, flash, display and haptics.
- Pogo orientation, contact resistance, charging current and temperature.
- Battery NTC, protection and charge-termination behavior.
- BLE range, connection reliability and antenna tuning in the final worn enclosure.
- Sensor identity, communication and synchronized data capture.
- Heart-rate and PPG waveform quality at rest and during motion.
- SpO2 evaluation against an appropriate reference across realistic conditions.
- Optical crosstalk, ambient light, fit and skin-contact testing.
- Temperature response and separation from internal heat sources.
- Pressure-vent response and environmental robustness.
- Display readability, dead-front behavior, sleep current and power-off leakage.
- Haptic strength, noise, peak current and mounting durability.
- NFC range and power only if the active NFC feature is retained.
- ESD, EMC pre-compliance, thermal, sweat, corrosion and water-resistance testing appropriate to the approved product target.

## 14. Success criteria

The first engineering prototype succeeds when:

- the complete device can be safely powered, programmed and recovered;
- all required sensors, BLE, display, haptics, storage and charging function reliably;
- the measured battery life meets the owner-approved profile;
- BLE and sensing performance remain acceptable in the final enclosure and on the wrist;
- health and activity outputs are explicitly characterized against suitable references;
- all design-rule, footprint, RF, optical, thermal, battery and safety findings are documented and resolved or formally accepted for the next prototype;
- no one describes the design as production-ready without evidence from assembled hardware.

## 15. Recommended development phases

1. **Requirements freeze:** resolve the blocking owner decisions and agree on measurable targets.
2. **Architecture freeze:** select controller, battery, display, haptic and  approve the power tree.
3. **Schematic and footprint review:** complete circuit capture, exact BOM and independent package checks.
4. **Mechanical and RF definition:** enclosure stack, optical system, thermal path, vent, PCB outline, stackup and antennas.
5. **PCB layout and review:** placement, routing, signal/power integrity, DFM and DFT.
6. **Prototype build and bring-up:** assemble a small quantity and follow a current-limited staged test procedure.
7. **Performance validation:** battery, RF, optical, thermal, charging, environmental and algorithm data collection.
8. **Rev C correction:** resolve prototype findings before considering certification or production tooling.

