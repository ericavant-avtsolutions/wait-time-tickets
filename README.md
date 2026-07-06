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


Vote Center Wait Time Queue Tracking Proposal
 
**Project Proposal**
 
Vote Center Wait Time Queue Tracking Solution
 
*Simple ticket-based queue measurement using Airtable, a local receipt printer, and a greeter check-in interface*
 
Prepared for: Vote Center Operations and Technology Teams
Backend base: Airtable appUopMKWWjJNZNMa
Draft date: July 1, 2026
Updated hardware baseline: July 2, 2026
 
| **Recommended approach: **Use a lightweight localhost ticket-printer app for the ticket station, backed by Airtable, and use either an Airtable Interface or a very simple web interface for greeter check-in. Use Power Apps primarily as a fallback or for the greeter interface, not as the preferred ticket-printing path, because local USB receipt printing and single-button operation are the highest-risk parts of the workflow. |
| --- |
 
# 1. Executive Summary
 
**This proposal defines a simple wait-time queue tracking solution for vote centers. **The goal is to measure how long voters wait in line without collecting personally identifiable information and without creating unnecessary operational complexity. The system uses numbered queue tickets, Airtable checkbox/timestamp fields, and a greeter check-in workflow to calculate wait time from the moment a ticket is printed until the person reaches the front of the line.
 
**The recommended minimum viable product (MVP) is intentionally small: **one ticket station, one local USB receipt printer, one USB programmable button or large on-screen button, one greeter queue view, and the existing Airtable Barcode table. This gives operations real-time visibility into active queue depth and completed wait times while keeping the user action to two simple moments: print ticket and check in ticket.
 
| **Item** | **Proposal Detail** |
| --- | --- |
| **Primary business outcome** | Capture accurate queue wait times at vote centers in near real time, using only anonymous numbered tickets. |
| **Recommended MVP** | Localhost ticket-printer app + Airtable API + local USB receipt printer + greeter check-in view. |
| **Backend already prepared** | Airtable base appUopMKWWjJNZNMa, table Barcode / tblbo46VVEReXbG3I, with fields for barcode value, barcode image, printed status, check-in status, and calculated wait time. |
| **Design principle** | Do not overengineer. Optimize for reliability, speed, field usability, and clear fallback procedures. |
| **Critical planning decisions** | Printer model/driver support, single-site vs multi-site queue separation, daily reset/history handling, and how to calculate live active waits when Airtable NOW() formulas are not second-by-second real-time. |
 
# 2. Problem Statement and Goals
 
**Current operational need. **Vote center leadership needs a simple way to see how long people are waiting in line and how queue conditions change throughout the day. Manual observation can be subjective, inconsistent, and hard to compare across sites or time periods.
 
**Proposed method. **Each person entering the line receives a numbered ticket. When the ticket is printed, Airtable marks the ticket as printed and captures the printed timestamp. When that person reaches the front of the line, a greeter checks in the ticket number, Airtable captures the checked-in timestamp, and the base calculates the total wait time.
 
**MVP goal: **Capture queue wait time with no voter identity, no scanner requirement, and minimal staff interaction.
 
**Operational goal: **Provide a live view of active queue depth and a record of completed wait times for after-action review.
 
**Technology goal: **Use the existing Airtable schema and keep the ticket station implementation simple enough to troubleshoot quickly during election operations.
 
**User-experience goal: **A person at the entrance presses one button to print the next ticket; a greeter clicks one checkbox when that ticket reaches the front of the line.
 
# 3. Proposed Scope
 
## 3.1 In Scope for MVP
 
Anonymous numbered ticket issuance using pre-created Barcode records numbered 0001 through 5000.
 
Ticket printing from the Barcode Image attachment field to a locally connected USB thermal receipt printer.
 
Automatic update of Ticket Printed after the print job is successfully submitted to the local print system.
 
Greeter queue interface showing printed but not yet checked-in tickets in order.
 
Greeter check-in action that checks Ticket Checked In and captures the served timestamp.
 
Basic reporting: current queue count, longest active wait, completed average wait, completed median or percentile if supported by the reporting layer, and wait time by time window.
 
Simple fallback procedure using paper tickets if hardware, network, or Airtable access fails.
 
## 3.2 Out of Scope for MVP
 
Collection of voter names, voter IDs, check-in records, or other personally identifiable information.
 
AI camera-based person tracking or automatic visual queue measurement.
 
Complex queue routing, appointment scheduling, priority lanes, or multi-service classification unless added in a later phase.
 
Direct integration with the voter registration system or vote center check-in system.
 
Enterprise-scale kiosk management before the one-site pilot proves the workflow.
 
# 4. Existing Airtable Backend Design
 
**Backend base: **appUopMKWWjJNZNMa. The attached field specification shows one primary table for this workflow: **Barcode / tblbo46VVEReXbG3I.**
 
**Important implementation note: **The attached schema is sufficient for a single live queue. For multiple vote centers, the production design should either add a Vote Center/Site field, create site-specific filtered views/tables, or create a Queue Session layer so that tickets and wait metrics from different sites do not mix.
 
| **Field** | **Type** | **MVP Role** |
| --- | --- | --- |
| Barcode Value | singleLineText | The unique 4 digit numeric value (ie 0001, 0002, 0003, etc) |
| Barcode Integer | formula | The integer value of the Barcode Value (ie 1, 2, 3) |
| Barcode Text | formula | The text label for the queue, also visible on the barcode image |
| Barcode Image | multipleAttachments | The image to be printed on each new ticket generated |
| Ticket Printed | checkbox | This is a tracking field so the automated ticketing system knows which tickets are already printed and which ones are available to print. It also informs the... |
| Printed Timestamp | lastModifiedTime | Timestamp generated when the Ticket Printed field is checked. |
| Ticket Checked In | checkbox | This field is used at the front counter to track with the person reaches the front of the line is finally being helped by an employee. It also informs the Ch... |
| Checked In Timestamp | lastModifiedTime | Timestamp generated when the Ticket Checked In field is checked. |
| Wait Time (s) | formula | The elapsed time in seconds from when the ticket is printed and when the ticket is checked in; ultimately calculating the wait time in the queue |
| Wait Time (min) | formula | The elapsed time in minutes from when the ticket is printed and when the ticket is checked in; ultimately calculating the wait time in the queue |
| Time in Queue (s) | formula | Shows seconds since ticket was printed if not yet checked in. |
| Time in Queue (min) | formula | Shows minutes since ticket was printed if not yet checked in. |
 
**Timestamp behavior. **Printed Timestamp and Checked In Timestamp are last-modified-time fields tied to the checkbox fields. This is simple and useful for the MVP, but checkboxes should not be casually unchecked and rechecked because that can overwrite timestamp history. The greeter interface should hide unnecessary edit options and the daily reset process should preserve or export historical results before clearing fields.
 
# 5. Operating Workflow
 
## 5.1 Ticket Printing Workflow
 
A person arrives and enters the line.
 
Staff presses the USB programmable button or the on-screen Print Next Ticket button.
 
The local ticket-printer app finds the lowest available Barcode record where Ticket Printed is unchecked, sorted by Barcode Integer.
 
The app retrieves or uses a cached copy of the Barcode Image for that record.
 
The app submits the ticket image to the local USB receipt printer.
 
After successful print-job submission, the app updates Ticket Printed to checked in Airtable.
 
Airtable captures Printed Timestamp through the existing last-modified-time field.
 
The app resets to ready state for the next press.
 
**Recommended sequence control: **The app should apply a short lockout/debounce period after each press and should never print two tickets from the same record. If multiple ticket stations are later used at the same site, a locking approach or station-specific ticket ranges should be added.
 
## 5.2 Greeter Check-In Workflow
 
Greeter sees a queue list filtered to records where Ticket Printed is checked and Ticket Checked In is unchecked.
 
The list is sorted by Barcode Integer or Printed Timestamp, with the oldest open ticket at the top.
 
The person at the front presents or states the ticket number.
 
Greeter verifies that it matches the next expected position number or selects the correct visible ticket if numbers were skipped.
 
Greeter checks Ticket Checked In.
 
Airtable captures Checked In Timestamp and calculates Wait Time (s) and Wait Time (min).
 
## 5.3 System Flow
 
Entrance / Ticket Station
  USB Button or On-Screen Button
        |
        v
Localhost Ticket App  ----->  Local USB Receipt Printer
        |                           |
        | Airtable API update        | Physical ticket: Position # 0001
        v
Airtable Barcode Table
  Ticket Printed = checked
  Printed Timestamp captured
        |
        v
Greeter Queue Interface
  Open tickets sorted in order
        |
        v
Ticket Checked In = checked
Checked In Timestamp captured
Wait Time calculated
 
# 6. Solution Options
 
| **Option** | **Pattern** | **Advantages** | **Concerns** |
| --- | --- | --- | --- |
| Option A - Recommended | Localhost ticket-printer app + Airtable API | Best fit for one-button operation, USB printer control, local troubleshooting, and lowest operational friction. Can be built in Python/Flask, Node/Electron, or .NET. Greeter can use Airtable Interface or the same simple web app. | Requires a small local app to be installed and maintained on ticket-station workstations. |
| Option B - Hybrid | Localhost printer app + Power Apps or Airtable Interface for greeter | Keeps the hard part local and simple while allowing a low-code greeter interface. Good compromise if greeters are already comfortable with Microsoft or Airtable UI. | Requires two small surfaces to maintain: local ticket app and greeter app/interface. |
| Option C - Fallback | Power Apps + Power Automate / Power Automate Desktop | Fits Microsoft ecosystem and may reduce custom code for UI. Power Automate Desktop can interact with local workstation printing. | Less ideal for one-button receipt printing. Power Apps Print depends on browser printer behavior, and image printing through Power Automate Desktop can require workarounds. |
 
**Recommendation. **Proceed with Option A for the ticket station and use either Airtable Interface or a simple app page for greeter check-in. Reserve Power Apps / Power Automate Desktop as a fallback if local app deployment is not acceptable, or use Power Apps only for the greeter side where printing is not required.
 
# 7. Hardware and Local Workstation Requirements
 
**Receipt printer: **USB thermal receipt printer with Windows driver support, 80 mm paper support preferred, auto-cutter preferred, and support for bitmap/image printing. ESC/POS compatibility is preferred because it improves flexibility for direct receipt printing.
 
**Example printer class: **Epson TM-T20III/TM-T20IV-class USB thermal receipt printer or equivalent Star/Posiflex/Bixolon model. Epson documentation for TM-T20III lists thermal line printing, up to 250 mm/sec print speed, 80 mm and 58 mm media dimensions, USB interface options, barcode support, and auto-cutter reliability specifications [R5].
 
**USB programmable button: **Use a simple USB HID/macro button configured to send a unique keyboard shortcut such as F13 or Ctrl+Alt+P. The app listens for that shortcut and triggers Print Next Ticket. Avoid buttons requiring specialized drivers at the vote center.
 
Ticket-station computer: MSI Cubi N100 CUBNADL021 or equivalent Windows 11 Pro mini PC. The quoted 4 GB RAM / 128 GB storage configuration is acceptable for a locked-down pilot station running only the print app, driver, endpoint tools, and network stack; 8 GB RAM is preferred for production if endpoint agents or browser-based dashboards are heavy.
 
**Supplies: **Thermal paper rolls compatible with the selected printer width, spare rolls, and one spare printer per deployment group if the workflow becomes operationally critical.
 
**Printer decision required early. **The exact printer model should be selected before application build begins because print formatting, image size, cutter behavior, and silent-print feasibility depend on the printer driver and supported command set.
 
# 8. Data, Reporting, and Dashboard Design
 
**Current active line count: **Count records where Ticket Printed is checked and Ticket Checked In is unchecked.
 
**Completed wait time: **Use Wait Time (s) and Wait Time (min) after check-in is complete.
 
**Longest active wait: **For an app/dashboard display, calculate current time minus Printed Timestamp for open tickets. The Airtable Time in Queue formulas may be useful, but they should not be treated as a second-by-second timer because Airtable NOW() recalculates periodically rather than continuously [R2].
 
**Trend reporting: **Average, median, maximum, and 90th percentile wait by hour, day, vote center, and election event once a site/session field or history table exists.
 
**Operational alerts: **Optional later phase: alert supervisors when active queue count or active wait exceeds thresholds such as 10 people, 20 minutes, or site-specific escalation rules.
 
**History and reset concern. **The current schema appears to use pre-created ticket records that will be reused. If Ticket Printed and Ticket Checked In are cleared at the end of each day, the attached last-modified-time timestamps will be overwritten on the next use. Production reporting should therefore include one of these simple history options:
 
Export completed records to CSV before reset and store the export with the election/day/site naming convention.
 
Append each completed ticket to a lightweight Queue History table before reset.
 
Create a Queue Session or Vote Center field so one table can hold multiple sites and days without mixing active queues.
 
# 9. Functional Requirements
 
| **ID** | **Requirement** | **Description** |
| --- | --- | --- |
| FR-01 | Print next available ticket | The ticket station prints the lowest available unprinted Barcode record in sequence. |
| FR-02 | Mark ticket printed | After print-job submission, update Ticket Printed to checked. Printed Timestamp is captured by Airtable. |
| FR-03 | Prevent duplicate print | The app locks the selected record during the print/update action or uses a single-station MVP to eliminate concurrent selection risk. |
| FR-04 | Show active queue | Greeter sees only printed but not checked-in tickets, sorted in queue order. |
| FR-05 | Check in ticket | Greeter checks Ticket Checked In when the person reaches the front of the line. |
| FR-06 | Calculate wait | Airtable calculates Wait Time (s) and Wait Time (min) after check-in. |
| FR-07 | Handle skipped numbers | Greeter can check in a visible ticket that is not the first in line if the person with an earlier number left or missed their turn. |
| FR-08 | Provide status feedback | Ticket station shows Ready, Printing, Printed Position #, Printer Error, Airtable Error, and Offline/Fallback states. |
| FR-09 | Support reset/history | End-of-day process preserves history or exports completed data before reusing ticket records. |
 
# 10. Non-Functional Requirements
 
**Simplicity: **Entrance staff should not need to navigate Airtable or Power Apps to print a ticket.
 
**Reliability: **The solution should fail closed: if the ticket cannot print, it should not mark Ticket Printed unless staff confirms the ticket was issued.
 
**Security: **Store Airtable API credentials outside the visible UI, never printed on tickets, and never embedded in client-side JavaScript visible to users.
 
**Privacy: **Tickets are anonymous position numbers only. No voter identity or reason for visit is required for MVP.
 
**Performance: **A print action should complete within a few seconds under normal network and printer conditions.
 
**Rate limits: **Airtable Web API list requests are paged and the API has per-base rate limits; the MVP should query only the next needed record and update one record per ticket press to stay well within normal operating limits [R1].
 
**Training: **Greeter training should fit on one quick-reference card: verify number, check in, handle skipped numbers, and escalate errors.
 
# 11. Security, Privacy, and Election Operations Controls
 
Use a dedicated Airtable personal access token or OAuth app with least-privilege scopes limited to the specific base and required table actions.
 
Do not expose the Airtable token in browser-side JavaScript. The local app should keep credentials server-side on the local workstation.
 
Lock down the greeter interface to the minimum fields needed for check-in and visibility; avoid showing fields that invite accidental edits.
 
Disable or restrict direct checkbox reset during live operations except for a supervisor role.
 
Maintain a paper fallback queue pad and document how to manually enter or reconcile fallback tickets after service restoration.
 
Do not place voter names, voter IDs, party affiliation, ballot style, or issue reason on the ticket or in the MVP table.
 
# 12. Implementation Plan
 
| **Phase** | **Name** | **Key Work** | **Estimate** |
| --- | --- | --- | --- |
| 0 | Confirm design decisions | Confirm the CDW pilot BOM; verify printer accessories, receipt paper, enclosure approach, site/session approach, daily reset/history method, greeter UI choice, and local app install permissions. | 1-2 days |
| 1 | Build ticket-printer prototype | Create local app on the MSI Cubi that queries Airtable for the next unprinted record, prints the Barcode Image to the Bixolon BK3-31AA, checks Ticket Printed, responds to the X-keys button shortcut, and shows/logs status. | 3-5 days |
| 2 | Build greeter interface | Create Airtable Interface, Power App, or app page showing active queue and allowing Ticket Checked In update. | 1-3 days |
| 3 | Reporting view | Create Airtable views/dashboard for current line, completed waits, and exportable after-action metrics. | 1-3 days |
| 4 | Single-site pilot | Run controlled pilot with staff using realistic arrival/check-in volume. Validate timestamps, skip handling, printer reliability, and reset process. | 1 day pilot + review |
| 5 | Deploy or iterate | Document setup, train staff, procure any additional printers/buttons, and decide whether to extend to multi-site deployment. | As approved |
 
# 13. Key Risks and Mitigations
 
| **Risk** | **Level** | **Mitigation** |
| --- | --- | --- |
| Duplicate ticket printed | Medium | Use a single ticket station for MVP; add local lock/debounce; update selected record immediately after print job acceptance. |
| Printer offline, out of paper, or driver issue | High | Select printer early; test driver and image printing; display printer errors; keep paper fallback procedure. |
| Airtable unavailable or network down | Medium | Use paper fallback; optionally cache a limited ticket range locally and reconcile later only if approved. |
| Historical wait data overwritten during reset | High | Export or append to history table before clearing checkboxes; define daily reset ownership. |
| Multiple vote centers mixed in one table | High for production | Add Site/Vote Center or Queue Session field before multi-site rollout, or use site-specific copies/views. |
| Attachment URL/image access issue | Medium | Use fresh Airtable API response when printing or pre-cache approved ticket images locally before election day. Airtable stores attachments as files and exposes them for use by interfaces/API/automation, but attachment URL behavior should be tested in the target workflow [R3]. |
| Active wait display not truly live | Medium | Calculate active wait in the app/reporting layer for live dashboards rather than relying only on formula fields using NOW(). |
| Greeter checks wrong ticket | Low/Medium | Display large position number and next expected number; allow supervisor correction procedure; avoid editing completed records unless authorized. |
 
# 14. Pilot Success Criteria
 
Ticket station staff can issue tickets with one button press and no Airtable navigation.
 
Greeter can check in tickets from a simple ordered list with no training beyond a quick-reference card.
 
At least 99% of pilot tickets have both Printed Timestamp and Checked In Timestamp where the person reached the front of the line.
 
No voter personally identifiable information is captured.
 
Average print action completes within a few seconds under normal conditions.
 
Reports can show current active queue count, average completed wait, maximum completed wait, and active longest wait for the pilot period.
 
Fallback process can continue operations if the app, printer, or network fails.
 
# 15. Open Decisions Before Build
 
| **ID** | **Decision** | **Why It Matters** |
| --- | --- | --- |
| D-01 | Will the MVP pilot be one vote center and one queue, or multiple vote centers? | Determines whether the current Barcode table is enough or needs Site/Queue Session fields. |
| D-02 | Should ticket numbers reset daily, per site, or per election event? | Determines reset/history design and whether ticket numbers can be reused. |
| D-03 | Confirm final printer station hardware configuration from the CDW pilot BOM. | The proposed BOM is suitable for the pilot, but the team must confirm printer accessories, silent printing, enclosure mounting, paper path, spare supplies, and button mapping before scaling beyond one station. |
| D-04 | Will the ticket station app be allowed to run locally on vote center laptops? | Determines feasibility of the recommended localhost approach. |
| D-05 | Should the greeter interface be Airtable Interface, Power Apps, or the same local web app? | Determines UI maintenance and permissions. |
| D-06 | How should skipped/abandoned tickets be handled? | Determines whether to add a Cancelled/Skipped checkbox or allow greeter to leave old tickets open until supervisor cleanup. |
| D-07 | Who owns end-of-day export/reset? | Prevents accidental loss of timestamp history. |
| D-08 | Will the X-keys Green One Button be acceptable for production, or should the final enclosure use a flush industrial panel button? | The CDW button is compatible and mountable, but it is surface-mounted rather than a 22mm/30mm flush industrial control. This is acceptable for pilot; final enclosure polish may require a non-CDW panel button. |
 
# 16. Recommendation
 
**Approve a small pilot build using the existing Airtable Barcode table and a local ticket-printer app. **The pilot should be limited to one queue first. It should validate the user workflow, printer compatibility, timestamp accuracy, reset/history procedure, and greeter check-in interface before any multi-site deployment.
 
**The most important early planning item is the receipt printer. **Because the ticket is a physical artifact and the workflow depends on fast local printing, the project should select and test the USB receipt printer before the application is finalized. The second most important planning item is deciding whether production reporting requires a Site/Queue Session/History layer beyond the current Barcode table.
 
# Appendix A - MVP Technical Design Notes
 
## A.1 Local Ticket App Suggested Behavior
 
Runs on localhost as a small web app, tray app, or background service with a local browser UI.
 
Reads environment variable or secure local config file for Airtable API token and base/table settings.
 
On button press, queries Airtable for the next available record using a filtered view or filter formula.
 
Downloads or uses cached Barcode Image attachment for the selected record.
 
Prints the image to the configured receipt printer.
 
Updates Ticket Printed only after the print job is accepted by the local print system.
 
Shows large visual status: READY, PRINTING, PRINTED #0001, ERROR, FALLBACK MODE.
 
Logs local actions for troubleshooting: timestamp, barcode value, Airtable record ID, print result, update result.
 
**Example Airtable selection logic, expressed conceptually:**
 
Find first record in Barcode table where:
  Ticket Printed is unchecked
  Barcode Image is not empty
Sort ascending by Barcode Integer
Limit result to 1 record
Print Barcode Image
PATCH record: Ticket Printed = true
 
## A.2 Greeter Interface Suggested Behavior
 
Filtered list: Ticket Printed = checked AND Ticket Checked In = unchecked.
 
Sort by Printed Timestamp ascending, then Barcode Integer ascending.
 
Large display of Barcode Text / Position number.
 
Single action: Check In.
 
Optional secondary action: Mark skipped/cancelled, only if an additional field is approved.
 
Supervisor-only correction view for mistaken check-ins.
 
# Appendix B - Planning References
 
| **Ref** | **Source** | **Planning Relevance** | **URL** |
| --- | --- | --- | --- |
| R1 | Airtable Web API getting started | Airtable documents record paging behavior and notes a Web API rate limit of 5 requests per second per base. | https://support.airtable.com/docs/getting-started-with-airtables-web-api |
| R2 | Airtable formula field reference | Airtable documents NOW() recalculation behavior; useful for interpreting Time in Queue formula limitations. | https://support.airtable.com/docs/formula-field-reference |
| R3 | Airtable attachment fields / attachment URL behavior | Airtable documents attachment field behavior, storage, and attachment URL workflow considerations. | https://support.airtable.com/docs/attachment-field |
| R4 | Microsoft Power Apps Print function | Microsoft documents Print function limitations, including mobile support and browser printer behavior. | https://learn.microsoft.com/en-us/power-platform/power-fx/reference/function-print |
| R5 | Microsoft Power Automate Desktop workstation and image printing references | Microsoft documents Print document actions and notes that image printing can require a separate image-printing approach. | https://learn.microsoft.com/en-us/power-automate/desktop-flows/actions-reference/workstation |
| R6 | Epson TM-T20III specification sheet | Epson specification sheet lists thermal printing, USB interface options, media sizes, barcode support, print speed, and cutter reliability. | https://mediaserver.goepson.com/ImConvServlet/imconv/436ded101ebd425440d8821a9671200969865e02/original?assetDescr=TM-T20III_Specification_Sheet_CPD-58120R1.pdf |
| R7 | CDW Shopping Cart PDF, page 1 | Provides the actual pilot BOM, CDW and manufacturer part numbers, quantities, Sourcewell pricing, item totals, and current availability. | Attached file: CDW _ Shopping Cart.pdf |
| R8 | Bixolon BK3 Series product page | Documents the BK3 Series as a 2-inch/3-inch open-frame kiosk thermal printer family with 203 dpi resolution and up to 250 mm/sec printing. | https://www.bixolon.com/product_view.php?idx=181 |
| R9 | Bixolon BK3-31 support/downloads | Documents the BK3-31 3-inch kiosk printer, driver/download availability, media-roll support, and bezel/presenter/retractor accessory considerations. | https://www.bixolon.com/download_view.php?idx=46 |
| R10 | MSI Cubi N ADL specifications | Documents the Cubi N ADL mini PC I/O profile, USB ports, 128 GB M.2 SSD configuration, VESA support, and business mini-PC specifications. | https://us.msi.com/Business-Productivity-PC/Cubi-N-ADL/Specification |
| R11 | CDW X-keys USB 3 Switch Interface listing | Documents switch connection via standard 3.5mm phone plugs and onboard macro/HID behavior relevant to the one-button workflow. | https://www.cdw.com/product/p.i.-engineering-x-keys-usb-3-switch-interface-assistive-switch-interface/3643729 |
| R12 | P.I. Engineering X-keys Green One Button Switch | Documents the button as a normally open switch with a 3.5mm mono plug, 12-foot cord, bottom mounting holes, and compatibility with X-keys USB Switch Interface devices. | https://piengineering.com/products/greenonebutton |
 
# Appendix C - Attached Field Specification Summary
 
| **Field Name** | **Field ID** | **Type** | **Status** | **Computed Using** |
| --- | --- | --- | --- | --- |
| Barcode Value | fldy7uUlqucmrx6Rf | singleLineText | editable | External app/Excel/Precalculated positions for each ticket available in the system |
| Barcode Integer | fldyL1zAA4SEqRF1S | formula | computed | '=INT({Barcode Value}) |
| Barcode Text | fldqO75H2OXtIIK4L | formula | computed | ="Position # "& {Barcode Value} |
| Barcode Image | fldlwRwUc6XO5a5DI | multipleAttachments | editable |  |
| Ticket Printed | fldZ3VKtHTpu3QjEy | checkbox | editable |  |
| Printed Timestamp | fldC0iDoToOJnZgNu | lastModifiedTime | computed |  |
| Ticket Checked In | fldvScOgPHLruNTx8 | checkbox | editable |  |
| Checked In Timestamp | fldlwBSqQ4LjNGL6N | lastModifiedTime | computed |  |
| Wait Time (s) | fldXO7j7YbV6jfOai | formula | computed | '=IF(   AND({Printed Timestamp}, {Checked In Timestamp}),     DATETIME_DIFF({Checked In Timestamp}, {Printed Timestamp}, 'seconds'),     BLANK() ) |
| Wait Time (min) | fldNRz52p71ZCJvet | formula | computed |  |
| Time in Queue (s) | fldQJTujgnZaZZFPD | formula | computed | '=IF(   AND({Ticket Printed}, NOT({Ticket Checked In})),     DATETIME_DIFF(NOW(), {Printed Timestamp}, 'seconds'),     BLANK() ) |
| Time in Queue (min) | fldvw0fjzC6dEL4nb | formula | computed | '=IF({Time in Queue (s)}, {Time in Queue (s)} / 60, BLANK()) |
 
# Appendix C - CDW Bill of Materials Review and Hardware Baseline
 
Verdict: The attached CDW shopping-cart bill of materials supports the intended MVP solution. It is an appropriate pilot hardware baseline for the recommended Option A architecture: local Windows mini PC, local USB kiosk printer, USB button interface, and Airtable-backed localhost ticket-printer app. It should not be treated as a complete production deployment kit until the validation tests below are completed.
 
| **Compatibility conclusion: Approved for pilot. The quoted components support a single-button ticket station using the Bixolon BK3-31AA printer, MSI Cubi N100 mini PC, X-keys USB 3 Switch Interface, and X-keys Green One Button. The main remaining risks are print-driver validation, exact printer accessory configuration, enclosure fit, receipt-paper supplies, and whether the surface-mounted X-keys button is acceptable for the final appliance.** |
| --- |
 
| **Component** | **Quote Detail** | **Project Role** | **Compatibility / Project Notes** |
| --- | --- | --- | --- |
| Bixolon 3-inch 203 dpi Kiosk Thermal Printer | MFG BK3-31AA; CDW 8043814; Qty 1; quoted item total $132.65; in stock on quote. | Primary ticket printer. | Strong fit. Open-frame kiosk printer category is appropriate for a custom housing. Validate auto-cutter/presenter/bezel, paper-roll holder, power supply, USB/serial interface, and reliable image/barcode output from the local app. |
| MSI Cubi N100 4 GB RAM / 128 GB / Windows 11 Pro | MFG CUBNADL021; CDW 7417309; Qty 1; quoted item total $344.66; in stock on quote. | Local print-station computer. | Strong fit for Option A. Windows 11 Pro helps with Bixolon driver support and endpoint management. 4 GB RAM is acceptable for a locked-down pilot; prefer 8 GB for production if normal endpoint/security tooling is heavy. |
| P.I. Engineering X-keys USB 3 Switch Interface | MFG XK-1283-UJS3-R; CDW 3643729; Qty 1; quoted item total $59.81; expected 11-13+ days on quote. | Converts external button press into a USB keyboard/HID command. | Strong fit. Program to emit a unique shortcut such as F13 or Ctrl+Alt+P. Local app/service should listen for that shortcut and ignore accidental repeat presses with debounce/lockout logic. |
| P.I. Engineering Green One Button Switch | MFG XK-A-1581-1BGR-R; CDW 8404691; Qty 1; quoted item total $45.38; expected 2-4+ days on quote. | Physical one-button trigger for ticket printing. | Compatible with the X-keys interface. Better than a consumer USB macro button. It is surface-mounted with bottom mounting holes rather than a flush 22mm/30mm industrial panel button, so final enclosure polish should be reviewed. |
| Quoted pilot station subtotal | Approx. $582.50 for the four quoted hardware items, before any additional shipping/tax/fees and before unquoted materials. | Budget planning baseline. | Does not include enclosure fabrication, receipt paper, spare equipment, setup peripherals, cable management, power protection, software build time, or support/training labor. |
 
Recommended architecture using this BOM:
 
MSI Cubi N100 runs Windows 11 Pro, the Bixolon printer driver, the local ticket-printer app, and a lightweight status/logging service.
 
X-keys Green One Button connects to the X-keys USB 3 Switch Interface, which connects to the MSI Cubi by USB and emits the configured print-ticket hotkey.
 
Bixolon BK3-31AA connects locally to the MSI Cubi, preferably by USB for the pilot; serial can remain a fallback if the selected configuration and app support it.
 
The local app queries Airtable for the next unprinted Barcode record, prints the Barcode Image or locally generated ticket layout, then checks Ticket Printed only after print-job acceptance.
 
Greeter check-in remains separate and simple: Airtable Interface, Power App, or app page filtered to printed/not-checked-in tickets.
 
Items still missing from the quoted BOM:
 
Thermal receipt paper rolls compatible with the final Bixolon media width and roll-holder configuration; include spare rolls for every pilot shift.
 
Custom enclosure, printer mounting plate, ticket exit slot/bezel or presenter hardware, service access panel, ventilation, and cable strain relief.
 
Power distribution/protection inside the station, including any required printer power supply confirmation, short power strip, and surge protection as approved by facilities/IT.
 
Setup peripherals: temporary keyboard, mouse, and HDMI/DisplayPort monitor or portable field monitor for troubleshooting. These do not need to remain attached during daily operation.
 
Optional spare parts: one spare printer or printer mechanism, spare X-keys button/interface, and one spare configured mini PC if the workflow becomes operationally critical.
 
Labels and staff-facing instructions, including a durable "Print Queue Ticket" label and one-page quick-reference procedure.
 
Required pilot validation tests before scaling:
 
| **Test** | **Pass Criteria** | **Owner / Timing** |
| --- | --- | --- |
| Printer driver and image test | MSI Cubi can silently or near-silently print the Airtable Barcode Image or locally generated ticket layout to the BK3-31AA with readable barcode/text and clean cut/presentation. | Technology, before app build is finalized |
| One-button input test | X-keys interface sends the configured shortcut reliably; local app triggers one and only one ticket per press and debounces repeated/held presses. | Technology, during prototype |
| Airtable end-to-end test | App selects the lowest unprinted ticket, prints it, checks Ticket Printed, and Airtable captures Printed Timestamp. Greeter can check in the same ticket and wait time calculates correctly. | Technology + Operations, during prototype |
| Power recovery/headless test | After power loss/reboot, Windows starts, app/service starts, printer is available, button works, and no monitor is needed for normal use. | Technology, before pilot |
| Enclosure/field setup test | Ticket exits cleanly, paper can be replaced, button is obvious and durable, cables are protected, Cubi has ventilation, and troubleshooting ports remain accessible. | Technology + Facilities, before pilot deployment |
| Fallback test | Staff can switch to paper fallback and later reconcile skipped/printed tickets without corrupting wait-time data. | Operations, pilot training |
 
Production decision guidance: If the CDW X-keys Green One Button is accepted by staff and fits the enclosure cleanly, it can remain the standard button. If the final station needs a more polished flush-mounted control-panel appearance, keep the CDW X-keys USB 3 Switch Interface but replace the physical button with a 22mm or 30mm normally-open momentary panel button sourced from an industrial/electrical vendor.
 
Draft planning proposal - queue ticketing, check-in, Airtable reporting
