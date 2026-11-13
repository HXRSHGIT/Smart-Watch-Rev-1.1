"""Charging input: two pogo pads into the ST OCVPB21-13F6 (bridge, ESD, overvoltage, current limit). A4."""
from .common import U, P, part, note

OV = "OCVPB21-13F6 DS13107 Rev 3"


def draw(d):
    d.head("CHARGING INPUT  -  two pogo pads, OCVPB21-13F6, charger", 12 * U, 16 * U)
    d.sub("Either polarity is accepted. The protected 5 V output (VBUS_PROT) goes to the charger on the power sheet.",
          12 * U, 19.5 * U)

    d.frame(*P(12, 23), *P(130, 88), heading="POGO PADS  >  PROTECTION  >  VBUS_PROT")
    u = d.put("smartwatch:OCVPB21-13F6", *P(66, 62), ref="U6", value="OCVPB21-13F6",
              footprint="smartwatch:OCVPB21-13F6_WLCSP-13_P0.4mm", props={"Datasheet": "hardware/datasheets/OCVPB21-13F6.pdf"})
    ina, inb = u.p("D1"), u.p("D3")

    # pogo pads: two pads, wires step in to the two input pins
    j1 = d.put("Connector_Generic:Conn_01x01", 22 * U, ina[1] - 7 * U, 180, ref="J1", value="Pogo pad",
               footprint="smartwatch:Pogo_Pad_D2.6mm", props={"Source": "research/power-battery/POGO_CHARGING.md"}, prefix="J", tside="L")
    j2 = d.put("Connector_Generic:Conn_01x01", 22 * U, inb[1] + 7 * U, 180, ref="J2", value="Pogo pad",
               footprint="smartwatch:Pogo_Pad_D2.6mm", props={"Source": "research/power-battery/POGO_CHARGING.md"}, prefix="J", tside="L")
    p1, p2 = j1.p(1), j2.p(1)
    d.w(p1, (42 * U, p1[1]), (42 * U, ina[1]), ina)
    d.w(p2, (42 * U, p2[1]), (42 * U, inb[1]), inb)
    # 2.54 mm header on the same two nets as the pads (before the OCVPB21, so it is protected too): bench supply or USB breakout
    j5 = d.put("Connector_Generic:Conn_01x02", 22 * U, (p1[1] + p2[1]) / 2 - U, 180, ref="J5", value="5 V in",
               footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
               props={"Source": "iteration 1: 5 V input without pogo contact"}, prefix="J", tside="L")
    # rotated 180 degrees pin 2 is the upper pin: pin 2 to POGO_A (above), pin 1 to POGO_B (below), so no wires cross
    d.w(j5.p(2), (40 * U, j5.p(2)[1]), (40 * U, p1[1]))
    d.w(j5.p(1), (40 * U, j5.p(1)[1]), (40 * U, p2[1]))
    d.caption("POGO A", 14 * U, ina[1] / U * U - 10 * U)
    d.caption("POGO B", 14 * U, p2[1] + 6 * U)

    # protected output: 10 uF on the output, then the rail symbol
    out = u.p("B2")
    c24 = part(d, "C", "C24", "22uF", "0805", 88, out[1] / U + 2, "X5R 16V low ESR, >= 10 uF effective at 5 V", OV + " Table 2")
    d.w(out, (104 * U, out[1]))
    d.rail("VBUS_PROT", 104 * U, out[1] - 3 * U)
    d.w((104 * U, out[1]), (104 * U, out[1] - 3 * U))
    d.gnd(*c24.p(2))

    # FLAG: open drain, pull-up to 1.8 V, port to the processor
    flag = u.p("E3")
    r15 = part(d, "R", "R15", "100k", "0201", 100, flag[1] / U - 2, "FLAG pull-up", OV + " Table 2")
    d.rail("+1V8", *r15.p(1))
    d.w(flag, (112 * U, flag[1]))
    d.port("CHG_FLAG", 112 * U, flag[1], "R", "output")

    # RLIM to ground
    rl = u.p("E1")
    r14 = part(d, "R", "R14", "180R", "0402", rl[0] / U, rl[1] / U + 5, "1% or better, 51-270 Ohm allowed", OV + " section 1.2", tside="L")
    d.w(rl, r14.p(1))
    d.gnd(*r14.p(2))

    # grounds: bridge, ESD and data grounds tied, one ground symbol
    gb, ge, gd = u.p("E2"), u.p("C3"), u.p("A3")
    d.w(gb, ge)
    d.w(ge, gd)
    d.w(ge, (ge[0], ge[1] + 3 * U))
    d.gnd(ge[0], ge[1] + 3 * U)

    # unused data and rectifier pins
    for pin in ("C2", "A2", "B3", "A1", "B1"):
        d.nc(*u.p(pin))

    nx = 136 * U
    h = note(d, "OCVPB21-13F6 combines a polarity bridge, ESD clamps, overvoltage cut-off and a current limit. "
                "Input range 4.25 to 5.55 V. OUT_5V needs 10 uF or more at 5 V (C24, 22 uF).", nx, 28 * U, 88)
    h2 = note(d, "RLIM (R14) sets the current limit: ILIM = (318 - RLIM) / 0.447 mA. 180 Ohm gives about 310 mA.",
              nx, 28 * U + h + 3, 88)
    h3 = note(d, "FLAG is open drain. R15 pulls it up to 1.8 V, so the processor reads a low level when a fault is "
                 "reported (CHG_FLAG).", nx, 28 * U + h + h2 + 6, 88)
    h4 = note(d, "J5 is a 2.54 mm header on the same POGO_A and POGO_B nets as the pads, for a bench supply or a USB "
                 "breakout (5 V and ground wires only) in iteration 1. Either polarity (pin 1 = POGO_B, pin 2 = POGO_A), 5.0 to 5.5 V. It sits before the "
                 "OCVPB21, so the bridge, overvoltage and current limit protect it as well.", nx, 28 * U + h + h2 + h3 + 9, 88)
    note(d, "Operating temperature of this part is -30 to +65 degC. Keep that in mind for the charging case. The data "
            "pins are not used with two pogo pads, so they are left open (crosses). C24 is 22 uF 16 V X5R 0805: X5R loses "
            "capacitance under DC bias, so 22 uF is chosen to keep 10 uF or more at 5 V. Confirm with the DC-bias curve of "
            "the part that is bought.", nx, 28 * U + h + h2 + h3 + h4 + 12, 88)
