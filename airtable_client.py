"""
airtable_client.py
==================
A tiny, transparent wrapper around the Airtable Web API for the ticket
station. It does exactly what the station needs and nothing more:

  1. Find the next available (unprinted) ticket -- lowest number first.
  2. Mark that ticket printed (which makes Airtable stamp the printed time).

Kept deliberately small and readable so it can be understood and
troubleshooted quickly during live election operations. Uses only `requests`.
"""

import threading
from contextlib import nullcontext

import requests

import config


# --- Errors, so app.py can show the right on-screen state -------------------

class AirtableError(Exception):
    """Airtable could not be reached or returned an error."""


class NoTicketsAvailable(Exception):
    """Every ticket has already been issued."""


class TokenNotConfigured(Exception):
    """The Airtable API token has not been set."""


# One lock shared across requests so two near-simultaneous presses on this
# single station can never claim the same ticket.
_claim_lock = threading.Lock()


# --- Low-level helpers ------------------------------------------------------

def _api_url(record_id=""):
    base = (
        "https://api.airtable.com/v0/"
        f"{config.AIRTABLE_BASE_ID}/{config.AIRTABLE_TABLE_ID}"
    )
    return f"{base}/{record_id}" if record_id else base


def _headers():
    if not config.AIRTABLE_TOKEN:
        raise TokenNotConfigured(
            "AIRTABLE_TOKEN is not set. Add it to a .env file or an "
            "environment variable (see .env.example)."
        )
    return {
        "Authorization": f"Bearer {config.AIRTABLE_TOKEN}",
        "Content-Type": "application/json",
    }


def _unprinted_formula():
    """Airtable filter for 'not yet printed' (optionally: 'and has an image')."""
    printed = config.FIELD_TICKET_PRINTED
    if config.REQUIRE_BARCODE_IMAGE:
        image = config.FIELD_BARCODE_IMAGE
        return f"AND(NOT({{{printed}}}), {{{image}}})"
    return f"NOT({{{printed}}})"


# --- Operations the station uses --------------------------------------------

def get_next_available_ticket():
    """
    Return the lowest-numbered unprinted ticket record, or None if there are
    none left. Does NOT modify anything.
    """
    params = {
        "filterByFormula": _unprinted_formula(),
        "maxRecords": 1,
        "pageSize": 1,
        "sort[0][field]": config.SORT_FIELD,
        "sort[0][direction]": "asc",
    }
    try:
        resp = requests.get(
            _api_url(),
            headers=_headers(),
            params=params,
            timeout=config.AIRTABLE_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise AirtableError(f"Could not reach Airtable: {exc}") from exc

    if resp.status_code != 200:
        raise AirtableError(f"Airtable returned {resp.status_code}: {resp.text[:300]}")

    records = resp.json().get("records", [])
    return records[0] if records else None


def mark_ticket_printed(record_id):
    """
    Set Ticket Printed = true on the given record. Airtable then stamps the
    Printed Timestamp automatically. Returns the updated record.
    """
    body = {"fields": {config.FIELD_TICKET_PRINTED: True}}
    try:
        resp = requests.patch(
            _api_url(record_id),
            headers=_headers(),
            json=body,
            timeout=config.AIRTABLE_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise AirtableError(f"Could not reach Airtable: {exc}") from exc

    if resp.status_code != 200:
        raise AirtableError(f"Airtable returned {resp.status_code}: {resp.text[:300]}")

    return resp.json()


def claim_next_ticket(before_mark=None):
    """
    Issue the next ticket: find the lowest unprinted record and mark it printed.

    Returns a small dict the screen can display:
        {
            "record_id":     "rec...",
            "barcode_value": "0042",
            "position_text": "Position # 0042",
        }

    Raises NoTicketsAvailable if none are left, or AirtableError on failure.

    `before_mark`, if given, is called as before_mark(barcode_value) after the
    record is found but BEFORE it is marked printed. It is used to print the
    ticket: if it raises (e.g. the printer failed), the record is NOT marked,
    so the exception propagates and no number is shown -- fail-closed, so a
    voter is never counted as in line for a ticket that did not print.

    The find + (print) + mark run under a lock so the same ticket cannot be
    claimed twice on this station.
    """
    lock_ctx = _claim_lock if config.CLAIM_LOCK_ENABLED else nullcontext()
    with lock_ctx:
        record = get_next_available_ticket()
        if record is None:
            raise NoTicketsAvailable()

        record_id = record["id"]
        fields = record.get("fields", {})
        barcode_value = fields.get(config.FIELD_BARCODE_VALUE, "")
        position_text = fields.get(
            config.FIELD_BARCODE_TEXT, f"Position # {barcode_value}"
        )

        # Print first (if a printer hook was provided). This raises on failure,
        # so we never reach the "mark printed" step for a ticket that did not
        # actually print.
        if before_mark is not None:
            before_mark(barcode_value)

        # Raises on failure -> we never reach the return below, so no number is
        # shown for a ticket we could not reserve.
        mark_ticket_printed(record_id)

        return {
            "record_id": record_id,
            "barcode_value": barcode_value,
            "position_text": position_text,
        }


def check_health():
    """
    Best-effort status for staff. Returns:
        {"online": bool, "tickets_available": bool, "detail": str}
    Does one cheap query (at most one record) and never modifies data.
    """
    try:
        record = get_next_available_ticket()
        return {"online": True, "tickets_available": record is not None, "detail": ""}
    except (TokenNotConfigured, AirtableError) as exc:
        return {"online": False, "tickets_available": False, "detail": str(exc)}
