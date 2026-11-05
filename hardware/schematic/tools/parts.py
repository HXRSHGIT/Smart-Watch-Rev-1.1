"""Chip symbols for the Smart Watch board. Pin numbers and names come from the datasheet pin tables
listed in hardware/DATASHEET_INDEX.md; check.py compares the nRF54L15 symbol with the pin table CSV.

Layout rule (STYLE_GUIDE.md): supply pins on top, ground pins at the bottom, signals left and right, so a
sheet can be drawn left to right with the supply row above the signal row. A pin tuple may carry a 4th item,
a list of further pad numbers of the same net that are stacked on the one drawn pin (hidden).
"""
from kigen import Unit, chip_symbol

PI, PO, BI, PA, NC, OD, TS = ("power_in", "power_out", "bidirectional", "passive", "no_connect",
                              "open_collector", "tri_state")
DS = "hardware/datasheets/"


def nrf54l15():
    u1 = Unit("nRF54L15-QFAA  power, clocks, RF, debug",
              top=[("47", "VDD", PI), ("48", "VDD", PI), ("10", "VDD", PI), ("22", "VDD", PI), ("36", "VDD", PI)],
              bottom=[("32", "VSS_PA", PA), None, ("44", "VSS", PI), ("49", "VSS_EP", PI)],
              left=[("46", "DCC", PA), None, ("45", "DECD", PA), None, None, None, ("43", "DECA", PA), ("33", "DECRF", PA),
                    None, None, None, None, ("25", "SWDIO", BI), ("26", "SWDCLK", "input"), ("30", "nRESET", "input")],
              right=[("35", "XC2", PA), None, None, ("34", "XC1", PA), None, ("1", "P1.00/XL1", BI), None,
                     ("2", "P1.01/XL2", BI), None, ("31", "ANT", PA)], width=22.86)
    u2 = Unit("GPIO ports P0 and P1",
              right=[("23", "P0.00", BI), ("24", "P0.01", BI), ("27", "P0.02", BI), ("28", "P0.03", BI), ("29", "P0.04", BI),
                     None, ("9", "P1.08", BI), None,
                     ("3", "P1.02/NFC1", BI), ("4", "P1.03/NFC2", BI), ("5", "P1.04/AIN0", BI), ("6", "P1.05/AIN1", BI),
                     ("7", "P1.06/AIN2", BI), ("8", "P1.07/AIN3", BI), ("37", "P1.09", BI),
                     ("38", "P1.10", BI), ("39", "P1.11/AIN4", BI), ("40", "P1.12/AIN5", BI), ("41", "P1.13/AIN6", BI),
                     ("42", "P1.14/AIN7", BI)], width=15.24)
    u3 = Unit("GPIO port P2",
              right=[("11", "P2.00", BI), ("12", "P2.01", BI), ("13", "P2.02", BI), ("15", "P2.04", BI),
                     ("16", "P2.05", BI), None, ("14", "P2.03", BI), ("17", "P2.06", BI), ("18", "P2.07/SWO", BI),
                     ("19", "P2.08", BI), ("20", "P2.09", BI), ("21", "P2.10", BI)], width=15.24)
    return chip_symbol("smartwatch", "nRF54L15-QFAA", "U", [u1, u2, u3],
                       footprint="Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm",
                       datasheet=DS + "nRF54L15_datasheet_v1.0.pdf",
                       description="Nordic nRF54L15 SoC, QFN48 6x6 mm (QFAA). Pin table 79.")


def max86141():
    u = Unit("MAX86141 optical front end",
             top=[("A1", "VLED", PI), None, None, None, None, ("D2", "VDD_ANA", PI), ("C2", "VDD_DIG", PI)],
             bottom=[("D3", "PGND", PI), ("C4", "GND_ANA", PI), ("C3", "GND_DIG", PI)],
             left=[("B2", "INT", OD), None, None, None, None, ("B3", "GPIO1", BI), ("B4", "GPIO2", BI), None,
                   ("A5", "CSB", "input"), ("A2", "SCLK", "input"), ("A4", "SDI", "input"), ("A3", "SDO", TS)],
             right=[("D1", "LED1_DRV", PA), None, None, ("C1", "LED2_DRV", PA), None, None, ("B1", "LED3_DRV", PA)] + [None] * 7 + [
                    ("C5", "PD_GND", PA), ("D4", "PD2_IN", PA), ("D5", "PD1_IN", PA), None, ("B5", "VREF", PA)],
             width=15.24)
    return chip_symbol("smartwatch", "MAX86141", "U", [u], footprint="smartwatch:MAX86141_WLP-20_2.048x1.848mm_P0.4mm",
                       datasheet=DS + "MAX86141_rev5.pdf",
                       description="ADI MAX86141 two-channel optical AFE, 20-bump WLP 5x4, 0.4 mm pitch. Rev 5 pin table.")


def bmi270():
    u = Unit("BMI270 motion sensor",
             top=[("8", "VDD", PI), ("5", "VDDIO", PI)], bottom=[("7", "GND", PI), ("6", "GNDIO", PI)],
             left=[("12", "CSB", "input"), ("2", "ASDx", "input"), ("3", "ASCx", "input"), None,
                   ("13", "SCx (SCL)", "input"), ("14", "SDx (SDA)", BI), None, ("1", "SDO", "input")],
             right=[("4", "INT1", BI), ("9", "INT2", BI), None, ("10", "OCSB", "input"), ("11", "OSDO", "output")],
             width=12.7)
    return chip_symbol("smartwatch", "BMI270", "U", [u], footprint="Package_LGA:Bosch_LGA-14_3x2.5mm_P0.5mm",
                       datasheet=DS + "BMI270.pdf", description="Bosch BMI270 6-axis IMU, LGA-14. Table 22 pin-out.")


def max30208():
    u = Unit("MAX30208 skin temperature",
             top=[("1", "VDD", PI), ("2", "VDD", PI), ("3", "VDD", PI)],
             bottom=[("4", "GND", PI), ("5", "GND", PI), ("6", "GND", PI)],
             left=[("8", "SDA", BI), ("9", "SCL", "input"), None, ("7", "GPIO1", "input")],
             right=[("10", "GPIO0", BI)], width=12.7)
    return chip_symbol("smartwatch", "MAX30208", "U", [u], footprint="smartwatch:MAX30208_TLGA-10_2x2mm",
                       datasheet=DS + "MAX30208.pdf", description="ADI MAX30208 digital temperature sensor, thin LGA-10.")


def tps61240():
    u = Unit("TPS61240 5 V boost",
             left=[("5", "L", PA), None, ("6", "VIN", PI), ("4", "EN", "input")],
             right=[("2", "VOUT", PO), ("3", "FB", "input")],
             bottom=[("1", "GND", PI), ("7", "PowerPAD", PI)], width=12.7)
    return chip_symbol("smartwatch", "TPS61240", "U", [u], footprint="Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm",
                       datasheet=DS + "TPS61240.pdf", description="TI TPS61240 fixed 5.0 V boost converter, WSON-6 (DRV).")


def ocvpb21():
    u = Unit("OCVPB21-13F6 charge input protection",
             top=[("C2", "RECTIF", PA), ("A2", "USB_IND", PA), ("B3", "USB_INC", PA), ("A1", "USB_DP", PA),
                  ("B1", "USB_DM", PA)],
             left=[("D1", "IN_A", PA), ("D3", "IN_B", PA)],
             right=[("B2", "OUT_5V", PO), None, None, None, None, ("E3", "FLAG", OD)],
             bottom=[("E1", "RLIM", PA), None, ("E2", "GND_BRIDGE", PI), ("C3", "GND_ESD", PI), ("A3", "GND_DATA", PI)],
             width=15.24)
    return chip_symbol("smartwatch", "OCVPB21-13F6", "U", [u],
                       footprint="smartwatch:OCVPB21-13F6_WLCSP-13_P0.4mm", datasheet=DS + "OCVPB21-13F6.pdf",
                       description="ST OCVPB21-13F6 ESD, overvoltage and overcurrent protection with bridge, WLCSP-13.")


def sfh7016():
    u = Unit("SFH 7016 emitter",
             top=[("2", "A", PA), ("5", "A", PA)],
             left=[("3", "K green 530 nm", PA), None, None, ("1", "K IR 940 nm", PA), None, None, ("4", "K red 655 nm", PA)],
             bottom=[("6", "NC", NC)], width=15.24)
    return chip_symbol("smartwatch", "SFH7016", "D", [u], footprint="smartwatch:SFH7016_1.85x1.65mm",
                       datasheet=DS + "SFH7016.pdf", description="ams OSRAM SFH 7016 green/red/IR emitter. Pin table p.14.")


def vemd8080():
    u = Unit("", top=[("1", "K", PA, ["2", "3", "4", "6", "7", "8"])], bottom=[("5", "A", PA)], width=5.08)
    return chip_symbol("smartwatch", "VEMD8080", "PD", [u], footprint="smartwatch:VEMD8080_4.8x2.5mm",
                       datasheet=DS + "VEMD8080.pdf",
                       description="Vishay VEMD8080 PIN photodiode. Pin 5 anode; the seven cathode pads 1-4 and 6-8 are one net and are drawn as one pin.")


def antenna():
    u = Unit("2450AT18A0100001E antenna", left=[("1", "FEED", PA)], right=[("2", "NC (solder for anchor)", PA)], width=12.7)
    return chip_symbol("smartwatch", "Chip_Antenna_2450AT18A", "AE", [u],
                       footprint="smartwatch:Johanson_2450AT18A0100001E_1206",
                       datasheet=DS + "Johanson_2450AT18A100.pdf",
                       description="Johanson 2.45 GHz chip antenna, pin 1 feed, pin 2 NC (mechanical).")


def tc2030():
    u = Unit("Tag-Connect TC2030 SWD",
             right=[("1", "VTREF", "power_in"), None, None, ("2", "SWDIO", BI), ("3", "nRESET", BI), ("4", "SWDCLK", BI),
                    ("6", "SWO", BI), None, None, ("5", "GND", "power_in")], width=12.7)
    return chip_symbol("smartwatch", "TC2030_SWD", "J", [u],
                       footprint="Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical",
                       datasheet="Tag-Connect TC2030-CTX-NL cable (pin order to be confirmed)",
                       description="Tag-Connect TC2030 no-legs SWD pads. Pin order: 1 VTREF, 2 SWDIO, 3 nRESET, 4 SWDCLK, 5 GND, 6 SWO.")

def npm1300():
    N = None
    u = Unit("nPM1300 PMIC",
             left=[("21", "VBUS", PI), N, N, N, ("23", "CC1", "input"), ("24", "CC2", "input"), N,
                   ("19", "VBAT", BI), N, N, N, ("18", "NTC", "input"), N, N,
                   ("17", "VSET1", "input"), ("16", "VSET2", "input"), N, N, N, N, ("15", "SHPHLD", "input"), N, N,
                   ("14", "SCL", "input"), ("13", "SDA", BI), N, N, N, ("12", "VDDIO", PI)],
             right=[("22", "VBUSOUT", PO), N, N, N, ("20", "VSYS", PO), ("4", "PVDD", PI), N, N, N, N,
                    ("3", "SW1", PA), N, ("1", "VOUT1", PO), N, N, N, N, ("2", "PVSS1", PA), N, N, N, N, N,
                    ("32", "VOUT2", PA), ("5", "SW2", PA), ("6", "PVSS2", PA), N,
                    ("28", "LSIN1/VINLDO1", PA), ("30", "LSIN2/VINLDO2", PA), ("29", "LSOUT1/VOUTLDO1", PA),
                    ("31", "LSOUT2/VOUTLDO2", PA), N,
                    ("7", "GPIO0", BI), ("8", "GPIO1", BI), ("9", "GPIO2", BI), ("10", "GPIO3", BI), ("11", "GPIO4", BI), N,
                    ("25", "LED0", PA), ("26", "LED1", PA), ("27", "LED2", PA)],
             bottom=[("33", "AVSS", PI)], width=17.78)
    return chip_symbol("smartwatch", "nPM1300-QEAA", "U", [u], footprint="Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm",
                       datasheet=DS + "nPM1300_PS_v1.3.txt",
                       description="Nordic nPM1300 PMIC with charger, two bucks, two load switches/LDOs, QFN32 5x5 mm (QEAA). Pin table: product specification v1.3, QFN32 pin assignments.")


def mx25r3235f():
    u = Unit("MX25R3235F 32 Mbit flash",
             top=[("8", "VCC", PI)], bottom=[("4", "GND", PI)],
             left=[("1", "CS#", "input"), None, None, ("6", "SCLK", "input"), None, None, ("5", "SI/SIO0", BI), None, None,
                   ("2", "SO/SIO1", TS)],
             right=[("3", "WP#/SIO2", BI), ("7", "RESET#/SIO3", BI)], width=15.24)
    return chip_symbol("smartwatch", "MX25R3235F", "U", [u], footprint="smartwatch:MX25R3235F_USON-8_4x3mm_P0.8mm",
                       datasheet=DS + "MX25R3235F_rev1.6.pdf",
                       description="Macronix MX25R3235F 32 Mbit serial NOR flash, 8-land USON 4x3 mm (ZB), RESET# option (L0). Rev 1.6 section 3.")


def battery_conn():
    u = Unit("Battery connector",
             right=[("1", "BAT+", PA), None, None, None, ("2", "NTC", PA), None, ("3", "GND", PA)], width=10.16)
    return chip_symbol("smartwatch", "Battery_Conn_3", "J", [u],
                       footprint="Connector_JST:JST_SH_SM03B-SRSS-TB_1x03-1MP_P1.00mm_Horizontal",
                       datasheet="~", description="Three-wire battery connector: BAT+, NTC thermistor, GND. Pin order CHECK against the chosen cell.")


ALL = [nrf54l15, max86141, bmi270, max30208, tps61240, ocvpb21, sfh7016, vemd8080, antenna, tc2030, npm1300, mx25r3235f, battery_conn]
