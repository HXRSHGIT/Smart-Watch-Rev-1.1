# Reference library - Smart Watch Rev 1.1

Local store for everything the schematic work was checked against, so nothing has to be searched for or downloaded twice.
This branch has no shared history with `main`. It holds files only; the design itself lives on `main`.

| Folder / file | What is in it |
|---|---|
| `datasheets/` | Vendor datasheets (PDF + extracted text) for every final part: nRF54L15 (datasheet v1.0, errata v1.1), nPM1300 (product spec v1.3, text only), MAX86141 rev 5, MAX30208, BMI270, TPS61240, OCVPB21-13F6, MX25R3235F rev 1.6, Johanson 2450AT18A100, SFH 7016, VEMD8080 |
| `reference-designs/` | MAXREFDES103 design files (zip is the complete set; the extracted copy leaves out six 3D STEP files, 0.03 to 113 MB each), MAXREFDES101 and MAXREFDES103 user guides, nRF54L15 QFN48 pin table |
| `checks/` | Results the design is checked against: KiCad ERC (`erc.json`), netlist (`smartwatch.xml`), 10-page PDF, and a snapshot of `check.py`, `lint.py`, `build.py`, `pinmap.py` |
| `REVIEW.md`, `DATASHEET_INDEX.md`, `REFERENCE_DESIGNS.md`, `REQUIREMENTS_FROM_DATASHEETS.md` | Snapshot of the review notes and the source/revision list |
| `SHA256SUMS.txt` | Checksum of every stored file (`sha256sum -c SHA256SUMS.txt`) |

Checks snapshot belongs to `main` commit `7f6c825`. The live scripts stay in `hardware/schematic/tools/` on `main`; the copies here are for the record.

## Use it

```
git worktree add ../Smart-Watch-Rev-1.1-reference reference-library   # check out beside the main folder
# or, to place it inside the working tree of main (ignored there):
git worktree add hardware/reference-library reference-library
```

Add a new datasheet: copy it into `datasheets/`, add its source and revision to `DATASHEET_INDEX.md`, regenerate `SHA256SUMS.txt`, commit.

## Licensing

Datasheets and reference designs belong to their vendors (Nordic, Analog Devices, Bosch, Texas Instruments, Macronix, ams OSRAM, Vishay, Johanson, onsemi/ST) and stay under their own terms. They are stored here for engineering reference only; the repository licence does not cover them.
