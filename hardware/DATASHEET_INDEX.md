# Datasheet index

Done by Harsh Thakur.

PDFs sit in `hardware/datasheets/` on the working PC and are **not committed** (vendor copyright, and the repo is public). This index records exactly which revision was used, so anyone can fetch the same document.

| Part | Role | Document | Revision / date | Pages | Source |
|---|---|---|---|---|---|
| Nordic nRF54L15 (QFN48, QFAA) | Processor, Bluetooth | Datasheet 4503_018 | v1.0 | 940 | Nordic docs site |
| Nordic nRF54L15 | | Errata 4503_489 | v1.1, 2026-05-12 | 27 | Nordic docs site |
| ADI MAX86141 (WLP20) | Optical front end | Datasheet 19-100051 | **Rev 5, 7/23** | 90 | analog.com |
| ams OSRAM SFH 7016 | Green / red / IR emitter | Datasheet | Version 1.5, 2022-04-12 | 23 | look.ams-osram.com |
| Vishay VEMD8080 | Photodiode (x2) | Datasheet 84565 | Rev 1.1, 2023-09-05 | 7 | vishay.com |
| Bosch BMI270 | Motion sensor | Datasheet BST-BMI270-DS000 | Rev 08 | 150 | bosch-sensortec.com |
| ADI MAX30208 (thin LGA10) | Skin temperature | Datasheet 19-100550 | Rev 1, 5/20 | 29 | analog.com |
| ADI MAX30208 | | Package outline 21-100265 | n/a | | analog.com |
| ADI MAX30208 | | PCN 2204 | n/a | | analog.com (read before ordering) |
| TI TPS61240 (WSON-6 DRV) | 5 V LED boost | Datasheet SLVS806D | Dec 2015 | 35 | ti.com |
| ST OCVPB21-13F6 (WLCSP13) | Charging-input protection | Datasheet DS13107 | Rev 3, Dec 2024 | 17 | st.com |
| Johanson 2450AT18A0100001E | 2.4 GHz chip antenna | Datasheet 36S0021A | Rev 4.0, 2024 | 6 | johansontechnology.com |

## Reference material

| Item | What | Revision |
|---|---|---|
| MAXREFDES103# design files | Sensor board schematic, BOM, layout, Allegro board, ODB++ | schematic dated 2019-09-03, rev P3 |
| UG-7145 | MAXREFDES103 user guide | 45 pages |
| UG-6780 | MAXREFDES101 user guide | 39 pages |
| Nordic KiCad block `nRF54L15-QFXX_Reference_Design` | Community-made KiCad version of Nordic's QFN48 reference circuit (CERN-OHL-P). Used only to cross-check values against the datasheet figure. | github.com/hlord2000/nordic-lib-kicad |

## Missing, needed before the power and memory sheets

| Part | Why it is missing | What to do |
|---|---|---|
| Nordic nPM1300 product specification (latest is v1.3, Oct 2026) | Nordic's site redirects every PDF link to its web reader. The PDF could not be saved automatically. | Save the PDF from docs.nordicsemi.com (nPM1300 Product Specification, v1.3) into `hardware/datasheets/nPM1300_PS_v1.3.pdf` |
| Macronix MX25R3235F datasheet | Macronix's datasheet link is built by a script on their page; distributor pages are bot-protected. | Save the PDF from macronix.com into `hardware/datasheets/MX25R3235F.pdf` |
| Passive component datasheets (capacitor, resistor, inductor, ferrite, NTC series) | Not yet chosen to a single MPN per value. | Next step in `TASKS.md` B5 |
| Battery cell, battery connector, NTC | Cell not chosen (150-250 mAh pouch with protection board) | Client decision, see open items |
