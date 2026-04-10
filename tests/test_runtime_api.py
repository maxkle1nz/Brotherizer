from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import api.brotherizer_api as api_mod
from runtime.service import RuntimeApiError


def fetch_json(url: str, method: str = "GET", body: dict | None = None) -> tuple[int, dict]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


class RuntimeApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), api_mod.BrotherizerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=2)
        self.server.server_close()

    def test_v1_health(self) -> None:
        status, payload = fetch_json(f"{self.base}/v1/health")
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["runtime"], "brotherizer-runtime")

    def test_v1_capabilities(self) -> None:
        status, payload = fetch_json(f"{self.base}/v1/capabilities")
        self.assertEqual(status, 200)
        self.assertIn("providers", payload)
        self.assertIn("limits", payload)
        self.assertIn("features", payload)

    def test_demo_route(self) -> None:
        with urllib.request.urlopen(f"{self.base}/demo") as resp:
            body = resp.read().decode("utf-8")
            self.assertEqual(resp.status, 200)
            self.assertIn("text/html", resp.headers.get("Content-Type", ""))
            self.assertIn("Brotherizer Demo", body)

    def test_demo_alias_route(self) -> None:
        with urllib.request.urlopen(f"{self.base}/demo/") as resp:
            body = resp.read().decode("utf-8")
            self.assertEqual(resp.status, 200)
            self.assertIn("Brotherizer Demo", body)

    def test_root_advertises_demo(self) -> None:
        status, payload = fetch_json(f"{self.base}/")
        self.assertEqual(status, 200)
        self.assertIn("/demo", payload["endpoints"])

    @patch("api.brotherizer_api.submit_rewrite")
    def test_v1_rewrite_error_envelope(self, mocked_submit) -> None:
        mocked_submit.side_effect = RuntimeApiError(
            "UNKNOWN_MODE",
            "Unknown mode",
            phase="request",
            retryable=False,
            status=400,
        )
        status, payload = fetch_json(
            f"{self.base}/v1/rewrite",
            method="POST",
            body={"text": "hello", "mode": "bad_mode"},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "UNKNOWN_MODE")
        self.assertEqual(payload["error"]["phase"], "request")


if __name__ == "__main__":
    unittest.main()
