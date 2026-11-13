# Sensor Time Synchronisation

Brief §4.1: "Time synchronization across PPG, motion and other sensors where required for motion-artifact reduction."

---

## 1. Why it matters

The motion-artifact algorithm (optical-ppg HR_MOTION_ARTIFACT) compares PPG and accelerometer spectra and correlations over 8 s windows. Two things go wrong if the streams aren't aligned:

1. **Offset:** a constant delay between streams. A phase error, it matters for adaptive filters, less for spectral methods.
2. **Rate mismatch:** each sensor runs on its **own oscillator**. A nominal "100 sps" from the MAX86141 and "100 Hz" from the BMI270 differ by up to their oscillator tolerances. Over an 8 s window, a 1 % rate error is 80 ms, which smears the spectrum. Over a night it adds up to minutes.

Required accuracy for this band (proposed):

- **≤ 1 sample period (10 ms at 100 sps)** relative alignment within each window;
- **no long-term drift** (rates measured, not assumed).

## 2. Time bases available

| Clock | Resolution | Source |
|---|---|---|
| nRF RTC on 32.768 kHz | 30.5 µs; ±20–50 ppm with a crystal (crystal-dependent) | SoC |
| BMI270 sensor time | **39.0625 µs per LSB**, 24-bit, written into FIFO frames | [Bosch](https://community.bosch-sensortec.com/t5/MEMS-sensors-forum/BMI270-timestamp-conversion/m-p/9397) |
| MAX86141 sample clock | internal oscillator; no timestamp in the FIFO | ADI (check the tolerance in the DS) |
| BMP390, MAX30208 | slow (1 Hz, 1/min): SoC time at read is enough | — |

**Reference = SoC RTC.** Fit the 32.768 kHz crystal (TRADE_STUDY_MCU pin budget includes it). The internal RC is worse by orders of magnitude.

## 3. Method

### 3.1 Timestamp every FIFO interrupt in SoC time

- On the MAX86141 FIFO-watermark INT and the BMI270 watermark INT, capture RTC (or a TIMER) **in the GPIO interrupt via PPI/DPPI hardware capture**, not in software, so latency is fixed and sub-microsecond.
- Read the FIFO and note **N samples**.

### 3.2 Estimate each sensor's true sample period continuously

Between two interrupts:

```
period_est = (t_int[k] - t_int[k-1]) / N_samples_between
```

Smooth it with a slow filter (minutes time constant). This is the measured rate in SoC ticks. Use it instead of the nominal ODR.

### 3.3 Assign a time to every sample

Sample i of a burst ending at t_int gets `t_i = t_int − (N − 1 − i) × period_est − latency`, where latency is the fixed watermark-to-INT delay (measure once).

For the BMI270, **cross-check with its own sensor-time frames**: they give an independent rate estimate at 39 µs resolution.

### 3.4 Resample onto a common grid

Before the HR algorithm, resample PPG and accel onto one 25/50/100 Hz grid. Linear interpolation is adequate at these bandwidths; cubic is better for HRV peak timing.

### 3.5 Raw-data export

Every exported sample carries:

- a per-sensor **sample counter** (gap detection);
- SoC time;
- the **current period estimate**.

Then offline analysis can redo the alignment (BLE_SECURITY_DFU §3).

### 3.6 Iteration 1: no MAX86141 INT pin (polled FIFO)

The first board leaves the MAX86141 INT ball open (`hardware/JLCPCB_DESIGN_RULES.md`), so §3.1 cannot timestamp its interrupt. The BMI270 INT stays wired and §3.1 to §3.3 are unchanged for it. For the MAX86141:

- Wake on the RTC at a fixed interval, read the FIFO sample counter and the overflow counter over SPI, burst-read the samples, and note SoC time at the read (RTC capture at the start of the SPI transfer).
- Keep a running total `n` of samples produced (read plus still in the FIFO, plus overflow). Each read gives `t_read = t0 + (n + u) * P`, where `u` in [0, 1) is the unknown age of the newest sample. Fit `t0` and `P` by least squares over many reads, using `n + 0.5`. This replaces `t_int` in §3.2 and §3.3.
- Add 3 ms or more of random jitter to the poll interval, so the reads do not stay locked to the sample clock. Poll at least four times per FIFO fill time (128 samples) so the FIFO cannot overflow when BLE or flash work delays a read.
- Simulation (idealised: exact counter, no lost samples, 0.5 ms read jitter, up to 50 ppm clock error, 400 trials each): with 3 ms dither and 30 reads the worst error was 0.46 to 0.69 of one sample period at 100, 50 and 25 sps, and 0.24 with 120 reads. The requirement is 1.0 (§1). This shows feasibility, not proof.
- Validation: the tap test and drift test in §4, unchanged. If the result is worse than ±1 sample, the product board brings INT back (1st-order HDI with a laser via under ball B2).

## 4. Validation

1. **Tap test:** tap the sensor area sharply. The tap shows up in the accel and, mechanically, as a spike in the PPG. Cross-correlate the two. Lag after alignment should be within ±1 sample. Repeat 50 times and check the spread.
2. **Drift test:** log 8 h. Compare period_est against nominal for each sensor and report ppm. Confirm the aligned streams show no growing lag (repeat the tap test at the start and end).
3. **Temperature:** repeat the drift test at 15 °C and 35 °C, since oscillators drift with temperature.
