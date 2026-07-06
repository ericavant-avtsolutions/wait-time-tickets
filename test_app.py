"""
test_app.py
===========
Automated tests for the ticket station. Airtable is mocked, so these run
offline and make no network calls.

Run:  python -m unittest
"""

import unittest
from unittest import mock

import app as flask_app
import airtable_client as at
import printer


class EndpointTests(unittest.TestCase):
    def setUp(self):
        flask_app.app.testing = True
        self.client = flask_app.app.test_client()

    def test_index_renders_button(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Print Next Ticket", resp.data)

    @mock.patch("app.at.claim_next_ticket")
    def test_print_ticket_success(self, mock_claim):
        mock_claim.return_value = {
            "record_id": "rec123",
            "barcode_value": "0042",
            "position_text": "Position # 0042",
        }
        resp = self.client.post("/api/print-ticket")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["barcode_value"], "0042")
        self.assertEqual(data["position_text"], "Position # 0042")

    @mock.patch("app.at.claim_next_ticket", side_effect=at.NoTicketsAvailable)
    def test_print_ticket_no_tickets(self, _):
        resp = self.client.post("/api/print-ticket")
        self.assertEqual(resp.status_code, 409)
        data = resp.get_json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["reason"], "no_tickets")

    @mock.patch("app.at.claim_next_ticket", side_effect=at.AirtableError("boom"))
    def test_print_ticket_airtable_error(self, _):
        resp = self.client.post("/api/print-ticket")
        self.assertEqual(resp.status_code, 503)
        data = resp.get_json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["reason"], "offline")

    @mock.patch("app.at.claim_next_ticket", side_effect=at.TokenNotConfigured("no token"))
    def test_print_ticket_not_configured(self, _):
        resp = self.client.post("/api/print-ticket")
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.get_json()["reason"], "not_configured")

    @mock.patch("app.at.claim_next_ticket",
                side_effect=printer.PrinterError("printer down"))
    def test_print_ticket_printer_error(self, _):
        resp = self.client.post("/api/print-ticket")
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.get_json()["reason"], "printer_error")

    @mock.patch("app.at.check_health")
    def test_health(self, mock_health):
        mock_health.return_value = {
            "online": True, "tickets_available": True, "detail": "",
        }
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["online"])


class ClaimLogicTests(unittest.TestCase):
    @mock.patch("airtable_client.mark_ticket_printed")
    @mock.patch("airtable_client.get_next_available_ticket")
    def test_claim_marks_printed_and_returns_values(self, mock_get, mock_mark):
        mock_get.return_value = {
            "id": "rec9",
            "fields": {"Barcode Value": "0001", "Barcode Text": "Position # 0001"},
        }
        mock_mark.return_value = {"id": "rec9", "fields": {}}

        result = at.claim_next_ticket()

        mock_mark.assert_called_once_with("rec9")
        self.assertEqual(result["record_id"], "rec9")
        self.assertEqual(result["barcode_value"], "0001")
        self.assertEqual(result["position_text"], "Position # 0001")

    @mock.patch("airtable_client.get_next_available_ticket", return_value=None)
    def test_claim_raises_when_empty(self, _):
        with self.assertRaises(at.NoTicketsAvailable):
            at.claim_next_ticket()

    @mock.patch("airtable_client.mark_ticket_printed")
    @mock.patch("airtable_client.get_next_available_ticket")
    def test_before_mark_runs_before_marking(self, mock_get, mock_mark):
        mock_get.return_value = {"id": "rec9", "fields": {"Barcode Value": "0007"}}
        order = []
        mock_mark.side_effect = lambda rid: order.append("mark:" + rid)
        at.claim_next_ticket(before_mark=lambda v: order.append("print:" + v))
        self.assertEqual(order, ["print:0007", "mark:rec9"])

    @mock.patch("airtable_client.mark_ticket_printed")
    @mock.patch("airtable_client.get_next_available_ticket")
    def test_before_mark_failure_is_fail_closed(self, mock_get, mock_mark):
        mock_get.return_value = {"id": "rec9", "fields": {"Barcode Value": "0007"}}

        def boom(_value):
            raise printer.PrinterError("printer down")

        with self.assertRaises(printer.PrinterError):
            at.claim_next_ticket(before_mark=boom)
        mock_mark.assert_not_called()   # ticket must NOT be marked if print fails

    @mock.patch("airtable_client.mark_ticket_printed",
                side_effect=at.AirtableError("write failed"))
    @mock.patch("airtable_client.get_next_available_ticket")
    def test_claim_fails_closed_when_write_fails(self, mock_get, _):
        # If the "mark printed" write fails, claim must raise (no number is
        # returned for a ticket we could not reserve).
        mock_get.return_value = {"id": "rec9", "fields": {"Barcode Value": "0001"}}
        with self.assertRaises(at.AirtableError):
            at.claim_next_ticket()


class FormulaTests(unittest.TestCase):
    def test_unprinted_formula_without_image(self):
        with mock.patch.object(at.config, "REQUIRE_BARCODE_IMAGE", False):
            self.assertEqual(at._unprinted_formula(), "NOT({Ticket Printed})")

    def test_unprinted_formula_with_image(self):
        with mock.patch.object(at.config, "REQUIRE_BARCODE_IMAGE", True):
            self.assertEqual(
                at._unprinted_formula(),
                "AND(NOT({Ticket Printed}), {Barcode Image})",
            )


if __name__ == "__main__":
    unittest.main()
