"""Copper planes for the 4-layer stack (run with KiCad 9's python).

  In1.Cu (L2): solid GND over the whole board (nothing inside the antenna keep-out)
  In2.Cu (L3): routing layer (signals); a +1V8 pour is added there after routing

Freerouting reads these as planes and drops vias from pads to them.
Saves with SaveBoard(..., True) so smartwatch.kicad_pro (JLCPCB rules) is not changed.

Done by Harsh Thakur.
"""
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.normpath(os.path.join(HERE, "..", "smartwatch.kicad_pcb"))
board = pcbnew.LoadBoard(BOARD)
mm = pcbnew.FromMM


def add_plane(name, net, layer, inset=0.25):
    for z in board.Zones():
        if z.GetZoneName() == name:
            board.Remove(z)
    bb = board.GetBoardEdgesBoundingBox()
    l, t, r, b = bb.GetLeft() + mm(inset), bb.GetTop() + mm(inset), bb.GetRight() - mm(inset), bb.GetBottom() - mm(inset)
    z = pcbnew.ZONE(board)
    z.SetZoneName(name)
    z.SetLayer(layer)
    z.SetNet(board.FindNet(net))
    z.SetLocalClearance(mm(0.2))
    z.SetMinThickness(mm(0.15))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetAssignedPriority(1)
    ol = pcbnew.SHAPE_LINE_CHAIN()
    for p in ((l, t), (r, t), (r, b), (l, b)):
        ol.Append(pcbnew.VECTOR2I(*p))
    ol.SetClosed(True)
    z.Outline().AddOutline(ol)
    board.Add(z)


add_plane("GND_L2", "GND", pcbnew.In1_Cu)
if "--v18" in __import__("sys").argv:       # +1V8 plane on In2 (blocks In2 routing; off by default)
    add_plane("V18_L3", "+1V8", pcbnew.In2_Cu)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(BOARD, board, True)
print("zones:", [z.GetZoneName() for z in board.Zones()])
