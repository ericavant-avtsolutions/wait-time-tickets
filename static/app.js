/* ===========================================================================
   Vote Center Ticket Station -- Version 1 (frontend)

   One button. Press it -> ask the local server for the next number -> show it.
   The server holds the Airtable token; this file never sees it.

   States: ready -> working -> confirmed | noTickets | offline
   =========================================================================== */

(function () {
  "use strict";

  var cfg = window.STATION_CONFIG || {};

  var panels = {
    ready:     document.getElementById("panelReady"),
    working:   document.getElementById("panelWorking"),
    confirm:   document.getElementById("panelConfirm"),
    noTickets: document.getElementById("panelNoTickets"),
    offline:   document.getElementById("panelOffline")
  };

  var printButton  = document.getElementById("printButton");
  var nextButton   = document.getElementById("nextButton");
  var noTicketsBtn = document.getElementById("noTicketsBack");
  var offlineRetry = document.getElementById("offlineRetry");
  var placardNumber = document.getElementById("placardNumber");
  var offlineText   = document.getElementById("offlineText");

  var statusEl     = document.getElementById("status");
  var statusText   = document.getElementById("statusText");

  var busy = false;          // true only while a request is in flight
  var autoReturnTimer = null;

  // --- Panel helpers -------------------------------------------------------

  function showPanel(name) {
    for (var key in panels) {
      if (Object.prototype.hasOwnProperty.call(panels, key)) {
        panels[key].hidden = (key !== name);
      }
    }
  }

  function clearAutoReturn() {
    if (autoReturnTimer) {
      clearTimeout(autoReturnTimer);
      autoReturnTimer = null;
    }
  }

  function toReady() {
    clearAutoReturn();
    showPanel("ready");
    if (printButton) { printButton.focus(); }
  }

  function renderConfirm(data) {
    placardNumber.textContent = data.barcode_value || data.position_text || "\u2014";
    showPanel("confirm");
    if (nextButton) { nextButton.focus(); }

    var secs = Number(cfg.confirmDisplaySeconds) || 0;
    if (secs > 0) {
      autoReturnTimer = setTimeout(toReady, secs * 1000);
    }
  }

  function renderOffline(message) {
    if (message) { offlineText.textContent = message; }
    showPanel("offline");
    if (offlineRetry) { offlineRetry.focus(); }
  }

  // --- The core action: issue the next ticket ------------------------------

  function issueTicket() {
    if (busy) { return; }          // ignore rapid repeat presses while working
    busy = true;
    clearAutoReturn();
    showPanel("working");

    fetch("/api/print-ticket", { method: "POST" })
      .then(function (resp) {
        return resp.json()
          .catch(function () { return {}; })
          .then(function (data) { return { ok: resp.ok, data: data }; });
      })
      .then(function (result) {
        var data = result.data || {};
        if (result.ok && data.ok) {
          renderConfirm(data);
        } else if (data.reason === "no_tickets") {
          showPanel("noTickets");
        } else {
          renderOffline(data.message || cfg.offlineText);
        }
      })
      .catch(function () {
        renderOffline(cfg.offlineText);
      })
      .then(function () {
        busy = false;              // runs on both success and failure
      });
  }

  // --- Status dot ----------------------------------------------------------

  function applyStatus(state, text) {
    statusEl.classList.remove("is-online", "is-warn", "is-offline");
    statusEl.classList.add(state);
    statusText.textContent = text;
  }

  function refreshStatus() {
    fetch("/api/health")
      .then(function (r) { return r.json(); })
      .then(function (h) {
        if (!h.online) {
          applyStatus("is-offline", "Offline");
        } else if (!h.tickets_available) {
          applyStatus("is-warn", "No tickets left");
        } else {
          applyStatus("is-online", "Online");
        }
      })
      .catch(function () {
        applyStatus("is-offline", "Offline");
      });
  }

  // --- Wire up -------------------------------------------------------------

  if (printButton)  { printButton.addEventListener("click", issueTicket); }
  if (nextButton)   { nextButton.addEventListener("click", toReady); }
  if (noTicketsBtn) { noTicketsBtn.addEventListener("click", toReady); }
  if (offlineRetry) { offlineRetry.addEventListener("click", issueTicket); }

  // Physical-button support: fire on the configured key(s) regardless of
  // focus. (Space/Enter are intentionally excluded in config -- they already
  // activate a focused on-screen button natively.)
  var triggerKeys = cfg.triggerKeys || [];
  if (triggerKeys.length) {
    document.addEventListener("keydown", function (e) {
      if (triggerKeys.indexOf(e.key) !== -1) {
        e.preventDefault();
        issueTicket();
      }
    });
  }

  // Initial state + status polling.
  toReady();
  refreshStatus();
  var pollSecs = Number(cfg.healthPollSeconds) || 0;
  if (pollSecs > 0) {
    setInterval(refreshStatus, pollSecs * 1000);
  }
})();
