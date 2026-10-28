"""Build the Smart Watch KiCad project: python build.py   (writes ../smartwatch.* and ../libs/*)

Every connection below follows hardware/REQUIREMENTS_FROM_DATASHEETS.md. Net prefixes:
  '=NAME'  power symbol, 'gl:NAME' global label, 'hl:NAME' hierarchical label (sheet interface), else local label.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import parts
from kigen import Lib, Registry, Sheet, uid, write_symbol_lib, parse, find, PROJECT

OUT = Path(__file__).resolve().parent.parent
FP = {
    "C": {"0201": "Capacitor_SMD:C_0201_0603Metric", "0402": "Capacitor_SMD:C_0402_1005Metric",
          "0603": "Capacitor_SMD:C_0603_1608Metric"},
    "R": {"0201": "Resistor_SMD:R_0201_0603Metric", "0402": "Resistor_SMD:R_0402_1005Metric"},
    "L": {"0201": "Inductor_SMD:L_0201_0603Metric", "0402": "Inductor_SMD:L_0402_1005Metric",
          "0603": "Inductor_SMD:L_0603_1608Metric", "0805": "Inductor_SMD:L_0805_2012Metric"},
}
XTAL4 = "Crystal:Crystal_SMD_2016-4Pin_2.0x1.6mm"
XTAL2 = "Crystal:Crystal_SMD_2012-2Pin_2.0x1.2mm"
TP_FP = "TestPoint:TestPoint_Pad_D1.0mm"

lib, reg = Lib(), Registry()
for n in ("C_Small", "R_Small", "L_Small", "FerriteBead_Small", "Crystal_Small", "Crystal_GND24", "NetTie_2"):
    lib.add_stock("Device", n)
lib.add_stock("Connector", "TestPoint")
lib.add_stock("Connector_Generic", "Conn_01x01")
lib.add_stock("power", "PWR_FLAG")
sym_blocks = [fn() for fn in parts.ALL]
for b in sym_blocks:
    lib.add_custom("smartwatch", b)

ROOT = uid()
BLOCK = {n: uid() for n in ("power_stub", "input_protection", "led_supply", "mcu", "rf", "optical", "sensors", "test")}
sheets = {}


def new(name, title):
    s = Sheet(lib, reg, ROOT, BLOCK[name], title)
    sheets[name] = s
    return s


def passive(sh, kind, x, y, value, pkg, a, b, ref=None, spec="", src="", dnp=False, rot=0, mpn=""):
    sym = {"C": "Device:C_Small", "R": "Device:R_Small", "L": "Device:L_Small", "FB": "Device:FerriteBead_Small"}[kind]
    fp = FP["L" if kind == "FB" else kind][pkg]
    props = {"Spec": spec, "Source": src}
    if mpn:
        props["MPN"] = mpn
    return sh.part(sym, x, y, rot, ref=ref, value=value, footprint=fp, nets={"1": a, "2": b}, props=props,
                   prefix={"C": "C", "R": "R", "L": "L", "FB": "FB"}[kind], dnp=dnp)


def header(sh, title, lines):
    sh.text(title, 15, 18, 2.54, True)
    for i, t in enumerate(lines):
        sh.text(t, 15, 25 + 4.5 * i, 1.27)


NRF = "nRF54L15 DS v1.0 Table 87 / Fig 180"

# =============================================================================== mcu
s = new("mcu", "nRF54L15 core")
header(s, "Processor: nRF54L15 (QFN48), supply, clocks, debug",
       ["Circuit follows Nordic circuit configuration 1 (DC/DC from the 1.8 V rail, no NFC), datasheet v1.0 section 10.3.",
        "GPIO plan: SPI on P2 (SPIM00, SCK on clock pin P2.01), I2C on P0 (TWIM30, SCL on clock pin P0.04), sensor interrupts on P0.",
        "P1.04-P1.07, P1.09-P1.14 left unused (errata 100). NFC pins P1.02/P1.03 unused."])
U1 = dict(libid="smartwatch:nRF54L15-QFAA", footprint="Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm", ref="U1",
          value="nRF54L15-QFAA", props={"Datasheet": "hardware/datasheets/nRF54L15_datasheet_v1.0.pdf"})
s.part(x=175, y=125, unit=1, nets={
    "47": "gl:+1V8", "48": "gl:+1V8", "10": "gl:+1V8", "22": "gl:+1V8", "36": "gl:+1V8",
    "46": "DCC", "45": "DECD", "43": "DECA", "33": "DECA",
    "44": "gl:GND", "49": "gl:GND", "32": "hl:VSS_PA",
    "34": "XC1", "35": "XC2", "1": "XL1", "2": "XL2", "31": "hl:RF_ANT",
    "25": "hl:SWDIO", "26": "hl:SWDCLK", "30": "NRESET_MCU"}, **U1)
s.part(x=335, y=70, unit=2, nets={
    "23": "hl:PPG_INT", "24": "hl:IMU_INT1", "27": "hl:IMU_INT2", "28": "hl:I2C_SDA", "29": "hl:I2C_SCL",
    "9": "hl:PMIC_IRQ"}, nc=("3", "4", "5", "6", "7", "8", "37", "38", "39", "40", "41", "42"), again=True, **{**U1, "ref": "U1"})
s.part(x=335, y=185, unit=3, nets={
    "11": "hl:CS_FLASH", "12": "hl:SPI_SCK", "13": "hl:SPI_MOSI", "14": "hl:TEMP_INT", "15": "hl:SPI_MISO",
    "16": "hl:CS_PPG", "17": "hl:CHG_FLAG", "18": "hl:SWO", "19": "hl:LED_BOOST_EN", "20": "hl:PPG_GPIO1",
    "21": "hl:PPG_GPIO2"}, again=True, **{**U1, "ref": "U1"})
# supply decoupling (Table 87)
s.text("VDD decoupling", 15, 52, 1.27, True)
passive(s, "C", 25, 66, "10uF", "0402", "=+1V8", "=GND", "C3", "X6S 20% 6.3V", NRF)
passive(s, "C", 35, 66, "100nF", "0201", "=+1V8", "=GND", "C10", "X7R 10%", NRF)
passive(s, "C", 45, 66, "100nF", "0201", "=+1V8", "=GND", "C4", "X7R 10%", NRF)
passive(s, "C", 55, 66, "100nF", "0201", "=+1V8", "=GND", "C7", "X7R 10%", NRF)
passive(s, "C", 65, 66, "100nF", "0201", "=+1V8", "=GND", "C8", "X7R 10%", NRF)
s.text("Internal regulators: DC/DC (DCC to DECD), DECD, DECA/DECRF", 15, 82, 1.27, True)
passive(s, "L", 30, 96, "4.7uH", "0603", "DCC", "DECD", "L1", "120 mA 20% 650 mOhm", NRF, rot=90)
passive(s, "C", 45, 96, "2.2uF", "0201", "DECD", "=GND", "C1", "X6T 20% 2.5V", NRF)
passive(s, "FB", 62, 96, "120R@100MHz", "0201", "DECD", "DECA", "FB1", "200 mA 500 mOhm max", NRF, rot=90)
passive(s, "C", 75, 96, "2.2uF", "0201", "DECA", "=GND", "C2", "X6T 20% 2.5V", NRF)
passive(s, "C", 85, 96, "10nF", "0201", "DECA", "=GND", "C12", "X7R 6.3V", NRF)
passive(s, "C", 95, 96, "2.2nF", "0201", "DECA", "=GND", "C5", "X7R 10% 10V", NRF)
s.text("Clocks and reset", 15, 120, 1.27, True)
s.part("Device:Crystal_GND24", 35, 138, 0, ref="X2", value="32MHz", footprint=XTAL4,
       nets={"1": "XC1", "3": "XC2", "2": "=GND"}, props={"Spec": "2.0x1.6 mm, CL 8 pF, total tol 40 ppm", "Source": NRF}, prefix="X")
s.part("Device:Crystal_Small", 35, 160, 0, ref="X1", value="32.768kHz", footprint=XTAL2,
       nets={"1": "XL1", "2": "XL2"}, props={"Spec": "2.0x1.2 mm, CL 9 pF, total tol 20 ppm", "Source": NRF}, prefix="X")
passive(s, "C", 62, 150, "3.9pF", "0201", "NRESET_MCU", "=GND", "C13", "C0G 0.25pF 50V", NRF)
passive(s, "R", 75, 150, "1k", "0201", "NRESET_MCU", "hl:NRESET", "R1", "1% 0.05W", NRF)
s.text("Single-point ties required by Nordic: VSS_PA (pin 32) to ground only at the exposed pad", 15, 180, 1.27, True)
s.part("Device:NetTie_2", 35, 192, 0, ref="NT1", value="NetTie", footprint="NetTie:NetTie-2_SMD_Pad0.5mm",
       nets={"1": "VSS_PA", "2": "=GND"}, props={"Source": NRF + " note on C6"}, prefix="NT")
for i, t in enumerate(("hl:RF_ANT",)):
    pass

# =============================================================================== rf
s = new("rf", "RF match and antenna")
header(s, "RF: Nordic filter-match network, then the antenna tee",
       ["Nordic network (Table 87): C6 returns to VSS_PA in the top layer ONLY; C9 returns to the BOTTOM ground layer ONLY.",
        "Antenna: Johanson 2450AT18A0100001E, corner mount, tuned on the worn band. Tee slots: series, shunt, series.",
        "Place the Nordic network as close to the ANT pin as possible (datasheet note)."])
RFN = "nRF54L15 DS v1.0 Fig 180 / Table 87"
passive(s, "L", 50, 80, "2.7nH", "0201", "hl:RF_ANT", "RF_A", "L2", "0.1 nH 600 mA", RFN, rot=90, mpn="LQP03HQ2N7B02")
passive(s, "C", 80, 95, "1.5pF", "0201", "RF_A", "hl:VSS_PA", "C6", "NP0 0.05 pF 25V high Q", RFN, mpn="GJM0335C1E1R5WB01")
passive(s, "L", 110, 80, "3.5nH", "0201", "RF_A", "RF_B", "L3", "0.1 nH 500 mA", RFN, rot=90, mpn="LQP03HQ3N5B02")
passive(s, "C", 140, 95, "2.0pF", "0201", "RF_B", "GND_BOT", "C9", "NP0 0.05 pF 25V", RFN, mpn="GJM0335C1E2R0WB01")
passive(s, "L", 170, 80, "3.5nH", "0201", "RF_B", "RF_C", "L4", "0.1 nH 500 mA", RFN, rot=90, mpn="LQP03HQ3N5B02")
passive(s, "C", 200, 95, "0.3pF", "0201", "RF_C", "=GND", "C11", "C0G 0.1 pF 50V", RFN)
s.part("Device:NetTie_2", 140, 118, 0, ref="NT2", value="NetTie", footprint="NetTie:NetTie-2_SMD_Pad0.5mm",
       nets={"1": "GND_BOT", "2": "=GND"}, props={"Source": RFN + " note on C9"}, prefix="NT")
s.text("Antenna tee (Johanson datasheet: leave slots for a series-shunt-series network). Start 0R / empty / 0R.", 15, 135, 1.27, True)
passive(s, "R", 40, 160, "0R", "0402", "RF_C", "ANT_A", None, "series slot", "Johanson DS 36S0021A note 4", rot=90)
passive(s, "C", 70, 175, "TBD", "0402", "ANT_A", "=GND", None, "shunt slot, tune on worn band", "Johanson DS 36S0021A note 4", dnp=True)
passive(s, "R", 100, 160, "0R", "0402", "ANT_A", "ANT_FEED", None, "series slot", "Johanson DS 36S0021A note 4", rot=90)
s.part("smartwatch:Chip_Antenna_2450AT18A", 150, 160, 0, ref="AE1", value="2450AT18A0100001E",
       footprint="smartwatch:Johanson_2450AT18A0100001E_1206", nets={"1": "ANT_FEED"}, nc=("2",),
       props={"Source": "Johanson DS 36S0021A rev 4.0"}, prefix="AE")

# =============================================================================== optical
s = new("optical", "Optical sensing")
header(s, "Optical: MAX86141 + SFH 7016 + 2 x VEMD8080",
       ["Supply 1.8 V (1.7-2.0 V): VDD_ANA and VDD_DIG shorted, 22 uF + 0.1 uF. VREF 1 uF. VLED 10 uF (3.1-5.5 V). Datasheet Rev 5 p.12, p.49.",
        "GND_ANA, GND_DIG and PGND meet at one via. PD_GND is a separate net with ONE tie to ground (net tie NT3).",
        "LED channel order follows the MAXREFDES103 table: LED1 = green, LED2 = IR, LED3 = red."])
MX = "MAX86141 DS Rev 5"
s.part("smartwatch:MAX86141", 150, 130, 0, ref="U2", value="MAX86141ENP+", footprint="smartwatch:MAX86141_WLP-20_2.048x1.848mm_P0.4mm",
       nets={"A1": "gl:VLED", "D3": "gl:GND", "D2": "gl:+1V8", "C2": "gl:+1V8", "C4": "gl:GND", "C3": "gl:GND",
             "B5": "VREF", "D1": "LED1_DRV", "C1": "LED2_DRV", "B1": "LED3_DRV", "D5": "PD1_IN", "D4": "PD2_IN",
             "C5": "PD_GND", "A5": "hl:CS_PPG", "A2": "hl:SPI_SCK", "A4": "hl:SPI_MOSI", "A3": "hl:SPI_MISO",
             "B2": "hl:PPG_INT", "B3": "hl:PPG_GPIO1", "B4": "hl:PPG_GPIO2"},
       props={"Datasheet": "hardware/datasheets/MAX86141_rev5.pdf"})
s.text("Supply decoupling (datasheet p.49)", 15, 52, 1.27, True)
passive(s, "C", 25, 66, "22uF", "0402", "=+1V8", "=GND", None, "6.3V or higher, effective ~10 uF", MX + " p.49")
passive(s, "C", 35, 66, "100nF", "0201", "=+1V8", "=GND", None, "at the VDD_ANA ball", MX + " p.12")
passive(s, "C", 45, 66, "1uF", "0201", "VREF", "=GND", None, "6.3V (VREF is 1.21 V)", MX + " p.12")
passive(s, "C", 55, 66, "10uF", "0603", "gl:VLED", "=GND", None, "10V X5R (VLED up to 5.5 V)", MX + " p.12")
s.text("Open-drain interrupt lines", 15, 86, 1.27, True)
passive(s, "R", 25, 100, "100k", "0201", "=+1V8", "hl:PPG_INT", None, "pull-up", "MAXREFDES103 R12")
passive(s, "R", 40, 100, "100k", "0201", "=+1V8", "hl:PPG_GPIO1", None, "pull-up", "MAXREFDES103 R23")
s.text("Emitter and links (0 Ohm in series with each cathode for bring-up)", 15, 120, 1.27, True)
s.part("smartwatch:SFH7016", 40, 150, 0, ref="D1", value="SFH 7016", footprint="smartwatch:SFH7016_1.85x1.65mm",
       nets={"2": "gl:VLED", "5": "gl:VLED", "3": "LED_G", "4": "LED_R", "1": "LED_IR"}, nc=("6",),
       props={"Datasheet": "hardware/datasheets/SFH7016.pdf"}, prefix="D")
passive(s, "R", 80, 150, "0R", "0201", "LED_G", "LED1_DRV", None, "link", "bring-up current measurement", rot=90)
passive(s, "R", 80, 162, "0R", "0201", "LED_IR", "LED2_DRV", None, "link", "bring-up current measurement", rot=90)
passive(s, "R", 80, 174, "0R", "0201", "LED_R", "LED3_DRV", None, "link", "bring-up current measurement", rot=90)
s.text("Photodiodes: anode (pin 5) to PD_GND, cathode pads (1-4, 6-8) to the channel input", 15, 195, 1.27, True)
cath = ("1", "2", "3", "4", "6", "7", "8")
for i, (name, x) in enumerate((("PD1", 45), ("PD2", 95))):
    nets = {"5": "PD_GND", **{c: f"{name}_IN" for c in cath}}
    s.part("smartwatch:VEMD8080", x, 225, 0, ref=name, value="VEMD8080", footprint="smartwatch:VEMD8080_4.8x2.5mm",
           nets=nets, props={"Datasheet": "hardware/datasheets/VEMD8080.pdf"}, prefix="PD")
s.part("Device:NetTie_2", 150, 215, 0, ref="NT3", value="NetTie", footprint="NetTie:NetTie-2_SMD_Pad0.5mm",
       nets={"1": "PD_GND", "2": "=GND"}, props={"Source": MX + " layout guidelines p.49: PD_GND to ground at one point"}, prefix="NT")

# =============================================================================== sensors
s = new("sensors", "Motion and temperature")
header(s, "Motion (BMI270) and skin temperature (MAX30208), I2C",
       ["BMI270: I2C address 0x68 (SDO to ground), CSB to VDDIO selects I2C, 100 nF on VDD and VDDIO, aux pins to VDDIO.",
        "MAX30208: address 0x50 (GPIO1 to ground; GPIO0 reads 0 at start-up through its internal 1 MOhm pull-down).",
        "One pair of 4.7 kOhm pull-ups for the whole I2C bus (rise time about 0.2 us for 50 pF)."])
s.part("smartwatch:BMI270", 120, 110, 0, ref="U3", value="BMI270", footprint="Package_LGA:Bosch_LGA-14_3x2.5mm_P0.5mm",
       nets={"8": "gl:+1V8", "5": "gl:+1V8", "7": "gl:GND", "6": "gl:GND", "12": "gl:+1V8", "1": "gl:GND",
             "13": "hl:I2C_SCL", "14": "hl:I2C_SDA", "2": "gl:+1V8", "3": "gl:+1V8", "4": "hl:IMU_INT1",
             "9": "hl:IMU_INT2"}, nc=("10", "11"), props={"Datasheet": "hardware/datasheets/BMI270.pdf"})
s.part("smartwatch:MAX30208", 120, 200, 0, ref="U4", value="MAX30208", footprint="smartwatch:MAX30208_TLGA-10_2x2mm",
       nets={"1": "gl:+1V8", "2": "gl:+1V8", "3": "gl:+1V8", "4": "gl:GND", "5": "gl:GND", "6": "gl:GND",
             "8": "hl:I2C_SDA", "9": "hl:I2C_SCL", "7": "gl:GND", "10": "hl:TEMP_INT"},
       props={"Datasheet": "hardware/datasheets/MAX30208.pdf"})
s.text("Decoupling", 15, 52, 1.27, True)
passive(s, "C", 25, 66, "100nF", "0201", "=+1V8", "=GND", None, "BMI270 VDD, pin 8", "BMI270 DS section 7.2")
passive(s, "C", 35, 66, "100nF", "0201", "=+1V8", "=GND", None, "BMI270 VDDIO, pin 5", "BMI270 DS section 7.2")
passive(s, "C", 45, 66, "100nF", "0201", "=+1V8", "=GND", None, "MAX30208 VDD (pins 1-3)", "MAX30208 DS p.5 pin table")
s.text("I2C pull-ups", 15, 86, 1.27, True)
passive(s, "R", 25, 100, "4.7k", "0201", "=+1V8", "hl:I2C_SDA", None, "pull-up", "rise time estimate, 400 kHz")
passive(s, "R", 40, 100, "4.7k", "0201", "=+1V8", "hl:I2C_SCL", None, "pull-up", "rise time estimate, 400 kHz")

# =============================================================================== led_supply
s = new("led_supply", "LED supply")
header(s, "LED supply: 5.0 V boost (TPS61240) with a direct link to VSYS for comparison",
       ["Fit ONE of the two 0R links: boost output to VLED (default) or VSYS to VLED (power tree option A).",
        "TPS61240: L = 1.0 uH min, CIN 2.2 uF, COUT effective 2.7 uF min at 5 V (datasheet 10.2.2). EN high level 1.0 V, so 1.8 V logic is enough.",
        "EN has a 100 kOhm pull-down so the boost is off while the processor pins float (errata 103)."])
TP = "TPS61240 DS SLVS806D"
s.part("smartwatch:TPS61240", 130, 100, 0, ref="U5", value="TPS61240DRVR", footprint="Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm",
       nets={"6": "gl:VSYS", "4": "hl:LED_BOOST_EN", "5": "SW", "1": "gl:GND", "7": "gl:GND", "2": "VLED_BOOST", "3": "VLED_BOOST"},
       props={"Datasheet": "hardware/datasheets/TPS61240.pdf"})
passive(s, "L", 80, 60, "1.0uH", "0805", "gl:VSYS", "SW", None, "1.0 uH min, Isat > 0.9 A", TP + " Table 2/3", rot=90, mpn="LQM21PN1R0MC0")
passive(s, "C", 40, 120, "2.2uF", "0402", "gl:VSYS", "=GND", None, "X5R 6.3V min", TP + " Table 2")
passive(s, "C", 160, 130, "10uF", "0603", "VLED_BOOST", "=GND", None, "X5R 10V (effective >= 2.7 uF at 5 V)", TP + " 10.2.2.4")
passive(s, "R", 60, 140, "100k", "0201", "hl:LED_BOOST_EN", "=GND", None, "pull-down", "nRF54L15 errata 103")
passive(s, "R", 200, 100, "0R", "0402", "VLED_BOOST", "gl:VLED", None, "VLED from the boost (default, fitted)", "power tree option B", rot=90)
passive(s, "R", 200, 130, "0R", "0402", "gl:VSYS", "gl:VLED", None, "VLED straight from VSYS (DNP, power tree option A)", "power tree option A", rot=90, dnp=True)
s.part("power:PWR_FLAG", 235, 100, 0, ref="#FLG1", value="PWR_FLAG", footprint="", nets={"1": "gl:VLED"}, prefix="#FLG")

# =============================================================================== input_protection
s = new("input_protection", "Charging input")
header(s, "Charging input: two pogo pads, ST OCVPB21-13F6, to the charger",
       ["The bridge accepts either polarity. Input 4.25-5.55 V. OUT_5V needs >= 10 uF. FLAG is open drain with 100 kOhm pull-up.",
        "RLIM sets the current limit: ILIM = (318 - RLIM) / 0.447 mA. 180 Ohm gives about 310 mA.",
        "Operating temperature of this part: -30 to +65 degC. Data pins are not used (two-pad pogo)."])
OV = "OCVPB21-13F6 DS13107 Rev 3"
s.part("smartwatch:OCVPB21-13F6", 130, 100, 0, ref="U6", value="OCVPB21-13F6", footprint="smartwatch:OCVPB21-13F6_WLCSP-13_P0.4mm",
       nets={"D1": "POGO_A", "D3": "POGO_B", "E1": "RLIM", "E3": "hl:CHG_FLAG", "B2": "gl:VBUS_PROT",
             "A3": "gl:GND", "C3": "gl:GND", "E2": "gl:GND"}, nc=("C2", "A2", "B3", "A1", "B1"),
       props={"Datasheet": "hardware/datasheets/OCVPB21-13F6.pdf"})
for i, (nm, y) in enumerate((("POGO_A", 90), ("POGO_B", 110))):
    s.part("Connector_Generic:Conn_01x01", 60, y, 0, ref=f"J{i+1}", value="Pogo pad", footprint="smartwatch:Pogo_Pad_D2.6mm",
           nets={"1": nm}, props={"Source": "research/power-battery/POGO_CHARGING.md"}, prefix="J")
passive(s, "R", 100, 140, "180R", "0402", "RLIM", "=GND", None, "1% or better, 51-270 Ohm allowed", OV + " section 1.2")
passive(s, "C", 175, 120, "10uF", "0603", "gl:VBUS_PROT", "=GND", None, "10V low ESR, >= 10 uF", OV + " Table 2")
passive(s, "R", 175, 150, "100k", "0201", "=+1V8", "hl:CHG_FLAG", None, "FLAG pull-up", OV + " Table 2")

# =============================================================================== test
s = new("test", "Test and programming")
header(s, "Programming and test access",
       ["Tag-Connect TC2030-NL SWD pads: pin order 1 VTREF, 2 SWDIO, 3 nRESET, 4 SWDCLK, 5 GND, 6 SWO (to be confirmed against the cable drawing).",
        "Test points: rails and the two buses, for the production fixture (research/storage-nfc-dft/DFT_PROGRAMMING.md)."])
s.part("smartwatch:TC2030_SWD", 110, 100, 0, ref="J3", value="TC2030-NL", footprint="Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical",
       nets={"1": "gl:+1V8", "2": "hl:SWDIO", "3": "hl:NRESET", "4": "hl:SWDCLK", "5": "gl:GND", "6": "hl:SWO"})
tp = [("+1V8", "gl:+1V8"), ("VSYS", "gl:VSYS"), ("VLED", "gl:VLED"), ("GND", "gl:GND"), ("GND", "gl:GND"),
      ("I2C_SDA", "hl:I2C_SDA"), ("I2C_SCL", "hl:I2C_SCL"), ("SPI_SCK", "hl:SPI_SCK"), ("SPI_MOSI", "hl:SPI_MOSI"),
      ("SPI_MISO", "hl:SPI_MISO"), ("PPG_INT", "hl:PPG_INT")]
for i, (nm, net) in enumerate(tp):
    s.part("Connector:TestPoint", 40 + 15 * (i % 6), 160 + 30 * (i // 6), 0, ref=None, value=f"TP {nm}", footprint=TP_FP,
           nets={"1": net}, prefix="TP")

# =============================================================================== power_stub (flags until the nPM1300 sheet)
s = new("power_stub", "Power rails (stand-in)")
header(s, "Stand-in for the nPM1300 power sheet (datasheet not yet saved)",
       ["Marks the rails that the nPM1300 will drive. Remove this sheet when the power sheet is added."])
for i, (nm, net) in enumerate((("+1V8", "gl:+1V8"), ("GND", "gl:GND"), ("VSYS", "gl:VSYS"))):
    s.part("power:PWR_FLAG", 50 + 30 * i, 80, 0, ref=None, value="PWR_FLAG", footprint="", nets={"1": net}, prefix="#FLG")

# =============================================================================== root
root = Sheet(lib, reg, ROOT, None, "HealthOS Band main board", paper="A3")
root.text("HealthOS Band Rev 1.1 main board: hierarchical schematic", 15, 18, 2.54, True)
root.text("Pending sheets: power (nPM1300, battery), memory (MX25R3235F). Their datasheets are not saved yet.", 15, 26, 1.27)
iface = {}
for name, s_ in sheets.items():
    iface[name] = list(dict.fromkeys(s_.ports))
layout = {"input_protection": (30, 50), "power_stub": (30, 130), "led_supply": (30, 190), "mcu": (160, 50),
          "rf": (290, 50), "optical": (290, 130), "sensors": (290, 215), "test": (160, 215)}
page = 2
for name, (x, y) in layout.items():
    pins = iface[name]
    half = (len(pins) + 1) // 2
    h = max(12.7, 2.54 * (half + 1))
    root.sheet_block(name, f"{name}.kicad_sch", x, y, 60, h, pins[:half], pins[half:], page, BLOCK[name])
    page += 1

# =============================================================================== write
(OUT / "libs").mkdir(exist_ok=True)
write_symbol_lib(OUT / "libs" / "smartwatch.kicad_sym", sym_blocks)
(OUT / "sym-lib-table").write_text(
    '(sym_lib_table\n\t(version 7)\n\t(lib (name "smartwatch")(type "KiCad")(uri "${KIPRJMOD}/libs/smartwatch.kicad_sym")(options "")(descr "Smart Watch chip symbols"))\n)\n',
    encoding="utf-8")
(OUT / "fp-lib-table").write_text(
    '(fp_lib_table\n\t(version 7)\n\t(lib (name "smartwatch")(type "KiCad")(uri "${KIPRJMOD}/libs/smartwatch.pretty")(options "")(descr "Smart Watch footprints"))\n)\n',
    encoding="utf-8")
(OUT / f"{PROJECT}.kicad_pro").write_text(json.dumps({"meta": {"filename": f"{PROJECT}.kicad_pro", "version": 3}}, indent=2), encoding="utf-8")
(OUT / f"{PROJECT}.kicad_sch").write_text(root.render(), encoding="utf-8")
for name, s_ in sheets.items():
    (OUT / f"{name}.kicad_sch").write_text(s_.render(), encoding="utf-8")
print("wrote", len(sheets) + 1, "sheets;", len(reg.used), "references")
