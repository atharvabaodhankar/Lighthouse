import unittest
from starlette.testclient import TestClient
from app.main import app

class TestLighthouseAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("app"), "Lighthouse")

    def test_index_page(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.headers.get("content-type", ""))
        self.assertIn("Lighthouse", res.text)
        self.assertIn("DNS for your home", res.text)

    def test_summary_api(self):
        res = self.client.get("/api/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("status", data)
        self.assertIn("dns_queries_today", data)
        self.assertIn("ads_blocked_today", data)
        self.assertIn("domains_being_blocked", data)

    def test_chart_api(self):
        res = self.client.get("/api/chart")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("labels", data)
        self.assertIn("total_queries", data)
        self.assertIn("blocked_queries", data)
        self.assertEqual(len(data["labels"]), len(data["total_queries"]))

    def test_top_items_api(self):
        res = self.client.get("/api/top-items")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("top_queries", data)
        self.assertIn("top_ads", data)
        self.assertIn("query_types", data)

    def test_clients_api(self):
        res = self.client.get("/api/clients")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("clients", data)
        self.assertIsInstance(data["clients"], list)

    def test_queries_api(self):
        # All queries
        res = self.client.get("/api/queries?limit=10&filter_type=all")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("queries", data)

        # Blocked queries
        res_blocked = self.client.get("/api/queries?limit=10&filter_type=blocked")
        self.assertEqual(res_blocked.status_code, 200)

        # Permitted queries
        res_permitted = self.client.get("/api/queries?limit=10&filter_type=permitted")
        self.assertEqual(res_permitted.status_code, 200)

    def test_rules_api(self):
        # GET rules
        res = self.client.get("/api/rules")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("blocked", data)
        self.assertIn("allowed", data)

        # POST rule validation
        res_invalid = self.client.post("/api/rules", json={"domain": ""})
        self.assertEqual(res_invalid.status_code, 400)

        # POST rule valid
        res_add = self.client.post("/api/rules", json={
            "domain": "telemetry-test-unit.example.com",
            "list_type": "blocked",
            "rule_type": "exact",
            "comment": "Unit test rule"
        })
        self.assertEqual(res_add.status_code, 200)
        self.assertTrue(res_add.json().get("success"))

        # DELETE rule
        res_del = self.client.request("DELETE", "/api/rules", json={
            "domain": "telemetry-test-unit.example.com",
            "list_type": "blocked"
        })
        self.assertEqual(res_del.status_code, 200)
        self.assertTrue(res_del.json().get("success"))

    def test_toggle_protection_api(self):
        res = self.client.post("/api/toggle", json={"enable": True, "duration": 0})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))

    def test_logs_flush_api(self):
        res = self.client.post("/api/logs/flush")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("success", data)
        self.assertIn("message", data)

    def test_telegram_test_preview(self):
        res = self.client.post("/api/telegram/test", json={"preview_only": True})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("preview", data)
        self.assertIn("Lighthouse", data["preview"])

if __name__ == "__main__":
    unittest.main()
