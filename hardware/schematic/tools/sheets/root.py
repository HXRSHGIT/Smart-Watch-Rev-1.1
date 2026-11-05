"""Top level: sheet blocks wired to each other in signal-flow order. A3. All nine sheets are on this page."""
from .common import U, P, note

MY = 36           # top of the processor block, grid units
# processor block pins: slot number -> net. Right-hand slots line up with the pin of the target block, so the wires run straight.
MCU_LEFT = {0: "CHG_FLAG", 8: "LED_BOOST_EN", 15: "SWDIO", 16: "SWDCLK", 17: "NRESET", 18: "SWO"}
MCU_RIGHT = {0: "PPG_INT", 1: "PPG_GPIO1", 2: "PPG_GPIO2", 3: "CS_PPG", 4: "SPI_SCK", 5: "SPI_MOSI", 6: "SPI_MISO",
             10: "CS_FLASH", 17: "PMIC_IRQ", 23: "I2C_SDA", 24: "I2C_SCL", 25: "IMU_INT1", 26: "IMU_INT2", 27: "TEMP_INT",
             31: "RF_ANT", 32: "VSS_PA"}
LX, MX, RX, BW = 24, 104, 186, 44        # block x positions and widths, grid units


def slots(d_, n):
    return [d_.get(i) for i in range(n)]


def block(d, name, x, y, w, left, right, ids):
    h = 2 * (max(len(left), len(right)) + 1)
    return d.sheet_block(name, f"{name}.kicad_sch", x * U, y * U, w * U, h * U, left, right, ids["pages"][name], ids["uuid"][name],
                         labels=False)


def draw(d, ids):
    d.head("HEALTHOS BAND REV 1.1  -  main board, top level", 12 * U, 16 * U)
    d.sub("Signals flow left to right between sheets. Supply rails (VBUS_PROT, VSYS, 1.8 V, VLED, ground) are power symbols "
          "inside the sheets and need no wire here.", 12 * U, 19.5 * U)
    mcu = block(d, "mcu", MX, MY, BW, slots(MCU_LEFT, 19), slots(MCU_RIGHT, 33), ids)
    # left column: inputs and test access
    ip = block(d, "input_protection", LX, MY, BW, [], ["CHG_FLAG"], ids)
    ls = block(d, "led_supply", LX, MY + 16, BW, [], ["LED_BOOST_EN"], ids)
    te = block(d, "test", LX, MY + 30, BW, [], ["SWDIO", "SWDCLK", "NRESET", "SWO"], ids)
    # right column, top to bottom, each block level with its first processor pin
    op = block(d, "optical", RX, MY, BW, ["PPG_INT", "PPG_GPIO1", "PPG_GPIO2", "CS_PPG", "SPI_SCK", "SPI_MOSI", "SPI_MISO"], [], ids)
    me = block(d, "memory", RX, MY + 20, BW, ["CS_FLASH", "SPI_SCK", "SPI_MOSI", "SPI_MISO"], [], ids)
    pw = block(d, "power", RX, MY + 34, BW, ["PMIC_IRQ", "I2C_SDA", "I2C_SCL"], [], ids)
    se = block(d, "sensors", RX, MY + 46, BW, ["I2C_SDA", "I2C_SCL", "IMU_INT1", "IMU_INT2", "TEMP_INT"], [], ids)
    rf = block(d, "rf", RX, MY + 62, BW, ["RF_ANT", "VSS_PA"], [], ids)

    # left column into the processor
    d.w(ip["CHG_FLAG"], mcu["CHG_FLAG"])
    d.w(ls["LED_BOOST_EN"], mcu["LED_BOOST_EN"])
    for n in ("SWDIO", "SWDCLK", "NRESET", "SWO"):
        d.w(te[n], mcu[n])
    # processor into the right column: one straight wire per signal
    for n in MCU_RIGHT.values():
        tgt = {**me, **pw, **op, **se, **rf}[n]     # a bus goes straight to its first receiver
        d.w(mcu[n], tgt)
    # second receivers of a bus: SPI also goes to the memory sheet, I2C also to the power sheet. A wire cannot reach them
    # without crossing the others, so the bus name is written at the pin (label), and again at the processor wire.
    for n in ("SPI_SCK", "SPI_MOSI", "SPI_MISO"):
        x, y = mcu[n]
        d.label_net(n, x + 6 * U, y, 0)
        tx, ty = me[n]
        d.w((tx, ty), (tx - 4 * U, ty))
        d.label_net(n, tx - 4 * U, ty, 180)
    for n in ("I2C_SDA", "I2C_SCL"):
        x, y = mcu[n]
        d.label_net(n, x + 6 * U, y, 0)
        tx, ty = pw[n]
        d.w((tx, ty), (tx - 4 * U, ty))
        d.label_net(n, tx - 4 * U, ty, 180)

    nx = 236 * U
    h = note(d, "How to read this page: each box is one sheet. A wire between two boxes is a signal that crosses sheets. "
                "SPI_SCK, SPI_MOSI and SPI_MISO serve the optical sheet and the memory sheet; I2C_SDA and I2C_SCL serve the "
                "sensors sheet and the power sheet. The second receiver of each of these five nets is joined by name "
                "(label) because a wire would cross other signals.", nx, 28 * U, 80)
    note(d, "Power: the charger input (VBUS_PROT) from the charging input sheet, the battery, VSYS and the 1.8 V rail are "
            "power symbols, so they connect by name across sheets and do not appear as wires here. The nPM1300 on the power "
            "sheet makes VSYS and the 1.8 V rail.", nx, 28 * U + h + 3, 80)
