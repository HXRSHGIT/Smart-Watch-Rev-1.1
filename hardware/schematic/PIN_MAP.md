# Pin map

Produced by `tools/pinmap.py` from the KiCad netlist. Do not edit by hand.

## U1  nRF54L15-QFAA  (QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm)

| Pin | Name | Net | Also connected to |
|---|---|---|---|
| 1 | P1.00/XL1 | (wire) | X1.1 |
| 2 | P1.01/XL2 | (wire) | X1.2 |
| 3 | P1.02/NFC1 | (not connected) |  |
| 4 | P1.03/NFC2 | (not connected) |  |
| 5 | P1.04/AIN0 | (not connected) |  |
| 6 | P1.05/AIN1 | (not connected) |  |
| 7 | P1.06/AIN2 | (not connected) |  |
| 8 | P1.07/AIN3 | (not connected) |  |
| 9 | P1.08 | PMIC_IRQ | U7.8 |
| 10 | VDD | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| 11 | P2.00 | CS_FLASH | R18.2, U8.1 |
| 12 | P2.01 | SPI_SCK | TP8.1, U2.A2, U8.6 |
| 13 | P2.02 | SPI_MOSI | TP9.1, U2.A4, U8.5 |
| 14 | P2.03 | TEMP_INT | U4.10 |
| 15 | P2.04 | SPI_MISO | TP10.1, U2.A3, U8.2 |
| 16 | P2.05 | CS_PPG | U2.A5 |
| 17 | P2.06 | CHG_FLAG | R15.2, U6.E3 |
| 18 | P2.07/SWO | SWO | J3.6 |
| 19 | P2.08 | LED_BOOST_EN | R11.1, U5.4 |
| 20 | P2.09 | PPG_GPIO1 | R5.2, U2.B3 |
| 21 | P2.10 | PPG_GPIO2 | U2.B4 |
| 22 | VDD | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| 23 | P0.00 | PPG_INT | R4.2, TP11.1, U2.B2 |
| 24 | P0.01 | IMU_INT1 | U3.4 |
| 25 | SWDIO | SWDIO | J3.2 |
| 26 | SWDCLK | SWDCLK | J3.4 |
| 27 | P0.02 | IMU_INT2 | U3.9 |
| 28 | P0.03 | I2C_SDA | R10.2, TP6.1, U3.14, U4.8, U7.13 |
| 29 | P0.04 | I2C_SCL | R9.2, TP7.1, U3.13, U4.9, U7.14 |
| 30 | nRESET | (wire) | C13.1, R1.2 |
| 31 | ANT | RF_ANT | L2.1 |
| 32 | VSS_PA | VSS_PA | C6.2, NT1.2 |
| 33 | DECRF | (wire) | C12.1, C2.1, C5.1, FB1.2, U1.43 |
| 34 | XC1 | (wire) | X2.1 |
| 35 | XC2 | (wire) | X2.3 |
| 36 | VDD | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| 37 | P1.09 | (not connected) |  |
| 38 | P1.10 | (not connected) |  |
| 39 | P1.11/AIN4 | (not connected) |  |
| 40 | P1.12/AIN5 | (not connected) |  |
| 41 | P1.13/AIN6 | (not connected) |  |
| 42 | P1.14/AIN7 | (not connected) |  |
| 43 | DECA | (wire) | C12.1, C2.1, C5.1, FB1.2, U1.33 |
| 44 | VSS | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| 45 | DECD | (wire) | C1.1, FB1.1, L1.1 |
| 46 | DCC | (wire) | L1.2 |
| 47 | VDD | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| 48 | VDD | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| 49 | VSS_EP | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |

## U2  MAX86141ENP+  (MAX86141_WLP-20_2.048x1.848mm_P0.4mm)

| Pin | Name | Net | Also connected to |
|---|---|---|---|
| A1 | VLED | VLED | C18.1, D1.2, D1.5, R12.2, R13.2, TP3.1 |
| A2 | SCLK | SPI_SCK | TP8.1, U1.12, U8.6 |
| A3 | SDO | SPI_MISO | TP10.1, U1.15, U8.2 |
| A4 | SDI | SPI_MOSI | TP9.1, U1.13, U8.5 |
| A5 | CSB | CS_PPG | U1.16 |
| B1 | LED3_DRV | (wire) | R8.1 |
| B2 | INT | PPG_INT | R4.2, TP11.1, U1.23 |
| B3 | GPIO1 | PPG_GPIO1 | R5.2, U1.20 |
| B4 | GPIO2 | PPG_GPIO2 | U1.21 |
| B5 | VREF | (wire) | C17.1 |
| C1 | LED2_DRV | (wire) | R7.1 |
| C2 | VDD_DIG | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| C3 | GND_DIG | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| C4 | GND_ANA | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| C5 | PD_GND | (wire) | NT3.2, PD1.5, PD2.5 |
| D1 | LED1_DRV | (wire) | R6.1 |
| D2 | VDD_ANA | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| D3 | PGND | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| D4 | PD2_IN | (wire) | PD2.1, PD2.2, PD2.3, PD2.4, PD2.6, PD2.7, PD2.8 |
| D5 | PD1_IN | (wire) | PD1.1, PD1.2, PD1.3, PD1.4, PD1.6, PD1.7, PD1.8 |

## U3  BMI270  (Bosch_LGA-14_3x2.5mm_P0.5mm)

| Pin | Name | Net | Also connected to |
|---|---|---|---|
| 1 | SDO | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| 2 | ASDx | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| 3 | ASCx | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| 4 | INT1 | IMU_INT1 | U1.24 |
| 5 | VDDIO | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| 6 | GNDIO | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| 7 | GND | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| 8 | VDD | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| 9 | INT2 | IMU_INT2 | U1.27 |
| 10 | OCSB | (not connected) |  |
| 11 | OSDO | (not connected) |  |
| 12 | CSB | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| 13 | SCx_(SCL) | I2C_SCL | R9.2, TP7.1, U1.29, U4.9, U7.14 |
| 14 | SDx_(SDA) | I2C_SDA | R10.2, TP6.1, U1.28, U4.8, U7.13 |

## U4  MAX30208  (MAX30208_TLGA-10_2x2mm)

| Pin | Name | Net | Also connected to |
|---|---|---|---|
| 1 | VDD | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| 2 | VDD | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| 3 | VDD | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| 4 | GND | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| 5 | GND | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| 6 | GND | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| 7 | GPIO1 | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| 8 | SDA | I2C_SDA | R10.2, TP6.1, U1.28, U3.14, U7.13 |
| 9 | SCL | I2C_SCL | R9.2, TP7.1, U1.29, U3.13, U7.14 |
| 10 | GPIO0 | TEMP_INT | U1.14 |

## U5  TPS61240DRVR  (WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm)

| Pin | Name | Net | Also connected to |
|---|---|---|---|
| 1 | GND | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| 2 | VOUT | (wire) | C23.1, R12.1, U5.3 |
| 3 | FB | (wire) | C23.1, R12.1, U5.2 |
| 4 | EN | LED_BOOST_EN | R11.1, U1.19 |
| 5 | L | (wire) | L5.2 |
| 6 | VIN | VSYS | C22.1, C27.1, C28.1, L5.1, R13.1, TP2.1, U7.20, U7.32, U7.4 |
| 7 | PowerPAD | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |

## U6  OCVPB21-13F6  (OCVPB21-13F6_WLCSP-13_P0.4mm)

| Pin | Name | Net | Also connected to |
|---|---|---|---|
| A1 | USB_DP | (not connected) |  |
| A2 | USB_IND | (not connected) |  |
| A3 | GND_DATA | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| B1 | USB_DM | (not connected) |  |
| B2 | OUT_5V | VBUS_PROT | C24.1, C25.1, U7.21 |
| B3 | USB_INC | (not connected) |  |
| C2 | RECTIF | (not connected) |  |
| C3 | GND_ESD | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| D1 | IN_A | (wire) | J1.1 |
| D3 | IN_B | (wire) | J2.1 |
| E1 | RLIM | (wire) | R14.1 |
| E2 | GND_BRIDGE | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| E3 | FLAG | CHG_FLAG | R15.2, U1.17 |

## D1  SFH 7016  (SFH7016_1.85x1.65mm)

| Pin | Name | Net | Also connected to |
|---|---|---|---|
| 1 | K_IR_940_nm | (wire) | R7.2 |
| 2 | A | VLED | C18.1, D1.5, R12.2, R13.2, TP3.1, U2.A1 |
| 3 | K_green_530_nm | (wire) | R6.2 |
| 4 | K_red_655_nm | (wire) | R8.2 |
| 5 | A | VLED | C18.1, D1.2, R12.2, R13.2, TP3.1, U2.A1 |
| 6 | NC | (not connected) |  |

## PD1  VEMD8080  (VEMD8080_4.8x2.5mm)

| Pin | Name | Net | Also connected to |
|---|---|---|---|
| 1 | K | (wire) | PD1.2, PD1.3, PD1.4, PD1.6, PD1.7, PD1.8, U2.D5 |
| 2 | K | (wire) | PD1.1, PD1.3, PD1.4, PD1.6, PD1.7, PD1.8, U2.D5 |
| 3 | K | (wire) | PD1.1, PD1.2, PD1.4, PD1.6, PD1.7, PD1.8, U2.D5 |
| 4 | K | (wire) | PD1.1, PD1.2, PD1.3, PD1.6, PD1.7, PD1.8, U2.D5 |
| 5 | A | (wire) | NT3.2, PD2.5, U2.C5 |
| 6 | K | (wire) | PD1.1, PD1.2, PD1.3, PD1.4, PD1.7, PD1.8, U2.D5 |
| 7 | K | (wire) | PD1.1, PD1.2, PD1.3, PD1.4, PD1.6, PD1.8, U2.D5 |
| 8 | K | (wire) | PD1.1, PD1.2, PD1.3, PD1.4, PD1.6, PD1.7, U2.D5 |

## PD2  VEMD8080  (VEMD8080_4.8x2.5mm)

| Pin | Name | Net | Also connected to |
|---|---|---|---|
| 1 | K | (wire) | PD2.2, PD2.3, PD2.4, PD2.6, PD2.7, PD2.8, U2.D4 |
| 2 | K | (wire) | PD2.1, PD2.3, PD2.4, PD2.6, PD2.7, PD2.8, U2.D4 |
| 3 | K | (wire) | PD2.1, PD2.2, PD2.4, PD2.6, PD2.7, PD2.8, U2.D4 |
| 4 | K | (wire) | PD2.1, PD2.2, PD2.3, PD2.6, PD2.7, PD2.8, U2.D4 |
| 5 | A | (wire) | NT3.2, PD1.5, U2.C5 |
| 6 | K | (wire) | PD2.1, PD2.2, PD2.3, PD2.4, PD2.7, PD2.8, U2.D4 |
| 7 | K | (wire) | PD2.1, PD2.2, PD2.3, PD2.4, PD2.6, PD2.8, U2.D4 |
| 8 | K | (wire) | PD2.1, PD2.2, PD2.3, PD2.4, PD2.6, PD2.7, U2.D4 |

## AE1  2450AT18A0100001E  (Johanson_2450AT18A0100001E_1206)

| Pin | Name | Net | Also connected to |
|---|---|---|---|
| 1 | FEED | (wire) | R3.2 |
| 2 | NC_(solder_for_anchor) | (not connected) |  |

## J1  Pogo pad  (Pogo_Pad_D2.6mm)

| Pin | Name | Net | Also connected to |
|---|---|---|---|
| 1 | Pin_1 | (wire) | U6.D1 |

## J2  Pogo pad  (Pogo_Pad_D2.6mm)

| Pin | Name | Net | Also connected to |
|---|---|---|---|
| 1 | Pin_1 | (wire) | U6.D3 |

## J3  TC2030-NL  (Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical)

| Pin | Name | Net | Also connected to |
|---|---|---|---|
| 1 | VTREF | +1V8 | C10.1, C15.1, C16.1, C19.1, C20.1, C21.1, C29.1, C3.1, C31.1, C32.1 ... |
| 2 | SWDIO | SWDIO | U1.25 |
| 3 | nRESET | NRESET | R1.1 |
| 4 | SWDCLK | SWDCLK | U1.26 |
| 5 | GND | GND | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2 ... |
| 6 | SWO | SWO | U1.18 |
