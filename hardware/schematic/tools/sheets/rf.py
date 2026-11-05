"""RF: Nordic filter-match network, antenna tee slots and the Johanson chip antenna. A4, one row, left to right."""
from .common import U, P, part, note

RFN = "nRF54L15 DS v1.0 Fig 180 / Table 87"
JOH = "Johanson DS 36S0021A note 4"


def draw(d):
    d.head("RF  -  Nordic match network, antenna tee, chip antenna", 12 * U, 16 * U)
    d.sub("The signal runs left to right: ANT pin of the processor, series-shunt-series filter, tee slots, antenna.",
          12 * U, 19.5 * U)
    ry = 52 * U
    d.frame(*P(12, 23), *P(100, 70), heading="NORDIC FILTER AND MATCH")
    d.frame(*P(102, 23), *P(222, 70), heading="ANTENNA TEE AND ANTENNA")

    d.port("RF_ANT", 20 * U, ry, "L", "bidirectional")
    l2 = part(d, "L", "L2", "2.7nH", "0201", 32, 52, "0.1 nH 600 mA", RFN, rot=90, mpn="LQP03HQ2N7B02")
    d.w((20 * U, ry), l2.p(1))
    # shunt 1: C6 to VSS_PA (top layer only)
    c6 = part(d, "C", "C6", "1.5pF", "0201", 42, 54, "NP0 0.05 pF 25V high Q", RFN, mpn="GJM0335C1E1R5WB01")
    d.w(l2.p(2), (50 * U, ry))
    d.w((42 * U, ry), c6.p(1))
    d.w(c6.p(2), (42 * U, 61 * U))
    d.port("VSS_PA", 42 * U, 61 * U, "R", "bidirectional")
    l3 = part(d, "L", "L3", "3.5nH", "0201", 54, 52, "0.1 nH 500 mA", RFN, rot=90, mpn="LQP03HQ3N5B02")
    d.w((50 * U, ry), l3.p(1))
    # shunt 2: C9 to the bottom ground only, through net tie NT2
    c9 = part(d, "C", "C9", "2.0pF", "0201", 66, 54, "NP0 0.05 pF 25V", RFN, mpn="GJM0335C1E2R0WB01", tside="L")
    d.w(l3.p(2), (74 * U, ry))
    d.w((66 * U, ry), c9.p(1))
    nt = d.put("Device:NetTie_2", 66 * U, 59 * U, 90, ref="NT2", value="NetTie", footprint="NetTie:NetTie-2_SMD_Pad0.5mm",
               props={"Source": RFN + " note on C9"}, prefix="NT")
    top, bot = (nt.p(1), nt.p(2)) if nt.p(1)[1] < nt.p(2)[1] else (nt.p(2), nt.p(1))
    d.w(c9.p(2), top)
    d.gnd(*bot)
    d.caption("BOTTOM GND ONLY", 56 * U, 68 * U, size=1.27)
    l4 = part(d, "L", "L4", "3.5nH", "0201", 78, 52, "0.1 nH 500 mA", RFN, rot=90, mpn="LQP03HQ3N5B02")
    d.w((74 * U, ry), l4.p(1))
    # shunt 3: C11 to ground
    c11 = part(d, "C", "C11", "0.3pF", "0201", 90, 54, "C0G 0.1 pF 50V", RFN)
    d.w(l4.p(2), (96 * U, ry))
    d.w((90 * U, ry), c11.p(1))
    d.gnd(*c11.p(2))

    # tee slots: series 0R, shunt (not fitted), series 0R, then the antenna
    r2 = part(d, "R", "R2", "0R", "0402", 112, 52, "series slot", JOH, rot=90)
    d.w((96 * U, ry), r2.p(1))
    c14 = part(d, "C", "C14", "TBD", "0402", 124, 54, "shunt slot, tune on worn band", JOH, dnp=True)
    d.w(r2.p(2), (136 * U, ry))
    d.w((124 * U, ry), c14.p(1))
    d.gnd(*c14.p(2))
    r3 = part(d, "R", "R3", "0R", "0402", 140, 52, "series slot", JOH, rot=90)
    d.w((136 * U, ry), r3.p(1))
    ae = d.put("smartwatch:Chip_Antenna_2450AT18A", 180 * U, ry, 0, ref="AE1", value="2450AT18A0100001E",
               footprint="smartwatch:Johanson_2450AT18A0100001E_1206", props={"Source": "Johanson DS 36S0021A rev 4.0"}, prefix="AE", ctext="TL")
    d.w(r3.p(2), ae.p(1))
    d.nc(*ae.p(2))

    nx = 14 * U
    h = note(d, "Nordic network: C6 returns to VSS_PA on the TOP layer only. C9 returns to the BOTTOM ground layer only "
                "(net tie NT2). Place the whole network as close to the ANT pin as possible. (nRF54L15 datasheet, Fig 180 "
                "and Table 87)", nx, 76 * U, 100)
    note(d, "Antenna tee: 0R, empty, 0R as a start (R2, C14, R3). The antenna is the Johanson 2450AT18A0100001E in a corner "
            "with its keep-out. Tune on the worn band with the final housing. Pin 2 is only a solder anchor. Johanson's own "
            "evaluation board uses series 1.0 pF, shunt 2.7 nH, series 3.9 nH: the shunt slot may need an inductor, so "
            "the 0402 slot C14 is a generic shunt element.",
         nx + 104 * U, 76 * U, 100)
