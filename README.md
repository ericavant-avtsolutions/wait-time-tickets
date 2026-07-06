# Vote Center Ticket Station — Version 1

A small local web app for issuing anonymous queue numbers at a vote center.
It shows one large **Print Next Ticket** button. Each press:

1. Finds the next available (lowest, unprinted) ticket number in Airtable.
2. Marks that ticket **Printed** in Airtable — Airtable stamps the print time,
   which starts the wait-time clock.
3. Shows the voter their confirmed number, large, on screen.

**Printing is enabled** and targets the printer named in `config.py`
(`PRINTER_NAME`, currently `DYMO LabelWriter 550`). Each press prints a ticket
and also shows the number on screen. The ticket prints *before* the record is
marked printed, so a failed print never counts a voter as in line. To run
without a printer, set `ENABLE_PRINTING = False` in `config.py`.

No voter names, IDs, or personal information are collected — only an anonymous
position number.

---

## What's in this folder

| File | Purpose |
| --- | --- |
| `config.py` | **The one file you edit.** Base/table/field names, on-screen text, timing, server settings. |
| `.env` | Holds only the secret Airtable token (you create this — see setup). |
| `app.py` | The local web server (Flask). Serves the screen and talks to Airtable. |
| `airtable_client.py` | Small, readable Airtable API wrapper. |
| `templates/index.html` | The kiosk screen. |
| `static/style.css`, `static/app.js` | Screen styling and behavior. |
| `test_app.py` | Automated tests (no network needed). |
| `tasks/` | Project plan and lessons log. |

---

## Setup (Windows 11 — the MSI Cubi station)

1. **Install Python 3.10+** from python.org. During install, check
   *"Add Python to PATH."*

2. **Open a terminal** in this folder (Shift + Right-click → *"Open PowerShell
   window here"*).

3. **(Recommended) create a virtual environment:**
   ```
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

4. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

5. **Add your Airtable token.** Copy `.env.example` to `.env` and paste your
   token into it:
   ```
   copy .env.example .env
   notepad .env
   ```
   Create the token at <https://airtable.com/create/tokens> with scopes
   `data.records:read` and `data.records:write`, limited to base
   `appUopMKWWjJNZNMa`.

6. **Review `config.py`** — it's already set for this base and table, so you
   usually don't need to change anything.

7. **Run it:**
   ```
   python app.py
   ```

8. **Open the screen:** go to <http://127.0.0.1:5000> in a browser and put it
   in full-screen / kiosk mode (**F11** in most browsers).

---

## Using the station

- Touch **Print Next Ticket**. The screen confirms the voter's number, then
  returns to the button automatically after a few seconds (adjust
  `CONFIRM_DISPLAY_SECONDS` in `config.py`, or set it to `0` to wait for a
  **Next Voter** tap).
- The status dot (top-right) shows **Online**, **No tickets left**, or
  **Offline**.
- If it shows **Offline**, hand out paper tickets and reconcile later.

### The physical button (optional, future)

When the X-keys USB button is wired up, program it to send the key set in
`TRIGGER_KEYS` in `config.py` (default `F13`). The station then issues a ticket
on each button press. Until then, the on-screen button is all you need.

---

## How the wait-time clock works

- Pressing the button sets **Ticket Printed** in Airtable → Airtable records
  **Printed Timestamp** (the moment the voter joined the line).
- Later, at the front counter, a greeter checks **Ticket Checked In** →
  Airtable records **Checked In Timestamp** and calculates the wait.
- The greeter check-in interface is separate and not part of Version 1.

---

## Security & privacy

- The Airtable token lives only in `.env` on this computer and is used
  server-side. It is **never** sent to the browser.
- Don't commit `.env` (`.gitignore` already excludes it).
- Tickets carry only a position number — no personal information.

---

## Printing

Printing is handled by `printer.py`, which is shared with the standalone
`print_test.py` tool — so the ticket that prints in production is the exact
layout you validate with the tester.

- **Requirements:** the printing libraries in `requirements-printtest.txt`
  (`pip install -r requirements-printtest.txt`). If you ran the print test,
  they're already installed.
- **Choose the printer:** run `python print_test.py --list` to see the exact
  names, then set `PRINTER_NAME` in `config.py` (currently
  `DYMO LabelWriter 550`). Leave it `""` to use the system default.
- **Layout:** `TICKET_WIDTH_DOTS`, `PRINT_BARCODE`, and `PRINT_COPIES` in
  `config.py` control the ticket. The image scales to fit whatever media is
  loaded.
- **Turn it off:** set `ENABLE_PRINTING = False` to run screen-only.

**Fail-closed:** on each press the ticket is printed first, and the Airtable
record is marked `Ticket Printed` only if the print succeeds. If the printer
fails, the number is not consumed and the screen shows the offline message.

> A DYMO validates the image print path the app uses. When the Bixolon receipt
> printer arrives, just update `PRINTER_NAME` — no code change needed. (Raw
> ESC/POS and auto-cutter behavior are receipt-printer specifics to confirm
> then.)

---

## Running the tests

```
python -m unittest
```

The tests mock Airtable, so they run offline and make no API calls.

---

## Notes for a hardened deployment

The built-in Flask server is fine for a single local kiosk. For a more
hardened setup you can run it behind a production WSGI server (e.g. `waitress`)
and configure the browser to launch full-screen in kiosk mode at startup.
