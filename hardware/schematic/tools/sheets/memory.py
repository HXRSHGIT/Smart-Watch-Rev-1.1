"""Memory: Macronix MX25R3235F 32 Mbit SPI NOR flash on the shared SPI bus. A4, left to right."""
from .common import U, P, part, note

MX = "MX25R3235F DS rev 1.6"


def draw(d):
    d.head("MEMORY  -  MX25R3235F 32 Mbit SPI flash", 12 * U, 16 * U)
    d.sub("The flash shares the SPI bus with the optical front end. Its chip select CS_FLASH comes from the processor. "
          "1.8 V supply (allowed 1.65 to 3.6 V).", 12 * U, 19.5 * U)
    d.frame(*P(12, 23), *P(112, 90), heading="MX25R3235FZBIL0  -  8-LAND USON 4 x 3 mm")

    u = d.put("smartwatch:MX25R3235F", *P(70, 58), ref="U8", value="MX25R3235FZBIL0",
              footprint="smartwatch:MX25R3235F_USON-8_4x3mm_P0.8mm", props={"Datasheet": "hardware/datasheets/MX25R3235F_rev1.6.pdf"})
    cs, sck, si, so = u.p("1"), u.p("6"), u.p("5"), u.p("2")
    px = 24 * U
    for pin, name, shape in ((cs, "CS_FLASH", "bidirectional"), (sck, "SPI_SCK", "bidirectional"),
                             (si, "SPI_MOSI", "bidirectional"), (so, "SPI_MISO", "output")):
        d.w((px, pin[1]), pin)
        d.port(name, px, pin[1], "L", shape)
    for k, (pin, name) in enumerate(((sck, "SPI_SCK"), (si, "SPI_MOSI"), (so, "SPI_MISO"))):       # bus test points
        d.put("Connector:TestPoint", 32 * U, pin[1], 180, ref=f"TP{8 + k}", value=f"TP {name}",
              footprint="TestPoint:TestPoint_Pad_D1.0mm", prefix="TP", tside="R")
    # CS# pull-up: keeps the flash deselected while the processor pins float (datasheet section 12, nRF54L15 errata 103)
    r18 = part(d, "R", "R18", "100k", "0201", 40, cs[1] / U - 2, "CS# pull-up", MX + " power-on state; nRF54L15 errata 103")
    d.rail("+1V8", *r18.p(1))
    d.w(r18.p(2), (r18.p(2)[0], cs[1]))

    # supply: stem up to the rail, 100 nF hangs from a short bar
    vcc = u.p("8")
    sy = vcc[1] - 6 * U
    d.w(vcc, (vcc[0], sy))
    d.w((vcc[0], sy - 2 * U), (vcc[0] + 8 * U, sy - 2 * U))
    d.w((vcc[0], sy), (vcc[0], sy - 4 * U))
    d.rail("+1V8", vcc[0], sy - 4 * U)
    c32 = part(d, "C", "C32", "100nF", "0201", vcc[0] / U + 8, sy / U, "X7R 10%, close to the VCC land", MX + " section 12")
    d.w((vcc[0] + 8 * U, sy - 2 * U), c32.p(1))
    d.gnd(*c32.p(2))
    # ground
    g = u.p("4")
    d.w(g, (g[0], g[1] + 2 * U))
    d.gnd(g[0], g[1] + 2 * U)
    # WP# and RESET# stay open: internal pull-ups
    d.nc(*u.p("3"))
    d.nc(*u.p("7"))

    nx = 120 * U
    h = note(d, "Part: MX25R3235FZBIL0, 8-land USON 4 x 3 mm, ultra-low-power default mode, pin 7 = RESET#. VCC 1.65 to 3.6 V, "
                "so the 1.8 V rail is fine. 100 nF (C32) close to VCC, as the datasheet recommends.", nx, 28 * U, 100)
    h2 = note(d, "SPI: mode 0 or 3. Up to 33 MHz for READ and 8 MHz for other commands in ultra-low-power mode, but the MAX86141 on the "
                 "same bus allows only 4 MHz, so run the bus at 4 MHz or less while the MAX86141 is selected. SO is high impedance "
                 "while CS# is high, so the bus can be shared (the MAX86141 SDO is also high impedance when CSB is high).",
              nx, 28 * U + h + 3, 100)
    h3 = note(d, "R18 pulls CS# to 1.8 V so the flash stays deselected while the processor pins float after reset "
                 "(nRF54L15 errata 103) and during power-up and power-down (datasheet section 12).", nx, 28 * U + h + h2 + 6, 100)
    h4 = note(d, "TP8 to TP10 are test points on the SPI clock, MOSI and MISO lines for the production fixture. WP# (pin 3) and RESET# (pin 7) are left open: both have an internal pull-up while not connected "
                 "(datasheet section 3, note 1). Use the Reset command if a hardware reset is ever needed.",
              nx, 28 * U + h + h2 + h3 + 9, 100)
    h5 = note(d, "The two metal pads under the package must stay floating or go to ground only, with no vias or traces under "
                 "them (datasheet section 19-4). Deep power-down is 0.35 uA maximum.", nx, 28 * U + h + h2 + h3 + h4 + 12, 100)
    note(d, "Open item: land pattern 0.35 x 0.9 mm per pad is drawn from the package outline. Compare with the Macronix "
            "recommended land pattern before layout.", nx, 28 * U + h + h2 + h3 + h4 + h5 + 15, 100)
