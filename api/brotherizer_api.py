#!/usr/bin/env python3
"""Brotherizer HTTP API."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runtime"))

from runtime.service import (  # noqa: E402
    RuntimeApiError,
    capabilities_payload,
    choose_candidate,
    get_job_response,
    modes_payload,
    submit_rewrite,
)
from runtime.paths import resource_path, writable_path  # noqa: E402
V1_JOB_PATH_RE = re.compile(r"^/v1/jobs/([^/]+)$")
V1_CHOOSE_PATH_RE = re.compile(r"^/v1/jobs/([^/]+)/choose$")
DEMO_PATHS = {"/demo", "/demo/"}


def json_response(status: int, payload: dict) -> tuple[bytes, str]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return body, "application/json; charset=utf-8"


def html_response(path: Path) -> tuple[bytes, str]:
    return path.read_bytes(), "text/html; charset=utf-8"


def legacy_rewrite_payload(job_result: dict) -> dict:
    return {
        "job_id": job_result["job_id"],
        "source_text": job_result.get("source_text", ""),
        "surface_mode": job_result.get("request", {}).get("surface_mode", ""),
        "candidates": [
            {
                "label": item.get("label", ""),
                "text": item.get("text", ""),
                "why": item.get("why", ""),
                "rerank_score": item.get("score", 0),
                "diagnostics": item.get("diagnostics", {}),
                "candidate_id": item.get("candidate_id", ""),
            }
            for item in job_result.get("candidates", [])
        ],
        "winner": (
            {
                "label": job_result["winner"].get("label", ""),
                "text": job_result["winner"].get("text", ""),
                "why": job_result["winner"].get("why", ""),
                "rerank_score": job_result["winner"].get("score", 0),
                "diagnostics": job_result["winner"].get("diagnostics", {}),
                "candidate_id": job_result["winner"].get("candidate_id", ""),
            }
            if job_result.get("winner")
            else None
        ),
        "donor_snippets": job_result.get("donor_snippets", []),
        "style_signals": job_result.get("style_signals", []),
    }


class BrotherizerHandler(BaseHTTPRequestHandler):
    server_version = "BrotherizerHTTP/1.0"

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _send(self, status: int, body: bytes, content_type: str, *, head_only: bool = False) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def _json(self, status: int, payload: dict, *, head_only: bool = False) -> None:
        body, content_type = json_response(status, payload)
        self._send(status, body, content_type, head_only=head_only)

    def _html(self, status: int, path: Path, *, head_only: bool = False) -> None:
        body, content_type = html_response(path)
        self._send(status, body, content_type, head_only=head_only)

    def _runtime_error(self, exc: RuntimeApiError, *, head_only: bool = False) -> None:
        self._json(exc.status, exc.to_payload(), head_only=head_only)

    def _handle_get(self, *, head_only: bool = False) -> None:
        path = urlparse(self.path).path

        if path == "/health":
            self._json(HTTPStatus.OK, {"ok": True, "service": "brotherizer", "version": "1.0.0"}, head_only=head_only)
            return
        if path == "/v1/health":
            self._json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "version": "1.0.0",
                    "runtime": "brotherizer-runtime",
                    "time": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                },
                head_only=head_only,
            )
            return
        if path == "/modes":
            self._json(HTTPStatus.OK, json.loads(resource_path("configs", "brotherizer_modes.json").read_text()), head_only=head_only)
            return
        if path == "/v1/modes":
            self._json(HTTPStatus.OK, modes_payload(), head_only=head_only)
            return
        if path == "/v1/capabilities":
            self._json(HTTPStatus.OK, capabilities_payload(), head_only=head_only)
            return
        if path in DEMO_PATHS:
            self._html(HTTPStatus.OK, resource_path("demo", "index.html"), head_only=head_only)
            return
        job_match = V1_JOB_PATH_RE.match(path)
        if job_match:
            try:
                self._json(HTTPStatus.OK, get_job_response(job_match.group(1)), head_only=head_only)
            except RuntimeApiError as exc:
                self._runtime_error(exc, head_only=head_only)
            return
        if path == "/":
            self._json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "service": "brotherizer",
                    "api": "v1",
                    "endpoints": [
                        "/v1/health",
                        "/v1/modes",
                        "/v1/capabilities",
                        "/v1/rewrite",
                        "/v1/jobs/:id",
                        "/v1/jobs/:id/choose",
                        "/demo",
                        "/health",
                        "/modes",
                        "/rewrite",
                    ],
                },
                head_only=head_only,
            )
            return
        self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"}, head_only=head_only)

    def do_GET(self) -> None:  # noqa: N802
        self._handle_get(head_only=False)

    def do_HEAD(self) -> None:  # noqa: N802
        self._handle_get(head_only=True)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            payload = self._read_json_body()
        except Exception:
            self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "invalid_json"})
            return

        if path == "/rewrite":
            try:
                result = submit_rewrite(
                    {
                        "text": payload.get("text", ""),
                        "mode": payload.get("mode", ""),
                        "surface_mode": payload.get("surface_mode", ""),
                        "query": payload.get("query", ""),
                        "candidate_count": int(payload.get("candidate_count", 3)),
                        "use_xai_judge": bool(payload.get("use_xai_judge", False)),
                    },
                    idempotency_key=self.headers.get("Idempotency-Key"),
                )
            except RuntimeApiError as exc:
                self._json(exc.status, {"ok": False, "error": exc.code, "message": exc.message})
                return
            self._json(HTTPStatus.OK, legacy_rewrite_payload(result))
            return

        if path == "/v1/rewrite":
            try:
                result = submit_rewrite(payload, idempotency_key=self.headers.get("Idempotency-Key"))
                self._json(HTTPStatus.OK, result)
            except RuntimeApiError as exc:
                self._runtime_error(exc)
            return

        choose_match = V1_CHOOSE_PATH_RE.match(path)
        if choose_match:
            try:
                result = choose_candidate(choose_match.group(1), payload)
                self._json(HTTPStatus.OK, result)
            except RuntimeApiError as exc:
                self._runtime_error(exc)
            return

        self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})


def recover_inflight_jobs() -> None:
    from storage.runtime_db import connect as connect_runtime_db  # noqa: E402
    from storage.runtime_db import create_runtime_error, update_job_state  # noqa: E402
    from runtime.runtime_ids import make_runtime_id  # noqa: E402

    conn = connect_runtime_db(writable_path("data", "runtime", "brotherizer_runtime.db"))
    rows = conn.execute(
        "SELECT id FROM jobs WHERE status IN ('accepted','generating','reranking','judging')"
    ).fetchall()
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for row in rows:
        create_runtime_error(
            conn,
            error={
                "id": make_runtime_id("bre"),
                "job_id": row["id"],
                "phase": "runtime",
                "code": "RUNTIME_RESTARTED_IN_FLIGHT",
                "message": "Runtime restarted while job was in flight.",
                "details": {},
                "created_at": timestamp,
            },
        )
        update_job_state(
            conn,
            job_id=row["id"],
            status="failed",
            updated_at=timestamp,
            failed_at=timestamp,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Brotherizer HTTP API.")
    parser.add_argument("--host", default=os.environ.get("BROTHERIZER_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("BROTHERIZER_PORT", "5555")))
    args = parser.parse_args(argv)

    host = args.host
    port = args.port
    recover_inflight_jobs()
    server = ThreadingHTTPServer((host, port), BrotherizerHandler)
    print(json.dumps({"ok": True, "host": host, "port": port}))
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
