"""Programming and test access: Tag-Connect SWD pads and the production test points. A4."""
from .common import U, P, note

TP_FP = "TestPoint:TestPoint_Pad_D1.0mm"


def draw(d):
    d.head("PROGRAMMING AND TEST ACCESS  -  Tag-Connect SWD pads and test points", 12 * U, 16 * U)
    d.sub("The pads are a plug-in cable footprint without a connector. Test points serve the production fixture.", 12 * U, 19.5 * U)

    d.frame(*P(12, 23), *P(76, 76), heading="TAG-CONNECT TC2030-NL  -  SWD")
    j = d.put("smartwatch:TC2030_SWD", *P(30, 56), ref="J3", value="TC2030-NL",
              footprint="Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical", ctext="TL")
    x, y = j.p("1")
    d.w((x, y), (x + 3 * U, y))
    d.rail("+1V8", x + 3 * U, y)
    for pin, name in (("2", "SWDIO"), ("3", "NRESET"), ("4", "SWDCLK"), ("6", "SWO")):
        px, py = j.p(pin)
        d.w((px, py), (68 * U, py))
        d.port(name, 68 * U, py, "R", "bidirectional")
    gx, gy = j.p("5")
    d.w((gx, gy), (gx + 3 * U, gy))
    d.gnd(gx + 3 * U, gy)

    d.frame(*P(79, 23), *P(122, 76), heading="SUPPLY TEST POINTS")
    for k, rail in enumerate(("+1V8", "VSYS", "VLED", "GND", "GND")):
        py = (38 + 6 * k) * U
        if rail == "GND":
            d.gnd(86 * U, py)
        else:
            d.rail(rail, 86 * U, py)
        d.w((86 * U, py), (102 * U, py))
        d.put("Connector:TestPoint", 102 * U, py, 270, ref=f"TP{k + 1}", value=f"TP {rail}", footprint=TP_FP, prefix="TP", tside="L")
    nx = 126 * U
    h = note(d, "Tag-Connect TC2030-NL pin order (to be confirmed against the cable drawing): 1 VTREF, 2 SWDIO, 3 nRESET, "
                "4 SWDCLK, 5 GND, 6 SWO. VTREF takes the 1.8 V rail so the programmer senses the target voltage.",
             nx, 28 * U, 50)
    h2 = note(d, "Test points are plain 1.0 mm pads. Put them on one side of the board where the production fixture can reach "
                 "them (research/storage-nfc-dft/DFT_PROGRAMMING.md). The bus test points sit on the sheets that own the bus: "
                 "I2C on the sensors sheet, SPI on the memory sheet, PPG_INT on the optical sheet.", nx, 28 * U + h + 3, 50)
    note(d, "Open items: confirm the Tag-Connect pin order, and decide which test points stay on the final board.",
         nx, 28 * U + h + h2 + 6, 50)
