#!/usr/bin/env python3
"""
print_test.py
=============
Standalone printer test for the Vote Center ticket project. It is SEPARATE
from the running app, but shares the SAME ticket generation and printing code
(printer.py) -- so whatever you validate here is exactly what the app prints.

Use it to prove a ticket can be printed automatically (silently -- no dialog)
to a Windows printer, and to find the exact printer name for config.py.

Examples (run on the Windows station):
  python print_test.py --list
  python print_test.py --printer "DYMO LabelWriter 550" --number 0042
  python print_test.py --image barcode_sample.png --printer "DYMO LabelWriter 550"
  python print_test.py --save-image ticket_preview.png         (no printer; preview only)

Notes:
  * A DYMO validates the *silent image print path* the app uses. It does not
    test ESC/POS, receipt roll, or auto-cutter -- those are receipt-printer
    specifics confirmed after procurement.
  * "Microsoft Print to PDF" proves the code path but asks where to save the
    file, so it is not fully silent. A real printer prints with no prompt.
"""

import argparse
import sys

import printer   # shared generation + printing


def main():
    ap = argparse.ArgumentParser(description="Standalone ticket printer test.")
    ap.add_argument("--list", action="store_true",
                    help="List installed printers and exit.")
    ap.add_argument("--printer",
                    help="Target printer name (default: system default printer).")
    ap.add_argument("--image",
                    help="Print this image file instead of a generated ticket.")
    ap.add_argument("--number", default="0042",
                    help="Number on the generated ticket (default 0042).")
    ap.add_argument("--width", type=int, default=printer.DEFAULT_WIDTH,
                    help="Ticket width in dots (default 576 ~ 80mm at 203 dpi).")
    ap.add_argument("--no-barcode", action="store_true",
                    help="Do not draw a barcode on the generated ticket.")
    ap.add_argument("--copies", type=int, default=1,
                    help="Number of copies (default 1).")
    ap.add_argument("--save-image", metavar="PATH",
                    help="Render the ticket to a file and exit (no printing). "
                         "Works on any OS.")
    args = ap.parse_args()

    try:
        if args.list:
            names, default = printer.list_printers()
            print("Installed printers:")
            for name in names:
                print("  - {}{}".format(name, "   (default)" if name == default else ""))
            return

        # The source is either an existing image or a freshly generated ticket.
        if args.image:
            source = args.image
        else:
            source = printer.generate_ticket_image(
                args.number, width=args.width, with_barcode=not args.no_barcode,
            )

        if args.save_image:
            if args.image:
                img = printer._pillow()[0].open(args.image)
            else:
                img = source
            img.save(args.save_image)
            print("Saved ticket preview to {} (no printing).".format(args.save_image))
            return

        used = printer.print_image(source, printer_name=args.printer,
                                   copies=args.copies, doc_name="Queue Ticket Test")
        print("Sent ticket to printer: {}".format(used))
        print("If nothing prints, check the printer is online and has media loaded.")

    except printer.PrinterError as exc:
        print("ERROR: {}".format(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
