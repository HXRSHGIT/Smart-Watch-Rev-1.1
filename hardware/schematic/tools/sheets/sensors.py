"""Motion (BMI270) and skin temperature (MAX30208) on the shared I2C bus. A4, drawn left to right."""
from .common import U, P, part, note

BMI_SRC = "BMI270 DS Rev 08 section 7"
MAX_SRC = "MAX30208 DS Rev 1 p.5"


def draw(d):
    d.head("MOTION AND SKIN TEMPERATURE  -  BMI270 + MAX30208 on the I2C bus", 12 * U, 16 * U)
    d.sub("Both parts run from the 1.8 V rail and share SDA / SCL. Interrupts go to the processor.", 12 * U, 19.5 * U)

    # ------------------------------------------------------------------ BMI270
    d.frame(*P(12, 23), *P(116, 91), heading="BMI270  -  MOTION")
    b = d.put("smartwatch:BMI270", *P(76, 66), ref="U3", value="BMI270",
              footprint="Package_LGA:Bosch_LGA-14_3x2.5mm_P0.5mm", props={"Datasheet": "hardware/datasheets/BMI270.pdf"})
    # supply: VDD and VDDIO tied, one stem up to the rail, two decoupling caps hang from the rail
    vdd, vio = b.p(8), b.p(5)
    d.w(vdd, vio)
    rail_y = 46 * U
    d.w(vio, (vio[0], 43 * U))
    d.rail("+1V8", vio[0], 43 * U)
    d.w((vio[0], rail_y), (54 * U, rail_y))
    c19 = part(d, "C", "C19", "100nF", "0201", 58, 48, "X7R 10%", BMI_SRC + ".2")
    c20 = part(d, "C", "C20", "100nF", "0201", 54, 48, "X7R 10%", BMI_SRC + ".2", tside="L")
    d.w(c19.p(2), c20.p(2))                 # one ground wire and one ground symbol for the pair
    d.gnd(*c19.p(2))
    # strap pins that go to VDDIO: CSB (selects I2C), ASDx, ASCx (datasheet: VDDIO or open, never ground)
    bar_x = 66 * U
    for pin in (12, 2, 3):
        d.w(b.p(pin), (bar_x, b.p(pin)[1]))
    d.w((bar_x, b.p(3)[1]), (bar_x, rail_y))
    # SDO to ground: I2C address 0x68
    d.w(b.p(1), (bar_x, b.p(1)[1]), (bar_x, b.p(1)[1] + 2 * U))
    d.gnd(bar_x, b.p(1)[1] + 2 * U)
    # ground pins
    d.w(b.p(7), b.p(6))
    d.w(b.p(6), (b.p(6)[0], b.p(6)[1] + 3 * U))
    d.gnd(b.p(6)[0], b.p(6)[1] + 3 * U)
    # unused pins
    d.nc(*b.p(10))
    d.nc(*b.p(11))
    # interrupt ports
    for pin, name in ((4, "IMU_INT1"), (9, "IMU_INT2")):
        x, y = b.p(pin)
        d.w((x, y), (104 * U, y))
        d.port(name, 104 * U, y, "R", "output")

    # ------------------------------------------------------------------ I2C bus in, pull-ups
    sda_y, scl_y = b.p(14)[1], b.p(13)[1]
    # SCL line comes in on the upper row and steps down to the pin; SDA comes in low and steps up.
    r_scl = part(d, "R", "R9", "4.7k", "0201", 38, 58, "pull-up", "I2C 400 kHz, 50 pF -> rise time about 0.2 us")
    r_sda = part(d, "R", "R10", "4.7k", "0201", 38, 74, "pull-up", "I2C 400 kHz, 50 pF -> rise time about 0.2 us")
    scl_line, sda_line = r_scl.p(2)[1], r_sda.p(2)[1]
    d.port("I2C_SCL", 26 * U, scl_line, "L")
    d.w((26 * U, scl_line), (50 * U, scl_line), (50 * U, scl_y), b.p(13))
    d.port("I2C_SDA", 26 * U, sda_line, "L")
    d.w((26 * U, sda_line), (48 * U, sda_line), (48 * U, sda_y), b.p(14))
    for k, (line, name) in enumerate(((sda_line, "I2C_SDA"), (scl_line, "I2C_SCL"))):          # bus test points
        d.put("Connector:TestPoint", 31 * U, line, 180, ref=f"TP{6 + k}", value=f"TP {name}",
              footprint="TestPoint:TestPoint_Pad_D1.0mm", prefix="TP", tside="R")
    d.rail("+1V8", *r_scl.p(1))
    d.rail("+1V8", *r_sda.p(1))
    d.caption("I2C PULL-UPS", 20 * U, 84 * U)

    # ------------------------------------------------------------------ MAX30208
    d.frame(*P(12, 95), *P(116, 150), heading="MAX30208  -  SKIN TEMPERATURE")
    m = d.put("smartwatch:MAX30208", *P(76, 124), ref="U4", value="MAX30208",
              footprint="smartwatch:MAX30208_TLGA-10_2x2mm", props={"Datasheet": "hardware/datasheets/MAX30208.pdf"})
    # VDD x3 tied, stem up, one 100 nF
    v1, v2, v3 = m.p(1), m.p(2), m.p(3)
    d.w(v1, v3)
    d.w(v2, (v2[0], 106 * U))
    d.rail("+1V8", v2[0], 106 * U)
    c21 = part(d, "C", "C21", "100nF", "0201", 86, 108, "X7R 10%", MAX_SRC + " pin table")
    d.w((v2[0], c21.p(1)[1]), c21.p(1))
    d.dot(v2[0], c21.p(1)[1])
    d.gnd(*c21.p(2))
    # ground x3 tied
    g1, g2, g3 = m.p(4), m.p(5), m.p(6)
    d.w(g1, g3)
    d.w(g2, (g2[0], g2[1] + 3 * U))
    d.gnd(g2[0], g2[1] + 3 * U)
    # GPIO1 to ground fixes the address bits at 0 (address 0x50)
    d.w(m.p(7), (66 * U, m.p(7)[1]), (66 * U, m.p(7)[1] + 2 * U))
    d.gnd(66 * U, m.p(7)[1] + 2 * U)
    # I2C: the bus is the same net as above, shown with labels at the second device
    for pin, name in ((8, "I2C_SDA"), (9, "I2C_SCL")):
        x, y = m.p(pin)
        d.w((x, y), (62 * U, y))
        d.label_net(name, 62 * U, y, 180)
    # alarm output
    x, y = m.p(10)
    d.w((x, y), (104 * U, y))
    d.port("TEMP_INT", 104 * U, y, "R", "output")

    # ------------------------------------------------------------------ notes
    nx = 126 * U
    h = note(d, "BMI270: I2C address 0x68 because SDO is tied to ground. CSB high selects I2C. ASDx and ASCx (the "
                "secondary interface) are tied to VDDIO as the datasheet requires, never to ground. OCSB and OSDO "
                "are not used.", nx, 28 * U, 78)
    note(d, "C19 and C20 are decoupling capacitors for BMI270 VDD and VDDIO (100 nF each). Keep them close to the pins.",
         nx, 28 * U + h + 3, 78)
    h2 = note(d, "MAX30208: address 0x50. GPIO1 is tied to ground, and GPIO0 reads low at start-up through its internal "
                 "1 MOhm pull-down, so the address stays 0x50. GPIO0 is the temperature alarm output "
                 "(TEMP_INT), open drain and active low in INTB mode: set that mode first, then enable the processor's "
                 "internal pull-up on P2.03. Do NOT add an external pull-up, it would change the address. All three VDD "
                 "pins and all three GND pins are connected.", nx, 98 * U, 78)
    note(d, "C21 decouples MAX30208 VDD (100 nF). Keep it close to the pins. Read PCN 2204 before ordering.",
         nx, 98 * U + h2 + 3, 78)
    note(d, "One pair of 4.7 kOhm pull-ups serves the whole bus. At 400 kHz and about 50 pF the rise time is about 0.2 us. "
            "The nPM1300 joins this bus on the power sheet.", nx, 62 * U, 78)
