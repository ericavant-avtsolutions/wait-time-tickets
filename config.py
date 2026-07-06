"""
config.py
=========
Central configuration for the Vote Center Ticket Station (Version 1).

This is the ONE file you edit to change how the station behaves. Everything
tunable lives here: Airtable base/table/field names, ticket-selection
behavior, on-screen text, timing, and server settings.

The ONLY thing that does NOT live here is the secret Airtable API token. For
security, the token is read from an environment variable (or a local .env
file) so it is never committed to source control or shown in the browser.
See .env.example and the README for how to set it.
"""

import os

# Load a local .env file if present, so AIRTABLE_TOKEN can live there. This is
# optional; if python-dotenv is not installed we skip it and rely on a real
# environment variable instead. The .env is loaded from THIS file's folder, so
# the app finds the token no matter which directory you launch it from.
try:
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass


# ---------------------------------------------------------------------------
# 1. AIRTABLE CONNECTION
# ---------------------------------------------------------------------------
# The base and table that hold the pre-created queue tickets (0001-5000).
AIRTABLE_BASE_ID = "appUopMKWWjJNZNMa"

# The table is referenced by its stable Table ID, so renaming the table in
# Airtable will not break the app. The human-readable name is kept for
# reference only (not used in API calls).
AIRTABLE_TABLE_ID = "tblbo46VVEReXbG3I"
AIRTABLE_TABLE_NAME = "Barcode"

# Secret token -- DO NOT paste it here. Set it in a .env file or an environment
# variable named AIRTABLE_TOKEN. See .env.example.
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN", "")

# How long to wait for Airtable before giving up. If Airtable does not respond
# in this time, the station shows an "offline / use paper backup" message.
AIRTABLE_TIMEOUT_SECONDS = 10


# ---------------------------------------------------------------------------
# 2. AIRTABLE FIELD NAMES
# ---------------------------------------------------------------------------
# These must match the field names in Airtable EXACTLY (spelling, spaces, and
# capitalization). If a field is renamed in Airtable, update it here.
FIELD_BARCODE_VALUE     = "Barcode Value"       # e.g. "0042" (the ticket number)
FIELD_BARCODE_INTEGER   = "Barcode Integer"     # e.g. 42 (used for sorting)
FIELD_BARCODE_TEXT      = "Barcode Text"         # e.g. "Position # 0042"
FIELD_BARCODE_IMAGE     = "Barcode Image"        # printed later; unused in v1
FIELD_TICKET_PRINTED    = "Ticket Printed"       # checkbox we set to true
FIELD_PRINTED_TIMESTAMP = "Printed Timestamp"    # auto-stamped by Airtable


# ---------------------------------------------------------------------------
# 3. TICKET SELECTION BEHAVIOR
# ---------------------------------------------------------------------------
# Which field to sort by when finding the next ticket to issue. The lowest
# value is issued first. "Barcode Integer" gives true numeric order. (You may
# also use "Barcode Value" -- it sorts identically because the numbers are
# zero-padded, e.g. 0001 < 0002 < ... < 5000.)
SORT_FIELD = "Barcode Integer"

# The app generates each ticket locally (number + barcode), so it does NOT need
# an attached image. Leave this False. Only set it True if you switch to
# printing the Airtable "Barcode Image" attachment instead of a generated
# ticket, so the station skips any record that has no image.
REQUIRE_BARCODE_IMAGE = False

# Server-side safety lock. Ensures two rapid presses can never claim the same
# ticket number on this single-station setup. Leave True.
CLAIM_LOCK_ENABLED = True


# ---------------------------------------------------------------------------
# 4. PRINTING
# ---------------------------------------------------------------------------
# Print a ticket on each press. Requires the printing libraries (already
# installed if you ran the print test):
#     pip install -r requirements-printtest.txt
# The ticket prints BEFORE the record is marked printed, so if printing fails
# the voter is not counted as in line (fail-closed).
ENABLE_PRINTING = True

# The exact Windows printer name. Run  python print_test.py --list  to see the
# installed names. Leave "" to use the system default printer.
PRINTER_NAME = "DYMO LabelWriter 550"

# Ticket layout. Width is in printer dots (576 ~ 80mm at 203 dpi; the image is
# scaled to fit whatever media is loaded). PRINT_BARCODE draws a scannable
# Code128 of the number. PRINT_COPIES is how many to print per press.
TICKET_WIDTH_DOTS = 576
PRINT_BARCODE = True
PRINT_COPIES = 1


# ---------------------------------------------------------------------------
# 5. ON-SCREEN TEXT  (what voters and staff read)
# ---------------------------------------------------------------------------
STATION_NAME     = "Vote Center \u2014 Queue Ticket"
BUTTON_LABEL     = "Print Next Ticket"
WORKING_LABEL    = "Getting your number\u2026"
CONFIRM_EYEBROW  = "Your place in line"
CONFIRM_SUBTEXT  = "Remember your number. We'll call it when it's your turn."
DONE_LABEL       = "Next Voter"
NO_TICKETS_TITLE = "No tickets available"
NO_TICKETS_TEXT  = "All numbers have been issued. Please tell a poll worker."
OFFLINE_TITLE    = "System offline"
OFFLINE_TEXT     = "Please ask a poll worker for a paper ticket."
FOOTNOTE         = "Anonymous queue number \u2014 no personal information is collected."


# ---------------------------------------------------------------------------
# 6. TIMING & INPUT
# ---------------------------------------------------------------------------
# How long the confirmed number stays on screen before the station returns to
# the start automatically. Set to 0 to disable auto-return (staff/voter must
# press "Next Voter"). Seconds.
CONFIRM_DISPLAY_SECONDS = 10

# How often the station quietly checks it can still reach Airtable, to drive
# the online/offline status dot. Set to 0 to check only once, on load. Seconds.
HEALTH_POLL_SECONDS = 30

# Physical-button support. The app also issues a ticket when one of these keys
# is pressed, so a USB button (e.g. the X-keys button programmed to send a
# keystroke) works without a mouse. Values are JavaScript KeyboardEvent.key
# names. Default "F13" matches a typical X-keys mapping.
#   NOTE: do not use " " (space) or "Enter" here -- those already activate the
#   on-screen button when it is focused, and listing them would fire twice.
# Set to [] to disable the physical-button trigger entirely.
TRIGGER_KEYS = ["F13"]


# ---------------------------------------------------------------------------
# 7. LOCAL SERVER
# ---------------------------------------------------------------------------
# 127.0.0.1 keeps the station reachable only from this computer (recommended).
HOST = "127.0.0.1"
PORT = 5000
# Never enable debug on a live station.
DEBUG = False
