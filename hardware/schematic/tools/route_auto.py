"""Autoroute the rest of the board with Freerouting (run with KiCad 9's python).

Usage:  python route_auto.py [passes]

1. Adds a board-wide "no tracks" rule area on In1.Cu (keeps the L2 ground plane solid; vias
   still pass through).
2. Exports a Specctra DSN. The tracks and vias that route_critical.py made are locked, so
   Freerouting keeps them as fixed.
3. Runs Freerouting (Java 25 + the jar in ~/.kicad-mcp), imports the session back and
   saves with SaveBoard(..., True) so smartwatch.kicad_pro (JLCPCB rules) is not changed.

Done by Harsh Thakur.
"""
import os
import subprocess
import sys
import tempfile

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.normpath(os.path.join(HERE, "..", "smartwatch.kicad_pcb"))
JAVA = r"C:\Users\TempAdmin\tools\jre25\bin\java.exe"
JAR = r"C:\Users\TempAdmin\.kicad-mcp\freerouting.jar"
passes = sys.argv[1] if len(sys.argv) > 1 else "40"

board = pcbnew.LoadBoard(BOARD)


def add_in1_keepout(layer=pcbnew.In1_Cu, name="IN1_NO_TRACKS"):
    for z in board.Zones():
        if z.GetZoneName() == name:
            return
    bb = board.GetBoardEdgesBoundingBox()
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    z.SetLayer(layer)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowCopperPour(False)
    z.SetDoNotAllowFootprints(False)
    ol = pcbnew.SHAPE_LINE_CHAIN()
    for p in ((bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()),
              (bb.GetRight(), bb.GetBottom()), (bb.GetLeft(), bb.GetBottom())):
        ol.Append(pcbnew.VECTOR2I(*p))
    ol.SetClosed(True)
    z.Outline().AddOutline(ol)
    board.Add(z)


add_in1_keepout()
add_in1_keepout(pcbnew.In2_Cu, "IN2_NO_TRACKS")     # In2 is the +1V8 plane: no tracks there either
for t in board.GetTracks():                         # pre-routed copper stays exactly where it is
    t.SetLocked(True)
work = tempfile.mkdtemp()
dsn = os.path.join(work, "board.dsn")
ses = os.path.join(work, "board.ses")
assert pcbnew.ExportSpecctraDSN(board, dsn), "DSN export failed"
# KiCad exports a 0.025 mm smd-to-smd clearance, which let Freerouting squeeze tracks of
# 0.06-0.075 mm between pins (below JLCPCB's 0.09 mm). Use the real 0.1 mm clearance.
txt = open(dsn, encoding="utf-8").read()
txt = txt.replace("(clearance 25 (type smd_smd))", "(clearance 100 (type smd_smd))")
open(dsn, "w", encoding="utf-8").write(txt)
print("dsn:", dsn)
cmd = [JAVA, "-jar", JAR, "-de", dsn, "-do", ses, "-mp", passes, "-mt", "6"]
print(" ".join(cmd))
subprocess.run(cmd, check=False)
assert os.path.exists(ses), "Freerouting produced no session file"
assert pcbnew.ImportSpecctraSES(board, ses), "SES import failed"
pcbnew.SaveBoard(BOARD, board, True)
print("saved", BOARD)
