# Vote Center Ticket Station — Version 1 Plan

## Goal
A local web app with a large on-screen "Print Next Ticket" button that
confirms the voter's number and marks the ticket printed in Airtable.
No print jobs yet (no printer connected). All tunable values live in one
easy-to-maintain config file.

## Plan
- [x] Confirm Airtable schema (base, table, field names) from the CSV
- [x] Design a civic, high-contrast, accessible kiosk UI (offline-safe fonts)
- [x] `config.py` — single, well-commented variables file (no secrets)
- [x] `.env` handling for the Airtable token (server-side only)
- [x] `airtable_client.py` — find lowest unprinted ticket; mark printed
- [x] Fail-closed claim: only confirm a number after the Airtable write succeeds
- [x] Server-side lock to prevent double-claim on one station
- [x] `app.py` — Flask routes: `/`, `POST /api/print-ticket`, `/api/health`
- [x] Frontend states: Ready, Working, Confirmed, No tickets, Offline
- [x] Accessibility: large targets, focus ring, aria-live number, reduced motion
- [x] Optional physical-button key trigger (configurable; default key `F13`)
- [x] Online/offline status dot with light polling
- [x] `test_app.py` — success, no-tickets, error, not-configured, health, claim
- [x] README with Windows setup, security, and "enable printing later" notes

## Verification
- [x] `python -m unittest` — all tests pass
- [x] `GET /` renders the button label
- [x] `POST /api/print-ticket` returns the number on success and correct
      status codes on no-tickets / error (verified with mocked Airtable)
- [x] Server imports and starts, prints a status banner

## Review
- Delivered Option A from the proposal: a localhost Flask app + Airtable API.
  The token stays server-side; the browser only calls `/api/print-ticket` and
  `/api/health`.
- `config.py` is the single maintenance surface for base/table/field names,
  on-screen copy, timing, the physical-button key, and the printing flag.
- Printing is stubbed off (`ENABLE_PRINTING = False`, `REQUIRE_BARCODE_IMAGE =
  False`). The claim path already writes `Ticket Printed`, so timestamps and
  wait-time formulas populate correctly for the pilot even before a printer
  exists.
- Scope kept intentionally small: single station, single queue. Multi-site and
  history/reset handling remain out of scope for v1 per the proposal.

---

## Add-on — Printer de-risking (standalone, pre-procurement)
- [x] `print_test.py` — standalone tool: list printers + silently print a ticket image to any Windows printer
- [x] Generate a realistic 80mm-width ticket (big number + Code128 barcode), autocropped
- [x] `--save-image` mode (no printer) — cross-platform preview; **verified in sandbox**
- [x] `requirements-printtest.txt` — pywin32 gated to Windows; kept out of the app's deps
- [x] `PRINT_TEST.md` — test procedure + pass criteria mirroring the proposal
- [x] (User) Run on Windows against a Dymo/any printer to confirm silent print
- [x] (Later) Wire the print call into the app behind `ENABLE_PRINTING`, fail-closed

### Note
- A Dymo validates the *image-based* silent print path (the path the app will
  use). It does not test ESC/POS, receipt roll, or auto-cutter — those are
  receipt-printer specifics confirmed after procurement.

---

## Fix — TemplateNotFound on first run (user report, 2026-07-02)
- [x] Diagnosed: templates/ and static/ subfolders were flattened when files
      were downloaded individually -> Flask can't find templates/index.html
- [x] Reproduced the exact error, and confirmed cwd is NOT the cause
- [x] config.py: load .env from the script directory (cwd-independent token)
- [x] app.py: fail-fast startup check listing any misplaced files
- [x] Ship a single ZIP that preserves the folder structure
- [x] Verified: 11 tests pass; structure check fires; .env loads from any cwd

---

## v2 — Enable printing to DYMO LabelWriter 550 (user request, 2026-07-02)
Plan:
- [x] `printer.py` — shared module: generate ticket + silent Windows print + list; raises PrinterError
- [x] Refactor `print_test.py` to import from `printer.py` (DRY; keep CLI identical)
- [x] `config.py` — ENABLE_PRINTING=True, PRINTER_NAME="DYMO LabelWriter 550", width/barcode/copies
- [x] `airtable_client.claim_next_ticket(before_mark=...)` — inject print step, fail-closed, under existing lock
- [x] `app.py` — pass printer.print_ticket as before_mark; map PrinterError -> 503
- [x] Tests — before_mark called; fail-closed when print fails; route maps PrinterError
- [x] Verify generation unchanged; app imports and serves; tests green; rebuild ZIP

Review (v2 printing):
- Shared printer.py is the single source of truth; print_test.py and app.py both
  use it, so production prints the exact ticket validated on the DYMO 550.
- Fail-closed enforced in one place: claim_next_ticket prints via before_mark and
  only marks Ticket Printed if that succeeds. If the printer fails, the number is
  not consumed and the voter sees the offline message.
- Printing libs are lazily imported; the app still runs with printing disabled or
  on non-Windows. Missing libs raise a clear PrinterError (fail-closed).
- Verified: generation unchanged, 14 tests pass, app serves, PrinterError maps to 503.

---

## Fix — nothing printed despite "Printing: ENABLED" (user report, 2026-07-02)
- [x] Diagnosed from banner + logs: OLD app.py/airtable_client.py still in place
      (partial file swap) -> printer.print_ticket never called; tickets marked only
- [x] Added startup printer preflight (found / wrong-name / libs-missing) for
      immediate, clear feedback
- [x] Verified preflight branches + 14 tests pass; rebuilt full ZIP
- [x] Fix for user: deploy the complete ZIP (all four .py files move together)
