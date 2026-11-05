"""Optical sensing: MAX86141 front end, SFH 7016 emitter, two VEMD8080 photodiodes. A3, drawn left to right."""
from .common import U, P, part, note

MX = "MAX86141 DS Rev 5"
LINK = "bring-up current measurement"


def draw(d):
    d.head("OPTICAL SENSING  -  MAX86141, SFH 7016 emitter, 2 x VEMD8080", 12 * U, 16 * U)
    d.sub("The processor talks to the front end over SPI. The front end drives the three LEDs and reads two photodiodes. "
          "Supply 1.8 V, LED supply VLED.", 12 * U, 19.5 * U)

    u = d.put("smartwatch:MAX86141", *P(86, 74), ctext="BL", ref="U2", value="MAX86141ENP+",
              footprint="smartwatch:MAX86141_WLP-20_2.048x1.848mm_P0.4mm", props={"Datasheet": "hardware/datasheets/MAX86141_rev5.pdf"})

    led3 = u.p("B1")[1] / U
    d.frame(*P(12, 23), *P(112, 126), heading="MAX86141  -  OPTICAL FRONT END")
    d.frame(*P(115, 23), *P(176, led3 + 9), heading="SFH 7016  -  EMITTER")
    d.frame(*P(115, led3 + 11), *P(176, 126), heading="VEMD8080  -  PHOTODIODES")

    # ------------------------------------------------------------------ supply row (top)
    vled, vana, vdig = u.p("A1"), u.p("D2"), u.p("C2")
    top_y = vled[1] - 8 * U
    d.w(vled, (vled[0], top_y))
    d.rail("VLED", vled[0], top_y)
    d.w((vled[0], top_y + 3 * U), (vled[0] - 8 * U, top_y + 3 * U))
    c18 = part(d, "C", "C18", "10uF", "0603", vled[0] / U - 8, top_y / U + 5, "10V X5R (VLED up to 5.5 V)", MX + " p.12", tside="L")
    d.w((vled[0] - 8 * U, top_y + 3 * U), c18.p(1))
    d.gnd(*c18.p(2))
    d.w(vana, vdig)
    d.w(vana, (vana[0], top_y))
    d.rail("+1V8", vana[0], top_y)
    d.w((vana[0], top_y + 3 * U), (vana[0] + 12 * U, top_y + 3 * U))
    c15 = part(d, "C", "C15", "22uF", "0402", vana[0] / U + 6, top_y / U + 5, "6.3V or higher, effective ~10 uF", MX + " p.49", tside="L")
    c16 = part(d, "C", "C16", "100nF", "0201", vana[0] / U + 12, top_y / U + 5, "at the VDD_ANA ball", MX + " p.12")
    d.w((vana[0] + 6 * U, top_y + 3 * U), c15.p(1))
    d.w((vana[0] + 12 * U, top_y + 3 * U), c16.p(1))
    d.w(c15.p(2), c16.p(2))
    d.gnd(*c15.p(2))

    # ------------------------------------------------------------------ ground row (bottom)
    g1, g2, g3 = u.p("D3"), u.p("C4"), u.p("C3")
    d.w(g1, g3)
    d.w(g2, (g2[0], g2[1] + 3 * U))
    d.gnd(g2[0], g2[1] + 3 * U)

    # ------------------------------------------------------------------ left: interrupt lines and SPI
    px = 24 * U
    for pin, name, shape, pull, ref in (("B2", "PPG_INT", "output", True, "R4"), ("B3", "PPG_GPIO1", "bidirectional", True, "R5"),
                                        ("B4", "PPG_GPIO2", "bidirectional", False, None), ("A5", "CS_PPG", "bidirectional", False, None),
                                        ("A2", "SPI_SCK", "bidirectional", False, None), ("A4", "SPI_MOSI", "bidirectional", False, None),
                                        ("A3", "SPI_MISO", "output", False, None)):
        x, y = u.p(pin)
        d.w((px, y), (x, y))
        d.port(name, px, y, "L", shape)
        if pull:
            r = part(d, "R", ref, "100k", "0201", 46, y / U - 2, "pull-up", "MAXREFDES103 " + ("R12" if ref == "R4" else "R23"))
            d.rail("+1V8", *r.p(1))

    ix, iy = u.p("B2")
    d.put("Connector:TestPoint", 32 * U, iy, 180, ref="TP11", value="TP PPG_INT", footprint="TestPoint:TestPoint_Pad_D1.0mm",
          prefix="TP", tside="R")

    # ------------------------------------------------------------------ right: LED drive
    sfh = d.put("smartwatch:SFH7016", 146 * U, u.p("D1")[1] + 7 * U, 0, ref="D1", value="SFH 7016",
                footprint="smartwatch:SFH7016_1.85x1.65mm", props={"Datasheet": "hardware/datasheets/SFH7016.pdf"}, prefix="D")
    for pin_u, pin_d, ref in (("D1", "3", "R6"), ("C1", "1", "R7"), ("B1", "4", "R8")):
        x, y = u.p(pin_u)
        r = part(d, "R", ref, "0R", "0201", 124, y / U, "link", LINK, rot=90)
        d.w((x, y), r.p(1))
        d.w(r.p(2), sfh.p(pin_d))
    d.w(sfh.p(2), sfh.p(5))
    d.w(sfh.p(2), (sfh.p(2)[0], sfh.p(2)[1] - 3 * U))
    d.rail("VLED", sfh.p(2)[0], sfh.p(2)[1] - 3 * U)
    d.nc(*sfh.p(6))

    # ------------------------------------------------------------------ right: photodiodes
    pg, p2, p1 = u.p("C5"), u.p("D4"), u.p("D5")
    pd1 = d.put("smartwatch:VEMD8080", 130 * U, p1[1] + 11 * U, 0, ref="PD1", value="VEMD8080",
                footprint="smartwatch:VEMD8080_4.8x2.5mm", props={"Datasheet": "hardware/datasheets/VEMD8080.pdf"}, prefix="PD")
    pd2 = d.put("smartwatch:VEMD8080", 150 * U, p1[1] + 11 * U, 0, ref="PD2", value="VEMD8080",
                footprint="smartwatch:VEMD8080_4.8x2.5mm", props={"Datasheet": "hardware/datasheets/VEMD8080.pdf"}, prefix="PD")
    k1, k2, a1, a2 = pd1.p(1), pd2.p(1), pd1.p(5), pd2.p(5)
    d.w(p1, (k1[0], p1[1]), k1)
    d.w(p2, (k2[0], p2[1]), k2)
    gx = 164 * U
    d.w(pg, (gx, pg[1]), (gx, a1[1] + 3 * U), (a1[0], a1[1] + 3 * U), a1)
    d.w((a2[0], a1[1] + 3 * U), a2)
    nt = d.put("Device:NetTie_2", gx, a1[1] + 9 * U, 90, ref="NT3", value="NetTie", footprint="NetTie:NetTie-2_SMD_Pad0.5mm",
               props={"Source": MX + " layout guidelines p.49: PD_GND to ground at one point"}, prefix="NT")
    top, bot = (nt.p(1), nt.p(2)) if nt.p(1)[1] < nt.p(2)[1] else (nt.p(2), nt.p(1))
    d.w((gx, a1[1] + 3 * U), top)
    d.gnd(*bot)
    d.caption("PD_GND", gx + 2 * U, pg[1] + 4 * U, size=1.27)

    # ------------------------------------------------------------------ VREF
    vr = u.p("B5")
    c17 = part(d, "C", "C17", "1uF", "0201", vr[0] / U + 7, vr[1] / U + 2, "6.3V (VREF is 1.21 V)", MX + " p.12")
    d.w(vr, (vr[0] + 7 * U, vr[1]))
    d.gnd(*c17.p(2))

    # ------------------------------------------------------------------ notes
    nx = 180 * U
    h = note(d, "Supply: VDD_ANA and VDD_DIG are tied and run from the 1.8 V rail (allowed 1.7 to 2.0 V). 22 uF plus 100 nF "
                "on the supply, 1 uF on VREF, 10 uF on VLED. Keep C16 at the VDD_ANA ball. (MAX86141 datasheet p.12 and p.49)",
             nx, 28 * U, 56)
    h2 = note(d, "PGND, GND_ANA and GND_DIG meet at one ground. PD_GND is a separate net that touches ground at ONE point "
                 "only, through net tie NT3 (datasheet layout guidelines p.49).", nx, 28 * U + h + 3, 56)
    h3 = note(d, "LED channel order follows MAXREFDES103: LED1 = green, LED2 = IR, LED3 = red. R6, R7 and R8 are 0 Ohm links "
                 "so the LED current can be measured during bring-up.", nx, 28 * U + h + h2 + 6, 56)
    h4 = note(d, "PPG_INT and PPG_GPIO1 are open-drain outputs, so R4 and R5 (100 kOhm) pull them up to 1.8 V. "
                 "SDO is high impedance while CSB is high, so the SPI bus can be shared.", nx, 28 * U + h + h2 + h3 + 9, 56)
    h5 = note(d, "VEMD8080: anode is pin 5, cathodes are pins 1-4 and 6-8 (one net, drawn as one pin). Numbering and pad "
                 "pattern checked against the Vishay package drawing (top view).",
              nx, 28 * U + h + h2 + h3 + h4 + 12, 56)
    h6 = note(d, "LED limits (SFH 7016): continuous current green 30 mA, red 40 mA, IR 60 mA; pulses 0.75 A, 0.3 A, 1 A at 0.5 % "
                 "duty. Forward voltage at 20 mA: green 2.2 to 2.8 V, red 1.7 to 2.2 V, IR 1.1 to 1.5 V. Firmware must stay "
                 "inside these.", nx, 28 * U + h + h2 + h3 + h4 + h5 + 15, 56)
    h7 = note(d, "SPI: the MAX86141 allows SCLK up to 4 MHz, so keep the bus at or below 4 MHz while it is selected. SDO goes "
                 "high impedance when CSB is high (shared bus with the flash).", nx, 28 * U + h + h2 + h3 + h4 + h5 + h6 + 18, 56)
    note(d, "VREF: the datasheet asks for 1 uF (C17). Maxim's MAXREFDES103 board fits 10 uF there. If the noise floor is "
            "higher than expected during bring-up, try 10 uF.", nx, 28 * U + h + h2 + h3 + h4 + h5 + h6 + h7 + 21, 56)
