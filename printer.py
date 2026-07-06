"""
printer.py
==========
Ticket generation + silent printing, shared by the app (app.py) and the
standalone tester (print_test.py). Because both use this one module, the
ticket that prints in production is the exact same layout you validated with
the print test.

Printing uses the Windows GDI path (pywin32) and needs the libraries in
requirements-printtest.txt. Those imports are done lazily inside the functions
so this module still imports on any OS and when printing is disabled -- and so
that a missing library fails closed with a clear message instead of a crash.
"""

import config


class PrinterError(Exception):
    """Ticket generation or printing failed (caller should fail closed)."""


# ~80mm at 203 dpi -- a typical thermal receipt width, in printer dots.
DEFAULT_WIDTH = 576


# ---------------------------------------------------------------------------
# Lazy imports (kept out of module top level on purpose -- see docstring)
# ---------------------------------------------------------------------------

def _pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageChops
        return Image, ImageDraw, ImageFont, ImageChops
    except ImportError as exc:
        raise PrinterError(
            "Pillow is required for printing. Install the printing libraries "
            "(already installed if you ran the print test):\n"
            "    pip install -r requirements-printtest.txt"
        ) from exc


def _win32():
    try:
        import win32print
        import win32ui
        import win32con
        from PIL import ImageWin
        return win32print, win32ui, win32con, ImageWin
    except ImportError as exc:
        raise PrinterError(
            "Silent printing requires Windows + pywin32. Install the printing "
            "libraries (already installed if you ran the print test):\n"
            "    pip install -r requirements-printtest.txt"
        ) from exc


# ---------------------------------------------------------------------------
# Ticket image generation (cross-platform -- no printer needed)
# ---------------------------------------------------------------------------

def _load_font(ImageFont, size, bold=True):
    candidates = []
    if bold:
        candidates += [
            "arialbd.ttf", "DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    candidates += [
        "arial.ttf", "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    try:
        return ImageFont.load_default(size=size)   # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


def _text_size(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _barcode_image(Image, value, target_width):
    """Code128 barcode as a PIL image, or None if python-barcode is absent."""
    try:
        import barcode
        from barcode.writer import ImageWriter
    except ImportError:
        return None
    code = barcode.get("code128", value, writer=ImageWriter())
    img = code.render(writer_options={
        "write_text": False,
        "module_height": 15.0,
        "quiet_zone": 2.0,
    }).convert("RGB")
    tw = int(target_width * 0.85)
    ratio = tw / img.width
    return img.resize((tw, max(1, int(img.height * ratio))))


def generate_ticket_image(number, width=DEFAULT_WIDTH, with_barcode=True):
    """Render a queue ticket (black ink on white) to a PIL image."""
    Image, ImageDraw, ImageFont, ImageChops = _pillow()

    number = str(number)
    canvas_h = 1200
    img = Image.new("RGB", (width, canvas_h), "white")
    draw = ImageDraw.Draw(img)

    margin = int(width * 0.06)
    y = margin

    f_small = _load_font(ImageFont, int(width * 0.055), bold=False)
    f_label = _load_font(ImageFont, int(width * 0.070), bold=True)
    f_number = _load_font(ImageFont, int(width * 0.34), bold=True)
    f_foot = _load_font(ImageFont, int(width * 0.045), bold=False)

    def centered(text, font, gap_after):
        nonlocal y
        tw, th = _text_size(draw, text, font)
        draw.text(((width - tw) // 2, y), text, fill="black", font=font)
        y += th + gap_after

    centered("VOTE CENTER", f_small, int(margin * 0.4))
    centered("YOUR PLACE IN LINE", f_label, int(margin * 0.6))

    tw, th = _text_size(draw, number, f_number)
    draw.text(((width - tw) // 2, y), number, fill="black", font=f_number)
    y += th + int(margin * 0.8)

    if with_barcode:
        bc = _barcode_image(Image, number, width)
        if bc is not None:
            img.paste(bc, ((width - bc.width) // 2, y))
            y += bc.height + int(margin * 0.3)

    centered("Position # " + number, f_small, int(margin * 0.5))
    centered("Keep this ticket \u2014 listen for your number", f_foot, margin)

    bbox = ImageChops.invert(img).getbbox()
    if bbox:
        img = img.crop((0, 0, width, min(canvas_h, bbox[3] + margin)))
    return img


# ---------------------------------------------------------------------------
# Windows printing (silent -- no dialog on a real printer)
# ---------------------------------------------------------------------------

def list_printers():
    """Return the list of installed printer names (Windows)."""
    win32print, _, _, _ = _win32()
    default = win32print.GetDefaultPrinter()
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    names = [info[2] for info in win32print.EnumPrinters(flags, None, 1)]
    return names, default


def print_image(image_or_path, printer_name=None, copies=1,
                doc_name="Queue Ticket"):
    """Silently print a PIL image (or image file path) to a Windows printer."""
    win32print, win32ui, win32con, ImageWin = _win32()
    Image = _pillow()[0]

    img = Image.open(image_or_path) if isinstance(image_or_path, str) else image_or_path
    img = img.convert("RGB")

    if not printer_name:
        printer_name = win32print.GetDefaultPrinter()

    hdc = win32ui.CreateDC()
    try:
        hdc.CreatePrinterDC(printer_name)
    except Exception as exc:
        raise PrinterError(
            "Could not open printer '{}'. Check the name with "
            "`python print_test.py --list`. ({})".format(printer_name, exc)
        ) from exc

    try:
        printable_w = hdc.GetDeviceCaps(win32con.HORZRES)
        ratio = printable_w / img.width
        draw_w = printable_w
        draw_h = int(img.height * ratio)

        hdc.StartDoc(doc_name)
        for _ in range(max(1, copies)):
            hdc.StartPage()
            ImageWin.Dib(img).draw(hdc.GetHandleOutput(), (0, 0, draw_w, draw_h))
            hdc.EndPage()
        hdc.EndDoc()
    except Exception as exc:
        raise PrinterError("Print job failed on '{}': {}".format(printer_name, exc)) from exc
    finally:
        hdc.DeleteDC()

    return printer_name


# ---------------------------------------------------------------------------
# High-level entry point used by the app
# ---------------------------------------------------------------------------

def print_ticket(barcode_value):
    """
    Generate a ticket for the given number and print it to the configured
    printer. Raises PrinterError on any failure so the caller can fail closed
    (i.e. NOT mark the ticket printed if it did not actually print).
    """
    img = generate_ticket_image(
        barcode_value,
        width=getattr(config, "TICKET_WIDTH_DOTS", DEFAULT_WIDTH),
        with_barcode=getattr(config, "PRINT_BARCODE", True),
    )
    print_image(
        img,
        printer_name=(getattr(config, "PRINTER_NAME", "") or None),
        copies=getattr(config, "PRINT_COPIES", 1),
        doc_name="Vote Center Queue Ticket " + str(barcode_value),
    )
