#!/usr/bin/env python3
"""Brotherizer HTTP API."""

from __future__ import annotations

import json
import mimetypes
import os
import re
import sys
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
UI_ROOT = ROOT / "ui"
WORKSPACE_DB_PATH = ROOT / "data" / "app" / "workspace.db"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "storage"))
sys.path.insert(0, str(ROOT / "runtime"))

from runtime.service import (  # noqa: E402
    RuntimeApiError,
    capabilities_payload,
    choose_candidate,
    get_job_response,
    modes_payload,
    submit_rewrite,
)
from workspace_db import (  # noqa: E402
    connect as connect_workspace_db,
    insert_file,
    insert_saved_output,
    insert_session,
    list_workspace,
    update_file,
)

REVIEW_PATH_RE = re.compile(r"^/review/([^/]+)$")
V1_JOB_PATH_RE = re.compile(r"^/v1/jobs/([^/]+)$")
V1_CHOOSE_PATH_RE = re.compile(r"^/v1/jobs/([^/]+)/choose$")


def json_response(status: int, payload: dict) -> tuple[bytes, str]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return body, "application/json; charset=utf-8"


def static_response(path: Path) -> tuple[bytes, str]:
    body = path.read_bytes()
    content_type, _ = mimetypes.guess_type(str(path))
    return body, content_type or "application/octet-stream"


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
        "review_url": job_result.get("review_url"),
    }


class BrotherizerHandler(BaseHTTPRequestHandler):
    server_version = "BrotherizerHTTP/1.0"

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: dict) -> None:
        body, content_type = json_response(status, payload)
        self._send(status, body, content_type)

    def _serve_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})
            return
        body, content_type = static_response(path)
        self._send(HTTPStatus.OK, body, content_type)

    def _with_absolute_review_url(self, payload: dict) -> dict:
        review_url = payload.get("review_url")
        if not review_url or not isinstance(review_url, str) or review_url.startswith("http"):
            return payload
        host = self.headers.get("Host") or f"127.0.0.1:{os.environ.get('BROTHERIZER_PORT', '5555')}"
        enriched = dict(payload)
        enriched["review_url"] = f"http://{host}{review_url}"
        return enriched

    def _runtime_error(self, exc: RuntimeApiError) -> None:
        self._json(exc.status, exc.to_payload())

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        if path == "/health":
            self._json(HTTPStatus.OK, {"ok": True, "service": "brotherizer", "version": "1.0.0"})
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
            )
            return
        if path == "/modes":
            self._json(HTTPStatus.OK, json.loads((ROOT / "configs" / "brotherizer_modes.json").read_text()))
            return
        if path == "/v1/modes":
            self._json(HTTPStatus.OK, modes_payload())
            return
        if path == "/v1/capabilities":
            self._json(HTTPStatus.OK, capabilities_payload())
            return
        if path == "/workspace":
            conn = connect_workspace_db(WORKSPACE_DB_PATH)
            self._json(HTTPStatus.OK, {"ok": True, **list_workspace(conn)})
            return
        job_match = V1_JOB_PATH_RE.match(path)
        if job_match:
            try:
                self._json(HTTPStatus.OK, self._with_absolute_review_url(get_job_response(job_match.group(1))))
            except RuntimeApiError as exc:
                self._runtime_error(exc)
            return
        review_match = REVIEW_PATH_RE.match(path)
        if review_match:
            self._serve_file(UI_ROOT / "review.html")
            return
        if path == "/onboarding":
            self._serve_file(UI_ROOT / "onboarding.html")
            return
        if path == "/":
            self._serve_file(UI_ROOT / "index.html")
            return
        if path.startswith("/ui/"):
            relative = path.removeprefix("/ui/")
            self._serve_file(UI_ROOT / relative)
            return
        self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            payload = self._read_json_body()
        except Exception:
            self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "invalid_json"})
            return

        if path == "/sessions":
            session_id = payload.get("id", "")
            name = payload.get("name", "").strip()
            created_at = payload.get("createdAt", "")
            if not session_id or not name or not created_at:
                self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "missing_session_fields"})
                return
            conn = connect_workspace_db(WORKSPACE_DB_PATH)
            insert_session(conn, session_id=session_id, name=name, created_at=created_at)
            self._json(HTTPStatus.OK, {"ok": True})
            return

        if path == "/files":
            file_id = payload.get("id", "")
            session_id = payload.get("sessionId", "")
            name = payload.get("name", "").strip()
            text = payload.get("text", "")
            mode = payload.get("mode", "")
            created_at = payload.get("createdAt", "")
            updated_at = payload.get("updatedAt", created_at)
            if not file_id or not session_id or not name or not created_at:
                self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "missing_file_fields"})
                return
            conn = connect_workspace_db(WORKSPACE_DB_PATH)
            insert_file(
                conn,
                file_id=file_id,
                session_id=session_id,
                name=name,
                text=text,
                mode=mode,
                created_at=created_at,
                updated_at=updated_at,
            )
            self._json(HTTPStatus.OK, {"ok": True})
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
                        "ui_mode": payload.get("ui_mode", "off"),
                        "use_xai_judge": bool(payload.get("use_xai_judge", False)),
                    },
                    idempotency_key=self.headers.get("Idempotency-Key"),
                )
            except RuntimeApiError as exc:
                self._json(exc.status, {"ok": False, "error": exc.code, "message": exc.message})
                return
            self._json(HTTPStatus.OK, self._with_absolute_review_url(legacy_rewrite_payload(result)))
            return

        if path == "/v1/rewrite":
            try:
                result = submit_rewrite(payload, idempotency_key=self.headers.get("Idempotency-Key"))
                self._json(HTTPStatus.OK, self._with_absolute_review_url(result))
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

        if path.startswith("/files/") and path.endswith("/saved-outputs"):
            file_id = path.split("/")[2]
            output_id = payload.get("id", "")
            saved_at = payload.get("savedAt", "")
            mode = payload.get("mode", "")
            label = payload.get("label", "")
            text = payload.get("text", "")
            why = payload.get("why", "")
            if not file_id or not output_id or not saved_at:
                self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "missing_saved_output_fields"})
                return
            conn = connect_workspace_db(WORKSPACE_DB_PATH)
            insert_saved_output(
                conn,
                output_id=output_id,
                file_id=file_id,
                saved_at=saved_at,
                mode=mode,
                label=label,
                text=text,
                why=why,
            )
            self._json(HTTPStatus.OK, {"ok": True})
            return

        self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})

    def do_PATCH(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            payload = self._read_json_body()
        except Exception:
            self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "invalid_json"})
            return

        if not path.startswith("/files/"):
            self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})
            return

        file_id = path.split("/")[2]
        conn = connect_workspace_db(WORKSPACE_DB_PATH)
        updated = update_file(
            conn,
            file_id=file_id,
            name=payload.get("name", "Untitled"),
            text=payload.get("text", ""),
            mode=payload.get("mode", ""),
            updated_at=payload.get("updatedAt", ""),
        )
        if not updated:
            self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "file_not_found"})
            return
        self._json(HTTPStatus.OK, {"ok": True})


def recover_inflight_jobs() -> None:
    from storage.runtime_db import connect as connect_runtime_db  # noqa: E402
    from storage.runtime_db import create_runtime_error, update_job_state  # noqa: E402
    from runtime.runtime_ids import make_runtime_id  # noqa: E402

    conn = connect_runtime_db(ROOT / "data" / "runtime" / "brotherizer_runtime.db")
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


def main() -> int:
    host = os.environ.get("BROTHERIZER_HOST", "127.0.0.1")
    port = int(os.environ.get("BROTHERIZER_PORT", "8787"))
    recover_inflight_jobs()
    server = ThreadingHTTPServer((host, port), BrotherizerHandler)
    print(json.dumps({"ok": True, "host": host, "port": port}))
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
