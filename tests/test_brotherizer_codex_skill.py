from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "brotherizer-codex-runtime" / "scripts" / "brotherizer_codex.py"


def run_helper(*args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(proc.stdout)


class BrotherizerCodexSkillTests(unittest.TestCase):
    def test_doctor_reports_codex_native_runtime(self) -> None:
        payload = run_helper("doctor", "--root", str(ROOT))

        self.assertTrue(payload["ok"])
        self.assertTrue(payload["codex_native_generation"])
        self.assertFalse(payload["requires_perplexity_api_key"])
        self.assertIn("en_professional_human_mode", payload["modes"])

    def test_payload_uses_local_donor_pack_without_perplexity(self) -> None:
        payload = run_helper(
            "payload",
            "--root",
            str(ROOT),
            "--mode",
            "en_professional_human_mode",
            "--surface-mode",
            "bio",
            "--text",
            "I build AI-native tools and creative systems.",
        )

        self.assertEqual(payload["source_text"], "I build AI-native tools and creative systems.")
        self.assertEqual(payload["mode_profile"], "seriously")
        self.assertEqual(payload["surface_mode"], "bio")
        self.assertEqual(payload["_codex_runtime"]["generator"], "codex")
        self.assertGreaterEqual(len(payload["donor_snippets"]), 1)

    def test_rerank_accepts_codex_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            payload_path = tmp / "payload.json"
            candidates_path = tmp / "candidates.json"

            payload = run_helper(
                "payload",
                "--root",
                str(ROOT),
                "--mode",
                "casual_us_human_mode",
                "--surface-mode",
                "reply",
                "--text",
                "This still sounds too polished and generic.",
            )
            payload_path.write_text(json.dumps(payload, ensure_ascii=False) + "\n")
            candidates_path.write_text(
                json.dumps(
                    {
                        "candidates": [
                            {
                                "label": "codex-a",
                                "text": "Yeah, this still sounds a bit too clean.",
                                "why": "Short and reply-like.",
                            },
                            {
                                "label": "codex-b",
                                "text": "It is polished, but in that off-the-shelf way.",
                                "why": "Keeps the complaint but changes the rhythm.",
                            },
                        ]
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

            ranked = run_helper(
                "rerank",
                "--root",
                str(ROOT),
                "--payload",
                str(payload_path),
                "--candidates",
                str(candidates_path),
            )

        self.assertIn("winner", ranked)
        self.assertIsNotNone(ranked["winner"])
        self.assertEqual(len(ranked["candidates"]), 2)
        self.assertIn("rerank_score", ranked["winner"])
        self.assertEqual(ranked["_codex_runtime"]["reranker"], "brotherizer-local-heuristic")


if __name__ == "__main__":
    unittest.main()
