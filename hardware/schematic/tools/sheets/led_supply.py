"""LED supply: TPS61240 5 V boost with two 0 Ohm links to VLED. A4, drawn left to right."""
from .common import U, P, part, note

TP = "TPS61240 DS SLVS806D"


def draw(d):
    d.head("LED SUPPLY  -  5.0 V boost (TPS61240) and the VLED link", 12 * U, 16 * U)
    d.sub("Battery system rail VSYS goes in on the left; the 5 V boost output or VSYS itself feeds the green LED rail VLED.",
          12 * U, 19.5 * U)

    # ------------------------------------------------------------------ boost converter
    d.frame(*P(12, 23), *P(86, 82), heading="TPS61240  -  5.0 V BOOST")
    u = d.put("smartwatch:TPS61240", *P(62, 62), ref="U5", value="TPS61240DRVR",
              footprint="Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm",
              props={"Datasheet": "hardware/datasheets/TPS61240.pdf"})
    sw, vin, en, vo, fb = u.p(5), u.p(6), u.p(4), u.p(2), u.p(3)

    # input: VSYS rail, one vertical bus; CIN hangs off a rail bar, the inductor and VIN branch off the bus
    bx, rail_y = 28 * U, 40 * U
    d.rail("VSYS", bx, 35 * U)
    d.w((bx, 35 * U), (bx, vin[1]))
    d.w((bx, rail_y), (22 * U, rail_y))
    cin = part(d, "C", "C22", "2.2uF", "0402", 22, 42, "X5R 6.3V min", TP + " Table 2")
    d.w((22 * U, rail_y), cin.p(1))
    d.gnd(*cin.p(2))
    l5 = part(d, "L", "L5", "1.0uH", "0805", 41, sw[1] / U, "1.0 uH min, Isat > 0.9 A", TP + " Table 2/3", rot=90, mpn="LQM21PN1R0MC0")
    d.w((bx, sw[1]), l5.p(1))
    d.w(l5.p(2), sw)
    d.w((bx, vin[1]), vin)
    # enable: port on the left, pull-down keeps the boost off while the processor pins float (errata 103)
    d.port("LED_BOOST_EN", 16 * U, en[1], "L")
    d.w((16 * U, en[1]), en)
    r11 = part(d, "R", "R11", "100k", "0201", 46, en[1] / U + 2, "pull-down", "nRF54L15 errata 103")
    d.gnd(*r11.p(2))

    # output: VOUT and FB are tied (fixed-output part), COUT hangs on the output wire
    d.w(vo, fb)
    ox = 76 * U
    d.w(vo, (ox + 4 * U, vo[1]))
    cout = part(d, "C", "C23", "10uF", "0603", 76, vo[1] / U + 2, "X5R 10V (effective >= 2.7 uF at 5 V)", TP + " 10.2.2.4")
    d.gnd(*cout.p(2))
    # ground pins: GND and PowerPAD, one ground symbol
    g1, g2 = u.p(1), u.p(7)
    d.w(g1, g2)
    d.w(g1, (g1[0], g1[1] + 3 * U))
    d.gnd(g1[0], g1[1] + 3 * U)

    # ------------------------------------------------------------------ VLED link
    d.frame(*P(89, 23), *P(136, 82), heading="VLED  -  PICK ONE SOURCE")
    bus = 120 * U
    r12 = part(d, "R", "R12", "0R", "0402", 106, vo[1] / U, "VLED from the boost (default, fitted)", "power tree option B", rot=90)
    r13 = part(d, "R", "R13", "0R", "0402", 106, 46, "VLED straight from VSYS (DNP, power tree option A)", "power tree option A",
               rot=90, dnp=True)
    d.w((ox + 4 * U, vo[1]), r12.p(1))
    d.w(r12.p(2), (bus, vo[1]))
    d.rail("VSYS", 96 * U, 46 * U)
    d.w((96 * U, 46 * U), r13.p(1))
    d.w(r13.p(2), (bus, 46 * U))
    d.rail("VLED", bus, 38 * U)
    d.w((bus, 38 * U), (bus, vo[1]))
    flag = d.put("power:PWR_FLAG", 126 * U, 52 * U, 0, ref="#FLG1", value="PWR_FLAG", prefix="#FLG")
    d.w((bus, 52 * U), (126 * U, 52 * U))
    d.caption("FIT ONE", 98 * U, 41 * U)

    # ------------------------------------------------------------------ notes
    nx = 142 * U
    h = note(d, "TPS61240 is a fixed 5.0 V boost. The inductor must be 1.0 uH or more (L5, saturation current above 0.9 A). "
                "CIN (C22) is 2.2 uF. COUT (C23) must keep at least 2.7 uF effective at 5 V, so a 10 uF 10 V part is used. "
                "Keep CIN and COUT close to the pins.", nx, 28 * U, 82)
    h2 = note(d, "EN needs only 1.0 V, so the 1.8 V logic level from the processor is enough. R11 holds EN low while the "
                 "processor pins float after reset (nRF54L15 errata 103).", nx, 28 * U + h + 3, 82)
    note(d, "VLED has two possible sources. R12 (boost, fitted) is the default. R13 (VSYS direct, not fitted) is power tree "
            "option A for comparison. Fit only one of the two. The PWR_FLAG tells ERC that VLED is driven.",
         nx, 28 * U + h + h2 + 6, 82)
    note(d, "Option A check: VLED must stay inside 3.1 to 5.5 V. The green LED needs its forward voltage (2.8 V max at 20 mA) "
            "plus about 0.9 V driver headroom, so about 3.7 V: with a 3.0 to 4.2 V cell the green channel drops out at the "
            "bottom of the discharge. Red and IR work down to about 3.1 V. The boost (R12) has no such limit.",
         12 * U, 88 * U, 100)
