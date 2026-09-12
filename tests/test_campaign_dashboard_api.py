import io
import json
import os
import unittest
from datetime import date
from unittest.mock import patch

from scripts import campaign_dashboard_api as api
from scripts.campaign_state import new_campaign


NOW = "2026-09-12T10:00:00+00:00"


def identity():
    return {
        "candidate_id": "CAND_TEST", "offer_id": "OFFER_TEST", "merchant": "amazon.in",
        "asin": "B000TEST", "product_title": "Test product", "variant": "One",
        "canonical_url": "https://www.amazon.in/dp/B000TEST",
        "affiliate_url": "https://www.amazon.in/dp/B000TEST?tag=rioaffiliate-21",
        "landing_page_url": "https://example.invalid/test", "candidate_score": 90,
        "candidate_status": "READY", "selected_at": NOW, "offer_verified_at": NOW,
        "availability": "IN_STOCK", "evidence_refs": ["test"],
    }


def request(method, path, body=None, cookie=None, csrf=None):
    raw = json.dumps(body or {}).encode()
    environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "CONTENT_LENGTH": str(len(raw)),
               "wsgi.input": io.BytesIO(raw)}
    if cookie:
        environ["HTTP_COOKIE"] = cookie
    if csrf:
        environ["HTTP_X_RIO_CSRF"] = csrf
    captured = {}
    def start(status, headers):
        captured["status"], captured["headers"] = status, dict(headers)
    payload = json.loads(b"".join(api.application(environ, start)))
    return int(captured["status"].split()[0]), captured["headers"], payload


class CampaignDashboardApiTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "RIO_FOUNDER_ACCESS_TOKEN": "founder-access-token-which-is-private",
            "RIO_SESSION_SECRET": "session-secret-must-be-at-least-32-characters",
            "RIO_CSRF_SECRET": "csrf-secret-must-be-at-least-32-characters",
            "RIO_FOUNDER_ID": "Vicky Gautam",
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def login(self):
        status, headers, body = request("POST", "/api/login", {"access_token": os.environ["RIO_FOUNDER_ACCESS_TOKEN"]})
        self.assertEqual(status, 200)
        return headers["Set-Cookie"].split(";", 1)[0], body["csrf_token"]

    def test_login_uses_secure_http_only_cookie(self):
        status, headers, body = request("POST", "/api/login", {"access_token": os.environ["RIO_FOUNDER_ACCESS_TOKEN"]})
        self.assertEqual(status, 200)
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertIn("Secure", headers["Set-Cookie"])
        self.assertNotIn(os.environ["RIO_FOUNDER_ACCESS_TOKEN"], headers["Set-Cookie"])
        self.assertTrue(body["csrf_token"])

    def test_read_requires_authentication(self):
        status, _, body = request("GET", "/api/campaigns")
        self.assertEqual(status, 401)
        self.assertEqual(body["error"]["code"], "AUTH_REQUIRED")

    def test_mutation_requires_csrf(self):
        cookie, _ = self.login()
        status, _, body = request("POST", "/api/campaigns/CMP_TEST/actions",
                                  {"action": "APPROVE_FOR_CREATIVE", "expected_revision": 0,
                                   "idempotency_key": "request-1"}, cookie)
        self.assertEqual(status, 403)
        self.assertEqual(body["error"]["code"], "CSRF_REJECTED")

    def test_approval_is_founder_transition_with_revision_and_audit(self):
        cookie, csrf = self.login()
        store = {"campaign": new_campaign("CMP_TEST", identity(), at=NOW)}
        with patch.object(api, "load_campaign", side_effect=lambda _: store["campaign"]), \
             patch.object(api, "save_campaign", side_effect=lambda value: store.update(campaign=value)):
            status, _, body = request("POST", "/api/campaigns/CMP_TEST/actions",
                                      {"action": "APPROVE_FOR_CREATIVE", "expected_revision": 0,
                                       "idempotency_key": "request-1"}, cookie, csrf)
        self.assertEqual(status, 200)
        self.assertEqual(body["campaign"]["state"], "APPROVED_FOR_CREATIVE")
        event = body["campaign"]["history"][-1]
        self.assertEqual(event["actor"]["role"], "FOUNDER")
        self.assertEqual(event["details"]["request_idempotency_key"], "request-1")

    def test_idempotent_replay_does_not_advance_revision(self):
        cookie, csrf = self.login()
        campaign = new_campaign("CMP_TEST", identity(), at=NOW)
        campaign["history"].append({"action": "APPROVE_FOR_CREATIVE",
                                    "details": {"request_idempotency_key": "request-1"}})
        with patch.object(api, "load_campaign", return_value=campaign):
            status, _, body = request("POST", "/api/campaigns/CMP_TEST/actions",
                                      {"action": "APPROVE_FOR_CREATIVE", "expected_revision": 0,
                                       "idempotency_key": "request-1"}, cookie, csrf)
        self.assertEqual(status, 200)
        self.assertTrue(body["replayed"])
        self.assertEqual(body["campaign"]["revision"], 0)

    def test_candidate_ranking_is_deterministic_and_stale_offers_are_blocked(self):
        with patch.object(api, "list_campaigns", return_value=[]):
            rows = api.candidate_catalog(date(2026, 9, 12))
        self.assertGreaterEqual(len(rows), 3)
        self.assertEqual([row["score"] for row in rows], sorted((row["score"] for row in rows), reverse=True))
        self.assertTrue(all(not row["eligible"] for row in rows))
        self.assertTrue(all("FRESH_OFFER_VERIFICATION_REQUIRED" in row["blockers"] for row in rows))


if __name__ == "__main__":
    unittest.main()
