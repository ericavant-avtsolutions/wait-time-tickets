# Lessons Log

Patterns and corrections captured during this project, so the same mistake
isn't repeated. Review at the start of each session.

## Version 1 build
- Airtable `Printed Timestamp` is a last-modified-time tied to `Ticket
  Printed`; setting the checkbox is what stamps the time. Do not add a
  separate timestamp write.
- Keep the Airtable token server-side only (never in browser JS) — matches the
  proposal's security requirement.
- `Barcode Value` is zero-padded (0001–5000), so it sorts correctly as text
  or via `Barcode Integer`. Default sort uses `Barcode Integer`.
- Claim must be fail-closed: read display values from the found record, mark
  printed, and only return a number if that write succeeds — so a voter is
  never shown a number that wasn't reserved.
- Don't put Space/Enter in `TRIGGER_KEYS`: they already activate a focused
  on-screen button, so a global handler for them would fire twice.

## Printer testing
- The high-risk item to de-risk is *silent printing from code to a Windows
  printer*, which is printer-agnostic. Any installed printer (Dymo, inkjet,
  or Microsoft Print to PDF) can prove that path before buying hardware.
- Silent GDI image printing on Windows = pywin32 win32ui printer DC +
  StartDoc/StartPage + ImageWin.Dib.draw. Real printers don't prompt;
  Microsoft Print to PDF does (asks for a filename), so it's only a partial
  "silent" test.
- Keep pywin32 out of the app's requirements — it's Windows-only. Gate it in a
  separate requirements file with a platform marker.

## Packaging / deployment
- Delivering files individually flattens the templates/ and static/ subfolders,
  which causes Flask `TemplateNotFound: index.html` at request time. ALWAYS ship
  the app as a ZIP that preserves the folder structure.
- Make the app cwd-independent so it works no matter where it's launched from:
  load .env via `Path(__file__).parent / ".env"` (not bare `load_dotenv()`,
  which reads from the current directory), and add a startup check that verifies
  templates/ and static/ are present, failing fast with a plain-language fix.

## Printing integration
- Keep one source of truth for the ticket: a shared printer.py used by both the
  CLI tester and the app, so "what you tested" == "what prints".
- Enforce fail-closed at a single chokepoint: print inside the locked claim,
  before marking Ticket Printed. Never mark-then-print.
- Lazy-import Windows/printing libs inside functions so the app imports anywhere
  and a missing dependency fails closed with an install hint, not a crash.

## Deployment / version skew
- Replacing files individually caused a version-skew bug: new config.py + printer.py
  but OLD app.py + airtable_client.py, so printing was never called (tickets marked,
  nothing printed). Symptom: banner read "Printing: ENABLED" (old) instead of
  "ENABLED -> <printer>" (new), and POST returned 200 with no Printer error line.
- Rule: deploy the WHOLE ZIP, never a subset of the .py files. The four files
  (app.py, airtable_client.py, printer.py, config.py) must move together.
- Make config observable at startup: the banner now echoes the target printer and a
  preflight confirms the printer exists, so stale/wrong wiring is visible immediately.
