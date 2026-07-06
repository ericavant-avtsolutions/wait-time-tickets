"""
app.py
======
Vote Center Ticket Station -- Version 1

A small local web app. It shows one large "Print Next Ticket" button on a
kiosk screen. Pressing it:
  1. Asks Airtable for the next available (lowest, unprinted) ticket number.
  2. Marks that ticket printed in Airtable (Airtable stamps the time, which
     starts the wait-time clock).
  3. Shows the voter their confirmed number, large, on screen.

Version 1 does NOT print anything -- there is no printer connected yet. The
on-screen number is the confirmation. Printing is added in a later version
(see config.ENABLE_PRINTING).

The Airtable API token is kept server-side and is never sent to the browser,
per the security requirements in the project proposal.

Run:  python app.py
Then open http://127.0.0.1:5000 in full-screen on the station.
"""

import logging
import os
import sys

from flask import Flask, render_template, jsonify

import config
import airtable_client as at
import printer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)

app = Flask(__name__)


def _ui_config():
    """The subset of config the screen needs. Passed to the page as JSON."""
    return {
        "stationName": config.STATION_NAME,
        "buttonLabel": config.BUTTON_LABEL,
        "workingLabel": config.WORKING_LABEL,
        "confirmEyebrow": config.CONFIRM_EYEBROW,
        "confirmSubtext": config.CONFIRM_SUBTEXT,
        "doneLabel": config.DONE_LABEL,
        "noTicketsTitle": config.NO_TICKETS_TITLE,
        "noTicketsText": config.NO_TICKETS_TEXT,
        "offlineTitle": config.OFFLINE_TITLE,
        "offlineText": config.OFFLINE_TEXT,
        "footnote": config.FOOTNOTE,
        "confirmDisplaySeconds": config.CONFIRM_DISPLAY_SECONDS,
        "healthPollSeconds": config.HEALTH_POLL_SECONDS,
        "triggerKeys": config.TRIGGER_KEYS,
        "printingEnabled": config.ENABLE_PRINTING,
    }


@app.route("/")
def index():
    """Serve the kiosk page, passing the display config through to the UI."""
    return render_template("index.html", ui=_ui_config())


@app.route("/api/print-ticket", methods=["POST"])
def print_ticket():
    """
    Issue the next ticket. Returns JSON:
      200  {"ok": true,  "barcode_value": "...", "position_text": "..."}
      409  {"ok": false, "reason": "no_tickets",     "message": "..."}
      503  {"ok": false, "reason": "offline"|"not_configured", "message": "..."}
    """
    try:
        before_mark = printer.print_ticket if config.ENABLE_PRINTING else None
        ticket = at.claim_next_ticket(before_mark=before_mark)
        app.logger.info(
            "Issued ticket %s (record %s)%s",
            ticket["barcode_value"], ticket["record_id"],
            " [printed]" if config.ENABLE_PRINTING else "",
        )
        return jsonify({
            "ok": True,
            "barcode_value": ticket["barcode_value"],
            "position_text": ticket["position_text"],
            "record_id": ticket["record_id"],
        })
    except at.NoTicketsAvailable:
        app.logger.warning("Print requested but no tickets remain.")
        return jsonify({
            "ok": False,
            "reason": "no_tickets",
            "message": config.NO_TICKETS_TEXT,
        }), 409
    except printer.PrinterError as exc:
        # Fail-closed: the ticket was NOT marked printed, so the number is free
        # to be issued again once the printer is fixed.
        app.logger.error("Printer error while issuing ticket: %s", exc)
        return jsonify({
            "ok": False,
            "reason": "printer_error",
            "message": config.OFFLINE_TEXT,
        }), 503
    except at.TokenNotConfigured as exc:
        app.logger.error("Airtable token not configured: %s", exc)
        return jsonify({
            "ok": False,
            "reason": "not_configured",
            "message": config.OFFLINE_TEXT,
        }), 503
    except at.AirtableError as exc:
        app.logger.error("Airtable error while issuing ticket: %s", exc)
        return jsonify({
            "ok": False,
            "reason": "offline",
            "message": config.OFFLINE_TEXT,
        }), 503


@app.route("/api/health")
def health():
    """Best-effort status for staff/monitoring. Never modifies data."""
    return jsonify(at.check_health())


def _check_project_structure():
    """Fail fast with a clear message if the folder layout is broken -- e.g.
    the templates/ or static/ folders got separated from app.py (a common
    result of downloading the files individually instead of as a folder)."""
    here = os.path.dirname(os.path.abspath(__file__))
    required = ("templates/index.html", "static/style.css", "static/app.js")
    missing = [p for p in required if not os.path.exists(os.path.join(here, p))]
    if missing:
        print("\n  ERROR -- these files are not where they belong:")
        for p in missing:
            print("      " + p.replace("/", os.sep))
        print("\n  app.py must sit next to its 'templates' and 'static' folders:")
        print("      app.py")
        print("      templates" + os.sep + "index.html")
        print("      static" + os.sep + "style.css")
        print("      static" + os.sep + "app.js")
        print("\n  Re-extract the project ZIP so the folder structure is kept,")
        print("  then run 'python app.py' from inside that folder.\n")
        sys.exit(1)


def _printer_preflight():
    """If printing is enabled, confirm the configured printer actually exists
    and say so at startup -- so a wrong name, an offline printer, or missing
    printing libraries is obvious immediately instead of silently not printing."""
    if not config.ENABLE_PRINTING:
        return
    try:
        names, default = printer.list_printers()
    except printer.PrinterError as exc:
        print("  Printer:   WARNING -- cannot check printers: "
              + str(exc).splitlines()[0])
        print("             Install printing libs: "
              "pip install -r requirements-printtest.txt\n")
        return
    if config.PRINTER_NAME and config.PRINTER_NAME not in names:
        print("  Printer:   WARNING -- '{}' not found.".format(config.PRINTER_NAME))
        print("             Installed: {}".format(", ".join(names) or "(none)"))
        print("             Fix PRINTER_NAME in config.py "
              "(see: python print_test.py --list)\n")
    else:
        print("  Printer:   OK -- {}\n".format(config.PRINTER_NAME or default))


if __name__ == "__main__":
    _check_project_structure()
    print(
        "\n"
        "  Vote Center Ticket Station -- Version 1\n"
        f"  Open:      http://{config.HOST}:{config.PORT}\n"
        f"  Base:      {config.AIRTABLE_BASE_ID}   Table: {config.AIRTABLE_TABLE_NAME}\n"
        f"  Printing:  {('ENABLED -> ' + (config.PRINTER_NAME or 'system default')) if config.ENABLE_PRINTING else 'disabled'}\n"
        f"  Token set: {'yes' if config.AIRTABLE_TOKEN else 'NO -- set AIRTABLE_TOKEN in .env'}\n"
    )
    _printer_preflight()
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
