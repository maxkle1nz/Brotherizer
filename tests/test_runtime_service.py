from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime import service


def fake_generated(*, source_text: str, mode: str, query: str, surface_mode: str, candidate_count: int):
    return {
        "source_text": source_text,
        "preferred_bucket": "casual_us_human",
        "style_signals": [{"title": "Casual US Human", "description": "test"}],
        "donor_snippets": [{"voice_bucket": "casual_us_human", "text": "sounds human"}],
        "candidates": [
            {"label": "winner", "text": "better text", "why": "best", "rerank_score": 4.2},
            {"label": "alt", "text": "alt text", "why": "alt", "rerank_score": 3.8},
        ][:candidate_count],
    }


class RuntimeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "runtime.db"
        service.RUNTIME_DB_PATH = self.db_path

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    @patch("runtime.service._run_generation", side_effect=fake_generated)
    def test_submit_rewrite_persists_job_and_candidates(self, _fake_generated) -> None:
        result = service.submit_rewrite(
            {
                "text": "hello world",
                "mode": "casual_us_human_mode",
                "surface_mode": "reply",
                "candidate_count": 2,
                "use_xai_judge": False,
            }
        )
        self.assertEqual(result["status"], "completed")
        self.assertIsNotNone(result["winner"])
        self.assertEqual(len(result["candidates"]), 2)
        self.assertNotIn("review_url", result)

        fetched = service.get_job_response(result["job_id"])
        self.assertEqual(fetched["job_id"], result["job_id"])
        self.assertEqual(fetched["winner_candidate_id"], result["winner"]["candidate_id"])
        self.assertEqual(fetched["source_text"], "hello world")

    @patch("runtime.service._run_generation", side_effect=fake_generated)
    def test_choose_candidate_updates_job(self, _fake_generated) -> None:
        result = service.submit_rewrite(
            {
                "text": "hello world",
                "mode": "casual_us_human_mode",
                "surface_mode": "reply",
                "candidate_count": 2,
                "use_xai_judge": False,
            }
        )
        alt_id = result["candidates"][1]["candidate_id"]
        choice = service.choose_candidate(
            result["job_id"],
            {
                "candidate_id": alt_id,
                "actor": {"type": "client", "id": "test"},
                "reason": "User preferred alt",
            },
        )
        self.assertEqual(choice["status"], "chosen")
        self.assertEqual(choice["chosen_candidate_id"], alt_id)

        fetched = service.get_job_response(result["job_id"])
        self.assertEqual(fetched["chosen"]["candidate_id"], alt_id)
        self.assertEqual(fetched["choice_history"][0]["reason"], "User preferred alt")

    @patch("runtime.service._run_generation", side_effect=fake_generated)
    def test_idempotency_same_request_returns_same_job(self, _fake_generated) -> None:
        payload = {
            "text": "hello world",
            "mode": "casual_us_human_mode",
            "surface_mode": "reply",
            "candidate_count": 2,
            "use_xai_judge": False,
        }
        first = service.submit_rewrite(payload, idempotency_key="abc")
        second = service.submit_rewrite(payload, idempotency_key="abc")
        self.assertEqual(first["job_id"], second["job_id"])

    @patch("runtime.service._run_generation", side_effect=fake_generated)
    def test_idempotency_conflict_raises(self, _fake_generated) -> None:
        first_payload = {
            "text": "hello world",
            "mode": "casual_us_human_mode",
            "surface_mode": "reply",
            "candidate_count": 2,
            "use_xai_judge": False,
        }
        second_payload = {
            "text": "different",
            "mode": "casual_us_human_mode",
            "surface_mode": "reply",
            "candidate_count": 2,
            "use_xai_judge": False,
        }
        service.submit_rewrite(first_payload, idempotency_key="same-key")
        with self.assertRaises(service.RuntimeApiError) as ctx:
            service.submit_rewrite(second_payload, idempotency_key="same-key")
        self.assertEqual(ctx.exception.code, "IDEMPOTENCY_KEY_REUSED")


if __name__ == "__main__":
    unittest.main()
