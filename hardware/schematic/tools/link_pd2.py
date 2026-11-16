"""Join the same-net pads of photodiode PD2 (VEMD8080) with short straight tracks (KiCad 9 python).

Pads 1-4 (top row), 6-8 (bottom row) are all PD2_IN; pad 5 is the other photodiode's net.
Top row is joined left to right, bottom row 7-6 (8-7 would cross the TEMP_INT track), (the rows stay two groups: the PD1 anode track runs between them),
so route_v2.py only has to bring one track from U2.D4 to this group.

Done by Harsh Thakur.
"""
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.normpath(os.path.join(HERE, "..", "smartwatch.kicad_pcb"))
board = pcbnew.LoadBoard(BOARD)
mm = pcbnew.FromMM
W = 0.15
pd = [f for f in board.GetFootprints() if f.GetReference() == "PD2"][0]
pads = {p.GetNumber(): p for p in pd.Pads()}
layer = pcbnew.B_Cu if pd.IsFlipped() else pcbnew.F_Cu
for a, b in (("1", "2"), ("2", "3"), ("3", "4"), ("7", "6")):
    assert pads[a].GetNetname() == pads[b].GetNetname(), (a, b)
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pads[a].GetPosition())
    t.SetEnd(pads[b].GetPosition())
    t.SetWidth(mm(W))
    t.SetLayer(layer)
    t.SetNet(pads[a].GetNet())
    t.SetLocked(True)
    board.Add(t)
pcbnew.SaveBoard(BOARD, board, True)
print("PD2 pads linked", flush=True)
os._exit(0)
