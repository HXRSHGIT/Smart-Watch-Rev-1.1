"""Processor nRF54L15: supply, regulators, clocks, reset, debug, and the GPIO ports. A3, left to right."""
from .common import U, P, part, note

NRF = "nRF54L15 DS v1.0 Table 87 / Fig 180"

UNIT2_PORTS = {"23": "PPG_INT", "24": "IMU_INT1", "27": "IMU_INT2", "28": "I2C_SDA", "29": "I2C_SCL", "9": "PMIC_IRQ"}
UNIT2_NC = ("3", "4", "5", "6", "7", "8", "37", "38", "39", "40", "41", "42")
UNIT3_PORTS = {"11": "CS_FLASH", "12": "SPI_SCK", "13": "SPI_MOSI", "14": "TEMP_INT", "15": "SPI_MISO", "16": "CS_PPG",
               "17": "CHG_FLAG", "18": "SWO", "19": "LED_BOOST_EN", "20": "PPG_GPIO1", "21": "PPG_GPIO2"}


def draw(d):
    d.head("PROCESSOR  -  nRF54L15 (QFN48): supply, regulators, clocks, reset, debug, GPIO", 12 * U, 16 * U)
    d.sub("Nordic circuit configuration 1 (DC/DC from the 1.8 V rail, no NFC), datasheet v1.0 section 10.3 and Table 87. "
          "Peripherals sit on the right, the supply network on the left.", 12 * U, 19.5 * U)
    d.frame(*P(12, 23), *P(176, 140), heading="nRF54L15  -  CORE")
    d.frame(*P(180, 23), *P(262, 140), heading="GPIO PORTS")

    u1 = d.put("smartwatch:nRF54L15-QFAA", *P(112, 98), unit=1, ref="U1", value="nRF54L15-QFAA",
               footprint="Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm",
               props={"Datasheet": "hardware/datasheets/nRF54L15_datasheet_v1.0.pdf"})
    LX, y0 = u1.p("46")
    RX = u1.p("35")[0]
    ys = lambda s: y0 + 2 * U * s

    # ------------------------------------------------------------------ supply: five VDD pins, one stem, decoupling bar
    vd = [u1.p(n) for n in ("47", "48", "10", "22", "36")]
    d.w(vd[0], vd[-1])
    sx = vd[2][0]
    rail_y = vd[0][1] - 10 * U
    d.rail("+1V8", sx, rail_y - 3 * U)
    d.w((sx, rail_y - 3 * U), (sx, vd[2][1]))
    caps = [("C3", "10uF", "0402", "X6S 20% 6.3V"), ("C10", "100nF", "0201", "X7R 10%"), ("C4", "100nF", "0201", "X7R 10%"),
            ("C7", "100nF", "0201", "X7R 10%"), ("C8", "100nF", "0201", "X7R 10%")]
    xs = []
    for k, (ref, val, pkg, spec) in enumerate(caps):
        cx = sx / U - 9 - 10 * k
        c = part(d, "C", ref, val, pkg, cx, rail_y / U + 2, spec, NRF)
        d.w((cx * U, rail_y), c.p(1))
        xs.append(c)
    d.w((sx, rail_y), (xs[-1].p(1)[0], rail_y))
    d.w(xs[0].p(2), xs[-1].p(2))
    d.gnd(*xs[-1].p(2))
    d.caption("VDD DECOUPLING", xs[-1].p(1)[0], rail_y - 5 * U, size=1.27)

    # ------------------------------------------------------------------ regulators (left)
    nx = LX - 20 * U
    l1 = part(d, "L", "L1", "4.7uH", "0603", LX / U - 8, y0 / U, "120 mA 20% 650 mOhm", NRF, rot=90)
    d.w(l1.p(2), (LX, y0))
    d.w(l1.p(1), (nx, y0), (nx, ys(2)), (LX, ys(2)))
    c1 = part(d, "C", "C1", "2.2uF", "0201", LX / U - 8, ys(2) / U + 2, "X6T 20% 2.5V", NRF, tside="L")
    d.w((LX - 8 * U, ys(2)), c1.p(1))
    d.gnd(*c1.p(2))
    fb = part(d, "FB", "FB1", "120R@100MHz", "0201", nx / U, ys(2) / U + 4, "200 mA 500 mOhm max", NRF, tside="L")
    d.w((nx, ys(2)), fb.p(1))
    d.w(fb.p(2), (nx, ys(6)), (LX, ys(6)))
    d.w((LX, ys(6)), (LX, ys(7)))
    d.w((nx, ys(6)), (nx - 27 * U, ys(6)))
    dc = []
    for k, (ref, val, spec) in enumerate((("C2", "2.2uF", "X6T 20% 2.5V"), ("C12", "10nF", "X7R 6.3V"), ("C5", "2.2nF", "X7R 10% 10V"))):
        cxx = nx / U - 9 - 9 * k
        c = part(d, "C", ref, val, "0201", cxx, ys(6) / U + 2, spec, NRF)
        d.w((cxx * U, ys(6)), c.p(1))
        dc.append(c)
    d.w(dc[0].p(2), dc[-1].p(2))
    d.gnd(*dc[-1].p(2))
    d.caption("DECD / DECA", nx - 27 * U, ys(6) - 3 * U, size=1.27)
    d.caption("DC/DC", nx - 2 * U, y0 - 4 * U, size=1.27)

    # ------------------------------------------------------------------ debug and reset (left, bottom)
    px = LX - 62 * U
    for pin, name in (("25", "SWDIO"), ("26", "SWDCLK")):
        x, y = u1.p(pin)
        d.w((x, y), (px, y))
        d.port(name, px, y, "L", "bidirectional")
    rx_, ry_ = u1.p("30")
    c13 = part(d, "C", "C13", "3.9pF", "0201", LX / U - 8, ry_ / U + 2, "C0G 0.25pF 50V", NRF, tside="L")
    d.gnd(*c13.p(2))
    r1 = part(d, "R", "R1", "1k", "0201", LX / U - 24, ry_ / U, "1% 0.05W", NRF, rot=90)
    d.w((rx_, ry_), r1.p(2))
    d.w((LX - 8 * U, ry_), c13.p(1))
    d.w(r1.p(1), (px, ry_))
    d.port("NRESET", px, ry_, "L", "bidirectional")

    # ------------------------------------------------------------------ ground pins and VSS_PA
    g1, g2 = u1.p("44"), u1.p("49")
    d.w(g1, g2)
    d.w(g2, (g2[0], g2[1] + 3 * U))
    d.gnd(g2[0], g2[1] + 3 * U)
    d.w((g2[0], g2[1] + 2 * U), (g2[0] + 6 * U, g2[1] + 2 * U))      # PWR_FLAG for ground, same reason
    d.put("power:PWR_FLAG", g2[0] + 6 * U, g2[1] + 2 * U, 0, ref="#FLG4", value="PWR_FLAG", prefix="#FLG")
    pa = u1.p("32")
    jy = pa[1] + 6 * U
    d.w(pa, (pa[0], jy))
    d.w((pa[0], jy), (pa[0] - 4 * U, jy))
    d.port("VSS_PA", pa[0] - 4 * U, jy, "L", "bidirectional")
    nt = d.put("Device:NetTie_2", pa[0], jy + 4 * U, 90, ref="NT1", value="NetTie", footprint="NetTie:NetTie-2_SMD_Pad0.5mm",
               props={"Source": NRF + " note on C6"}, prefix="NT")
    top, bot = (nt.p(1), nt.p(2)) if nt.p(1)[1] < nt.p(2)[1] else (nt.p(2), nt.p(1))
    d.w((pa[0], jy), top)
    d.gnd(*bot)
    d.caption("VSS_PA TO GROUND ONLY AT THE EXPOSED PAD", pa[0] - 40 * U, jy + 12 * U, size=1.27)

    # ------------------------------------------------------------------ clocks (right)
    x2 = d.put("Device:Crystal_GND24", RX + 14 * U, ys(0) + 3 * U, 90, ref="X2", value="32MHz",
               footprint="Crystal:Crystal_SMD_2016-4Pin_2.0x1.6mm", props={"Spec": "2.0x1.6 mm, CL 8 pF, total tol 40 ppm", "Source": NRF},
               prefix="X", tside="L")
    d.w(u1.p("35"), (x2.p(3)[0], ys(0)))
    d.w(u1.p("34"), (x2.p(1)[0], ys(3)))
    d.gnd(*x2.p(2))
    x1 = d.put("Device:Crystal_Small", RX + 14 * U, ys(6), 270, ref="X1", value="32.768kHz",
               footprint="Crystal:Crystal_SMD_2012-2Pin_2.0x1.2mm", props={"Spec": "2.0x1.2 mm, CL 9 pF, total tol 20 ppm", "Source": NRF},
               prefix="X")
    d.w(u1.p("1"), (x1.p(1)[0], ys(5)))
    d.w(u1.p("2"), (x1.p(2)[0], ys(7)))
    ax, ay = u1.p("31")
    d.w((ax, ay), (RX + 40 * U, ay))
    d.port("RF_ANT", RX + 40 * U, ay, "R", "bidirectional")

    # ------------------------------------------------------------------ GPIO units
    u2 = d.put("smartwatch:nRF54L15-QFAA", *P(204, 66), unit=2, ref="U1", value="nRF54L15-QFAA",
               footprint="Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm", again=True)
    u3 = d.put("smartwatch:nRF54L15-QFAA", *P(204, 118), unit=3, ref="U1", value="nRF54L15-QFAA",
               footprint="Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm", again=True)
    for unit, ports in ((u2, UNIT2_PORTS), (u3, UNIT3_PORTS)):
        for pin, name in ports.items():
            x, y = unit.p(pin)
            d.w((x, y), (x + 14 * U, y))
            d.port(name, x + 14 * U, y, "R", "bidirectional")
    for pin in UNIT2_NC:
        d.nc(*u2.p(pin))

    nx_ = 268 * U
    h = note(d, "Supply: all five VDD pins run from the 1.8 V rail. 10 uF plus four 100 nF as in Table 87. Place each 100 nF "
                "next to its VDD pin and keep the 10 uF close by.", nx_, 28 * U, 56)
    h2 = note(d, "Regulators: L1 4.7 uH from DCC to DECD, FB1 from DECD to DECA, C1 2.2 uF on DECD, C2 2.2 uF + C12 10 nF + "
                 "C5 2.2 nF on DECA (DECRF is tied to DECA).", nx_, 28 * U + h + 3, 56)
    h3 = note(d, "VSS_PA (pin 32) goes to ground ONLY at the exposed pad, through net tie NT1. The RF network C6 returns to "
                 "VSS_PA on the top layer (see the RF sheet).", nx_, 28 * U + h + h2 + 6, 56)
    h4 = note(d, "Clocks: 32 MHz crystal on XC1/XC2, 32.768 kHz crystal on P1.00/P1.01. No external load capacitors: "
                 "internal load capacitors are used (CL 8 pF and 9 pF).", nx_, 28 * U + h + h2 + h3 + 9, 56)
    h5 = note(d, "Reset: R1 1 kOhm in series, C13 3.9 pF to ground. SWDIO, SWDCLK and nRESET go to the Tag-Connect pads on "
                 "the test sheet.", nx_, 28 * U + h + h2 + h3 + h4 + 12, 56)
    h6 = note(d, "GPIO plan: SPI on P2 (SCK on clock pin P2.01), I2C on P0 (SCL on clock pin P0.04), sensor interrupts on P0. "
                 "P1.04 to P1.07 and P1.09 to P1.14 are left open because of errata 100. P1.02/P1.03 are NFC and unused. "
                 "Errata 103: GPIO state is undefined for 10 us at reset, so LED_BOOST_EN has a pull-down.",
              nx_, 28 * U + h + h2 + h3 + h4 + h5 + 15, 56)
