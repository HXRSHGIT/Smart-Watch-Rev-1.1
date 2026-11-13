"""Power: nPM1300 PMIC (charger, 1.8 V buck, VSYS), battery connector, ship-mode button. A3, inputs left, outputs right."""
from .common import U, P, part, note

NP = "nPM1300 PS v1.3"
CFG2 = NP + " Reference circuitry, Configuration 2"


def draw(d):
    d.head("POWER  -  nPM1300 charger, 1.8 V buck, battery", 12 * U, 16 * U)
    d.sub("Charger input VBUS_PROT and the battery come in on the left; VSYS and the 1.8 V rail leave on the right. "
          "Nordic reference circuit, configuration 2 (one buck, no USB-C, no LEDs).", 12 * U, 19.5 * U)
    d.frame(*P(12, 23), *P(176, 136), heading="nPM1300  -  CHARGER, BUCK 1, SYSTEM RAIL")

    cx, cy = 112, 82
    u = d.put("smartwatch:nPM1300-QEAA", *P(cx, cy), ref="U7", value="nPM1300-QEAA",
              footprint="Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm",
              props={"Datasheet": "hardware/datasheets/nPM1300_PS_v1.3.txt"})
    LX, RX = u.p("21")[0], u.p("22")[0]
    lx, rx = LX / U, RX / U
    L = lambda pin: u.p(pin)               # pin tip, sheet mm
    Y = lambda pin: u.p(pin)[1] / U        # pin row, grid units

    # ============================================================ LEFT: charger input, battery, controls, bus
    # VBUS: wire to the left, stem up to the VBUS_PROT rail, C25 hangs below the wire
    vb = L("21")
    d.w(vb, ((lx - 15) * U, vb[1]))
    d.rail("VBUS_PROT", (lx - 15) * U, vb[1] - 3 * U)
    d.w(((lx - 15) * U, vb[1]), ((lx - 15) * U, vb[1] - 3 * U))
    c25 = part(d, "C", "C25", "1uF", "0603", lx - 9, Y("21") + 2, "X5R 10V 10%", CFG2 + " C1", tside="L")
    d.w(((lx - 9) * U, vb[1]), c25.p(1))
    d.gnd(*c25.p(2))
    d.caption("VBUS_PROT FROM THE CHARGING INPUT", (lx - 36) * U, vb[1] - 8 * U, size=1.27)

    # CC1 and CC2: no USB-C connector, so both go to ground (datasheet: floating or ground)
    cc1, cc2 = L("23"), L("24")
    d.w(cc1, ((lx - 5) * U, cc1[1]), ((lx - 5) * U, cc2[1]))
    d.w(cc2, ((lx - 5) * U, cc2[1]))
    d.w(((lx - 5) * U, cc2[1]), ((lx - 5) * U, cc2[1] + 2 * U))
    d.gnd((lx - 5) * U, cc2[1] + 2 * U)

    # battery connector: BAT+ on the VBAT row, NTC on the NTC row, GND on the ground bar
    vbat, ntc = L("19"), L("18")
    off = d.lib.pins("smartwatch:Battery_Conn_3")[(1, "1")][1]
    j4 = d.put("smartwatch:Battery_Conn_3", (lx - 32) * U, vbat[1] + off, 0, ref="J4", value="Battery",
               footprint="Connector_JST:JST_SH_SM03B-SRSS-TB_1x03-1MP_P1.00mm_Horizontal",
               props={"Source": "battery cell and connector: open item", "Spec": "not fitted in iteration 1 (no battery)"},
               prefix="J", tside="L", dnp=True)
    d.w(j4.p(1), vbat)
    c30 = part(d, "C", "C30", "2.2uF", "0603", lx - 10, Y("19") + 2, "X7R 16V 10%", CFG2 + " C6", tside="L")
    d.w(((lx - 10) * U, vbat[1]), c30.p(1))
    d.gnd(*c30.p(2))
    d.w(j4.p(2), ntc)
    rn = part(d, "R", "R17", "10k", "0201", lx - 18, Y("18") + 2,
              "NTC substitute: fitted while J4 is empty (iteration 1); remove when a pack WITH thermistor goes on J4",
              NP + " NTC thermistor configuration", tside="R")
    d.w(((lx - 18) * U, ntc[1]), rn.p(1))
    d.w(j4.p(3), rn.p(2))
    d.gnd(*rn.p(2))
    d.caption("BATTERY PACK WITH NTC (NOT FITTED IN ITERATION 1)", (lx - 36) * U, vbat[1] - 5 * U, size=1.27)

    # VSET1: 68 kOhm to ground = 2.0 V at power-up (firmware lowers it to 1.9 V); VSET2: ground = buck 2 off
    v1, v2 = L("17"), L("16")
    r16 = part(d, "R", "R16", "68k", "0201", lx - 10, Y("17") + 2, "1% (sets BUCK1 = 2.0 V at power-up, firmware sets 1.9 V)",
               NP + " BUCK output voltage selection", tside="L")
    d.w(v1, r16.p(1))
    d.gnd(*r16.p(2))
    d.w(v2, ((lx - 4) * U, v2[1]), ((lx - 4) * U, v2[1] + 2 * U))
    d.gnd((lx - 4) * U, v2[1] + 2 * U)

    # SHPHLD: button to ground (exits ship mode; 10 s hold = hard reset)
    sh = L("15")
    sw = d.put("Switch:SW_SPST", (lx - 10) * U, sh[1], 0, ref="SW1", value="Ship mode / reset",
               footprint="Button_Switch_SMD:SW_SPST_B3U-1000P", props={"Source": NP + " Ship and Hibernate modes"}, prefix="SW")
    d.w(sh, sw.p(2))
    d.w(sw.p(1), (sw.p(1)[0] - 4 * U, sw.p(1)[1]), (sw.p(1)[0] - 4 * U, sw.p(1)[1] + 2 * U))
    d.gnd(sw.p(1)[0] - 4 * U, sw.p(1)[1] + 2 * U)
    d.caption("SHIP MODE / RESET BUTTON", (lx - 44) * U, sh[1] + 0.5 * U, size=1.27)

    # I2C: straight to the sheet ports
    for pin, name in (("14", "I2C_SCL"), ("13", "I2C_SDA")):
        x, y = L(pin)
        d.w((x, y), ((lx - 40) * U, y))
        d.port(name, (lx - 40) * U, y, "L", "bidirectional")

    # VDDIO to the 1.8 V rail, 100 nF
    vi = L("12")
    d.w(vi, ((lx - 11) * U, vi[1]))
    d.w(((lx - 5) * U, vi[1]), ((lx - 5) * U, vi[1] - 3 * U))
    d.rail("+1V8", (lx - 5) * U, vi[1] - 3 * U)
    c31 = part(d, "C", "C31", "100nF", "0201", lx - 11, Y("12") + 2, "X5R 10%", CFG2 + " C13", tside="L")
    d.w(((lx - 11) * U, vi[1]), c31.p(1))
    d.gnd(*c31.p(2))

    # ============================================================ RIGHT: VBUSOUT, VSYS, buck 1, unused pins
    # VBUSOUT: decoupling only
    vo = L("22")
    c26 = part(d, "C", "C26", "1uF", "0603", rx + 6, Y("22") + 2, "X5R 10V 10%, mandatory on VBUSOUT", CFG2 + " C5")
    d.w(vo, c26.p(1))
    d.gnd(*c26.p(2))

    # VSYS and PVDD joined; bar to the right with C28 (to ground) and C27 (to PVSS1)
    vs, pv = L("20"), L("4")
    d.w(vs, ((rx + 4) * U, vs[1]))
    d.w(pv, ((rx + 4) * U, pv[1]), ((rx + 4) * U, vs[1]))
    bar_end = (rx + 30) * U
    d.w(((rx + 4) * U, vs[1]), (bar_end, vs[1]))
    d.w((bar_end, vs[1]), (bar_end, vs[1] - 3 * U))
    d.rail("VSYS", bar_end, vs[1] - 3 * U)
    c28 = part(d, "C", "C28", "10uF", "0603", rx + 10, Y("20") + 2, "X5R 25V 20%", CFG2 + " C4")
    d.w(((rx + 10) * U, vs[1]), c28.p(1))
    d.gnd(*c28.p(2))
    c27 = part(d, "C", "C27", "10uF", "0603", rx + 24, Y("20") + 2, "X5R 25V 20%, returns to PVSS1", CFG2 + " C2")
    d.w(((rx + 24) * U, vs[1]), c27.p(1))

    # buck 1: SW1 -> L1 -> VOUT1 (+1V8), C7 to PVSS1
    sw1, vo1, pvss1 = L("3"), L("1"), L("2")
    l6 = part(d, "L", "L6", "2.2uH", "0805", rx + 8, (sw1[1] + vo1[1]) / 2 / U, "DCR <= 400 mOhm, Isat > 350 mA, 20%", NP + " BUCK component selection",
              tside="R")
    d.w(sw1, l6.p(1))
    d.w(vo1, l6.p(2))
    d.w(l6.p(2), ((rx + 20) * U, vo1[1]))
    d.w(((rx + 20) * U, vo1[1]), ((rx + 20) * U, vo1[1] - 3 * U))
    d.rail("+1V8", (rx + 20) * U, vo1[1] - 3 * U)
    c29 = part(d, "C", "C29", "10uF", "0603", rx + 14, Y("1") + 2, "X5R 25V 20% (>= 4 uF effective)", CFG2 + " C7")
    d.w(((rx + 14) * U, vo1[1]), c29.p(1))
    d.w(c29.p(2), (c29.p(2)[0], pvss1[1]))
    # PVSS1 line: net tie to ground, C29 and C27 return here
    d.w(pvss1, ((rx + 24) * U, pvss1[1]))
    d.w(c27.p(2), ((rx + 24) * U, pvss1[1]))
    nt = d.put("Device:NetTie_2", (rx + 5) * U, pvss1[1] + 4 * U, 90, ref="NT4", value="NetTie",
               footprint="NetTie:NetTie-2_SMD_Pad0.5mm", props={"Source": CFG2 + " (net tie on PVSS1)"}, prefix="NT", tside="L")
    top, bot = (nt.p(1), nt.p(2)) if nt.p(1)[1] < nt.p(2)[1] else (nt.p(2), nt.p(1))
    d.w(((rx + 5) * U, pvss1[1]), top)
    d.gnd(*bot)
    d.caption("PVSS1 JOINS GROUND ONLY AT THE NET TIE", (rx + 8) * U, pvss1[1] + 3 * U, size=1.27)

    # buck 2 unused: VOUT2 to VSYS, SW2 open, PVSS2 and the four load-switch pins to ground
    v2o = L("32")
    d.w(v2o, ((rx + 12) * U, v2o[1]))
    d.w(((rx + 12) * U, v2o[1]), ((rx + 12) * U, v2o[1] - 3 * U))
    d.rail("VSYS", (rx + 12) * U, v2o[1] - 3 * U)
    d.nc(*L("5"))
    gx = (rx + 4) * U
    pv2 = L("6")
    pins = [L(p) for p in ("28", "30", "29", "31")]
    d.w(pv2, (gx, pv2[1]), (gx, pins[-1][1]))
    for p in pins:
        d.w(p, (gx, p[1]))
    d.gnd(gx, pins[-1][1])
    d.caption("BUCK 2 AND LOAD SWITCHES UNUSED", (rx + 17) * U, v2o[1] + 3 * U, size=1.27)

    # GPIO: GPIO1 is the interrupt output, the rest are open
    for pin in ("7", "9", "10", "11"):
        d.nc(*L(pin))
    g1 = L("8")
    d.w(g1, ((rx + 16) * U, g1[1]))
    d.port("PMIC_IRQ", (rx + 16) * U, g1[1], "R", "output")
    for pin in ("25", "26", "27"):
        d.nc(*L(pin))

    # exposed pad
    av = L("33")
    d.w(av, (av[0], av[1] + 2 * U))
    d.gnd(av[0], av[1] + 2 * U)

    # ============================================================ notes
    nx = 182 * U
    w = 70
    h = note(d, "Input: VBUS comes from the OCVPB21 output (VBUS_PROT) with 1 uF (C25). CC1 and CC2 go to ground because "
                "there is no USB-C connector. The input current limit starts at 100 mA and the next step is 500 mA. The "
                "OCVPB21 limits at about 310 mA (R14 = 51 Ohm for about 600 mA). Iteration 1 has no battery to help "
                "with load peaks: firmware selects 500 mA after boot, and the real limit is then the OCVPB21.", nx, 28 * U, w)
    h2 = note(d, "Buck 1 = 2.0 V at power-up from R16 (68 kOhm on VSET1); firmware sets 1.9 V. L6 2.2 uH (DCR 400 mOhm max, Isat above 350 mA), C29 10 uF "
                 "(at least 4 uF effective). 200 mA maximum. PVSS1 is the power ground of buck 1; it joins ground only "
                 "through net tie NT4.", nx, 28 * U + h + 3, w)
    h3 = note(d, "VSYS and PVDD are one net with 10 uF to PVSS1 (C27) and 10 uF to ground (C28). Never feed VSYS from "
                 "outside. Never power the application from VBAT: use VSYS or VOUT1 only (datasheet).",
              nx, 28 * U + h + h2 + 6, w)
    h4 = note(d, "Iteration 1 runs from 5 V on the pogo pads with no battery: J4 is not fitted, R17 (10 kOhm) is fitted, "
                 "firmware disables the NTC function (BCHGDISABLESET) and never enables the charger (no battery gives "
                 "repeated charger events). When a pack with NTC goes on J4 pin 2, remove R17. The pack must carry its "
                 "own protection (over/under voltage, over current). Thermistor type is chosen in software (10, 47 or 100 kOhm).",
              nx, 28 * U + h + h2 + h3 + 9, w)
    h5 = note(d, "SW1 on SHPHLD exits Ship mode (a charger on VBUS also does) and a 10 s hold resets the system. TWI "
                 "address is 0x6B. VDDIO is the 1.8 V rail and has its own 100 nF (C31). GPIO1 is the interrupt line "
                 "PMIC_IRQ; the other GPIOs, LED0..2 and SW2 are open. The I2C pull-ups are on the sensors sheet.",
              nx, 28 * U + h + h2 + h3 + h4 + 12, w)
    h6 = note(d, "DECIDED (rail voltage): the nRF54L15 needs VDD of at least 1.75 V during power-on reset, and 47 kOhm on "
                 "VSET1 would give 1.8 V +/-5 %, which is 1.71 V at worst. 68 kOhm gives 2.0 V +/-5 % (1.9 to 2.1 V), "
                 "inside the nRF54L15 limit and under the MAX86141 absolute maximum of 2.2 V. Firmware lowers the rail to "
                 "1.9 V (BUCK1NORMVOUT) before the MAX86141 is used, which keeps it inside its 1.7 to 2.0 V operating range. "
                 "Net name stays +1V8.",
              nx, 28 * U + h + h2 + h3 + h4 + h5 + 15, w)
    note(d, "Open items: battery cell and connector pin order (J4), button part (SW1), QFN32 exposed pad size (footprint "
            "EP 3.45 mm, datasheet 3.5 mm nominal).", nx, 28 * U + h + h2 + h3 + h4 + h5 + h6 + 18, w)
