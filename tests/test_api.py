import unittest
from fastapi.testclient import TestClient
from app.main import app
from scripts.verify_dns import make_dns_query, _recv_exact
from scripts.prepare_deployment import build_user_data, BASE_DIR

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
        self.assertIn("flushed_at", data)
        self.assertIsInstance(data["flushed_at"], float)

    def test_telegram_test_preview(self):
        res = self.client.post("/api/telegram/test", json={"preview_only": True})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("preview", data)
        self.assertIn("Lighthouse", data["preview"])

    def test_toggle_protection_with_timer(self):
        res = self.client.post("/api/toggle", json={"enable": False, "duration": 300})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))

    def test_queries_search_filter(self):
        res = self.client.get("/api/queries?limit=25&filter_type=all&search=google")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("queries", data)

    def test_dns_query_wire_format(self):
        wire = make_dns_query("example.com")
        self.assertGreater(len(wire), 12)
        # Check header transaction ID (0x1234)
        self.assertEqual(wire[0], 0x12)
        self.assertEqual(wire[1], 0x34)

    def test_queries_validation_boundaries(self):
        # Limit below minimum (ge=1)
        res_low = self.client.get("/api/queries?limit=0")
        self.assertEqual(res_low.status_code, 422)

        # Limit above maximum (le=200)
        res_high = self.client.get("/api/queries?limit=250")
        self.assertEqual(res_high.status_code, 422)

        # Invalid filter_type pattern
        res_invalid_filter = self.client.get("/api/queries?filter_type=invalid_filter")
        self.assertEqual(res_invalid_filter.status_code, 422)

        # Search query exceeding 100 characters
        res_long_search = self.client.get(f"/api/queries?search={'a'*105}")
        self.assertEqual(res_long_search.status_code, 422)

    def test_rules_whitespace_validation(self):
        res = self.client.post("/api/rules", json={"domain": "   ", "list_type": "blocked"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.json())

    def test_rules_regex_addition(self):
        res = self.client.post("/api/rules", json={
            "domain": "^telemetry.*\\.local$",
            "list_type": "blocked",
            "rule_type": "regex",
            "comment": "Regex unit test"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["rule"]["type"], "regex")

        # Clean up
        res_del = self.client.request("DELETE", "/api/rules", json={
            "domain": "^telemetry.*\\.local$",
            "list_type": "blocked"
        })
        self.assertEqual(res_del.status_code, 200)

    def test_recv_exact_tcp_fragmentation(self):
        class MockFragmentedSocket:
            def __init__(self, data: bytes, chunk_size: int = 1):
                self.data = data
                self.chunk_size = chunk_size
                self.offset = 0

            def recv(self, num_bytes: int):
                if self.offset >= len(self.data):
                    return b""
                end = min(self.offset + min(num_bytes, self.chunk_size), len(self.data))
                chunk = self.data[self.offset:end]
                self.offset = end
                return chunk

        raw_payload = b"\x00\x2a\x12\x34\x56\x78\x9a\xbc\xde\xf0"
        # Each recv call will return only 1 byte
        mock_sock = MockFragmentedSocket(raw_payload, chunk_size=1)
        # Read exact 10 bytes across 10 fragmented reads
        result = _recv_exact(mock_sock, 10)
        self.assertEqual(result, raw_payload)

        # Test socket closure / EOF
        mock_eof_sock = MockFragmentedSocket(b"\x01\x02", chunk_size=1)
        incomplete = _recv_exact(mock_eof_sock, 5)
        self.assertEqual(incomplete, b"\x01\x02")

    def test_dns_query_wire_multi_label(self):
        wire = make_dns_query("sub.domain.deep.example.com", qtype=28) # AAAA query
        self.assertGreater(len(wire), 20)
        # Check QTYPE is 28 (0x001c)
        self.assertEqual(wire[-4:], b"\x00\x1c\x00\x01")


if __name__ == "__main__":
    unittest.main()
