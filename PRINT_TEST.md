# Printer Test — de-risk silent printing before buying the receipt printer

`print_test.py` is a standalone tool (separate from the app). It proves the
station can print a ticket **automatically and silently** to a Windows printer.
Run it against any printer you already have — a **DYMO LabelWriter**, an
ordinary inkjet/laser, or the built-in **Microsoft Print to PDF**.

## Why this works with a DYMO (or anything)

The risky part isn't the specific printer — it's **silent printing from code to
a Windows printer** (the ticket prints with no dialog). That path is the same
regardless of hardware, so a Dymo validates it.

- **A Dymo proves:** it installs as a normal Windows printer and prints a
  rendered ticket *image* silently — exactly the path the app will use to print
  the Airtable "Barcode Image."
- **A Dymo does not prove:** 80 mm receipt roll, auto-cutter, or ESC/POS. Those
  are receipt-printer specifics. The planned approach prints an image, so the
  Dymo covers the path you'll actually use.

## Setup (on the Windows station)

```
pip install -r requirements-printtest.txt
```

## Steps

1. **Find the exact printer name:**
   ```
   python print_test.py --list
   ```

2. **Silently print a generated ticket** (swap in your printer's name):
   ```
   python print_test.py --printer "DYMO LabelWriter 550" --number 0042
   ```

3. **Print the real Airtable sample image** (tests your actual ticket art):
   ```
   python print_test.py --image barcode_sample.png --printer "DYMO LabelWriter 550"
   ```

4. **Preview with no printer at all** (works on any computer):
   ```
   python print_test.py --save-image preview.png
   ```

Other flags: `--copies N`, `--width DOTS` (default 576 ≈ 80 mm @ 203 dpi),
`--no-barcode`.

## Pass criteria (mirrors the proposal's "Printer driver and image test")

- The ticket prints with **no print dialog** (fully automatic).
- The number is large and readable; the barcode scans.
- Output is clean (no clipping; the layout fits the media).

> Note: **Microsoft Print to PDF** is a good zero-hardware dry run, but its
> driver asks where to save the file, so it is not *fully* silent. A real
> printer (Dymo, inkjet, or the eventual Bixolon) prints with no prompt.

## How this maps into the app later

When a printer is chosen, the print step slots into the app at the
`ENABLE_PRINTING` flag. The order stays **fail-closed**: print the ticket
first, and only mark `Ticket Printed` in Airtable if the print job succeeds —
so a voter is never counted as "in line" for a ticket that never printed.
