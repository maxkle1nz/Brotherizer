#!/usr/bin/env python3
"""Brotherizer runtime orchestration service."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "storage"))
sys.path.insert(0, str(ROOT / "rewrite"))
sys.path.insert(0, str(ROOT / "runtime"))

from runtime.runtime_ids import make_runtime_id  # noqa: E402
from storage.runtime_db import (  # noqa: E402
    connect as connect_runtime_db,
    create_choice,
    create_idempotency_record,
    create_job,
    create_runtime_error,
    get_idempotency_record,
    get_job,
    list_candidates,
    list_choices,
    list_runtime_errors,
    replace_candidates,
    update_job_state,
)
from rewrite_reranker import DEFAULT_XAI_MODEL, heuristic_rerank, merge_xai_scores, run_xai_judge_scores  # noqa: E402
from runtime.paths import resource_path, writable_path  # noqa: E402

RUNTIME_DB_PATH = writable_path("data", "runtime", "brotherizer_runtime.db")
MODES_PATH = resource_path("configs", "brotherizer_modes.json")
TMP_ROOT = Path(os.environ.get("BROTHERIZER_TMPDIR", writable_path(".omx", "state", "tmp")))

MAX_INPUT_CHARS = int(os.environ.get("BROTHERIZER_MAX_INPUT_CHARS", "120000"))
MAX_CANDIDATE_COUNT = int(os.environ.get("BROTHERIZER_MAX_CANDIDATE_COUNT", "8"))
GENERATION_PROVIDER = "perplexity"
GENERATION_MODEL = os.environ.get("BROTHERIZER_GENERATION_MODEL", "sonar")
JUDGE_PROVIDER = "xai"


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_tempdir():
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=TMP_ROOT)


def request_hash(data: dict[str, Any]) -> str:
    rendered = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


@dataclass
class RuntimeApiError(Exception):
    code: str
    message: str
    phase: str = "runtime"
    retryable: bool = False
    details: dict[str, Any] | None = None
    status: int = 400

    def to_payload(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "phase": self.phase,
                "retryable": self.retryable,
                "details": self.details or {},
            }
        }


def connect_runtime():
    return connect_runtime_db(RUNTIME_DB_PATH)


def judge_enabled() -> bool:
    return bool(os.environ.get("XAI_API_KEY", "").strip())


def active_judge_model() -> str:
    return os.environ.get("BROTHERIZER_XAI_MODEL", DEFAULT_XAI_MODEL)


def load_modes() -> dict[str, Any]:
    return json.loads(MODES_PATH.read_text())


def slug_to_label(slug: str) -> str:
    base = slug.removesuffix("_mode").replace("_", " ").strip()
    return " ".join(part.upper() if part in {"us", "uk", "ptbr"} else part.capitalize() for part in base.split())


def infer_surfaces(mode_slug: str, cfg: dict[str, Any]) -> list[str]:
    bucket = cfg.get("bucket", "")
    profile = cfg.get("profile", "default")
    if "casual_us_human" in bucket or "british_banter" in bucket or "worldwide_ironic" in bucket or "ptbr_casual" in bucket or "ptbr_ironic" in bucket:
        return ["reply", "post", "caption"]
    if "professional" in bucket:
        return ["bio", "note", "post"]
    if profile == "narrative" or "reflective" in bucket:
        return ["note", "post"]
    return ["reply", "post", "note"]


def capabilities_payload() -> dict[str, Any]:
    return {
        "providers": {
            "generation": {"name": GENERATION_PROVIDER, "model": GENERATION_MODEL},
            "judge": {
                "enabled": judge_enabled(),
                "name": JUDGE_PROVIDER,
                "model": active_judge_model(),
            },
        },
        "limits": {
            "max_input_chars": MAX_INPUT_CHARS,
            "max_candidate_count": MAX_CANDIDATE_COUNT,
            "supports_document_rewrite": False,
        },
        "features": {
            "surface_mode": True,
            "choose_candidate": True,
            "streaming": False,
        },
    }


def modes_payload() -> dict[str, Any]:
    modes = []
    for slug, cfg in load_modes().items():
        modes.append(
            {
                "slug": slug,
                "label": slug_to_label(slug),
                "surfaces": infer_surfaces(slug, cfg),
            }
        )
    return {"modes": modes}


def normalize_rewrite_request(payload: dict[str, Any]) -> dict[str, Any]:
    text = str(payload.get("text", "") or "")
    if not text.strip():
        raise RuntimeApiError("MISSING_TEXT", "Field `text` is required.", phase="request", status=400)
    if len(text) > MAX_INPUT_CHARS:
        raise RuntimeApiError(
            "INPUT_TOO_LARGE",
            f"Input exceeds max_input_chars={MAX_INPUT_CHARS}.",
            phase="request",
            status=413,
            details={"max_input_chars": MAX_INPUT_CHARS},
        )

    mode = str(payload.get("mode", "") or "")
    if not mode:
        raise RuntimeApiError("MISSING_MODE", "Field `mode` is required.", phase="request", status=400)

    modes = load_modes()
    if mode not in modes:
        raise RuntimeApiError("UNKNOWN_MODE", f"Unknown mode `{mode}`.", phase="request", status=400)

    candidate_count = int(payload.get("candidate_count", 3))
    if candidate_count < 1 or candidate_count > MAX_CANDIDATE_COUNT:
        raise RuntimeApiError(
            "INVALID_CANDIDATE_COUNT",
            f"`candidate_count` must be between 1 and {MAX_CANDIDATE_COUNT}.",
            phase="request",
            status=400,
        )

    return {
        "text": text,
        "mode": mode,
        "surface_mode": str(payload.get("surface_mode", "") or ""),
        "query": str(payload.get("query", "") or ""),
        "candidate_count": candidate_count,
        "use_xai_judge": bool(payload.get("use_xai_judge", judge_enabled())),
        "client": payload.get("client") or {},
    }


def _run_generation(
    *,
    source_text: str,
    mode: str,
    query: str,
    surface_mode: str,
    candidate_count: int,
) -> dict[str, Any]:
    env = dict(os.environ)
    if not env.get("PERPLEXITY_API_KEY", "").strip():
        raise RuntimeApiError("MISSING_PERPLEXITY_KEY", "Missing PERPLEXITY_API_KEY.", phase="generating", status=500)

    with make_tempdir() as tmpdir:
        rewrite_path = Path(tmpdir) / "rewrite.json"

        import subprocess

        executor_cmd = [
            sys.executable,
            str(ROOT / "rewrite" / "rewrite_executor.py"),
            "--mode",
            mode,
            "--source-text",
            source_text,
            "--query",
            query or mode,
            "--surface-mode",
            surface_mode,
            "--candidate-count",
            str(candidate_count),
            "--model",
            GENERATION_MODEL,
            "--out",
            str(rewrite_path),
        ]
        subprocess.run(executor_cmd, check=True, capture_output=True, text=True, env=env)
        return json.loads(rewrite_path.read_text())


def _candidate_record(job_id: str, idx: int, item: dict[str, Any], generated: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": make_runtime_id("brc"),
        "job_id": job_id,
        "rank": idx + 1,
        "label": item.get("label", f"candidate-{idx+1}"),
        "text": item.get("text", ""),
        "score": float(item.get("rerank_score", 0)),
        "why": item.get("why", ""),
        "diagnostics": {
            "composition_penalty": item.get("composition_penalty", 0),
            "composition_matches": item.get("composition_matches", []),
            "xai_judge_score": item.get("xai_judge_score"),
        },
        "donor_snippets": generated.get("donor_snippets", []),
        "style_signals": generated.get("style_signals", []),
        "is_winner": idx == 0,
    }


def _job_response(conn, job_id: str) -> dict[str, Any]:
    job = get_job(conn, job_id=job_id)
    if not job:
        raise RuntimeApiError("JOB_NOT_FOUND", f"Job `{job_id}` not found.", phase="runtime", status=404)
    candidates = list_candidates(conn, job_id=job_id)
    choices = list_choices(conn, job_id=job_id)
    runtime_errors = list_runtime_errors(conn, job_id=job_id)

    serialized_candidates = []
    winner = None
    chosen = None
    top_donor_snippets: list[dict[str, Any]] = []
    top_style_signals: list[dict[str, Any]] = []
    for row in candidates:
        donor_snippets = json.loads(row["donor_snippets_json"] or "[]")
        style_signals = json.loads(row["style_signals_json"] or "[]")
        if not top_donor_snippets and donor_snippets:
            top_donor_snippets = donor_snippets
        if not top_style_signals and style_signals:
            top_style_signals = style_signals
        item = {
            "candidate_id": row["id"],
            "rank": row["rank"],
            "label": row["label"],
            "text": row["text"],
            "score": row["score"],
            "why": row["why"],
            "diagnostics": json.loads(row["diagnostics_json"] or "{}"),
            "donor_snippets": donor_snippets,
            "style_signals": style_signals,
        }
        serialized_candidates.append(item)
        if row["id"] == job["winner_candidate_id"]:
            winner = item
        if row["id"] == job["chosen_candidate_id"]:
            chosen = item

    return {
        "job_id": job["id"],
        "status": job["status"],
        "source_text": job["source_text"],
        "request": {
            "mode": job["mode"],
            "surface_mode": job["surface_mode"],
            "query": job["query"],
            "candidate_count": job["candidate_count"],
        },
        "winner_candidate_id": job["winner_candidate_id"],
        "chosen_candidate_id": job["chosen_candidate_id"],
        "winner": winner,
        "chosen": chosen,
        "candidates": serialized_candidates,
        "donor_snippets": top_donor_snippets,
        "style_signals": top_style_signals,
        "insight": {
            "mode": job["mode"],
            "surface_mode": job["surface_mode"],
            "judge_enabled": bool(job["judge_enabled"]),
            "generation_provider": job["generation_provider"],
            "generation_model": job["generation_model"],
            "judge_provider": job["judge_provider"],
            "judge_model": job["judge_model"],
        },
        "choice_history": [
            {
                "choice_id": row["id"],
                "candidate_id": row["candidate_id"],
                "actor_type": row["actor_type"],
                "actor_id": row["actor_id"],
                "reason": row["reason"],
                "created_at": row["created_at"],
            }
            for row in choices
        ],
        "errors": [
            {
                "id": row["id"],
                "phase": row["phase"],
                "code": row["code"],
                "message": row["message"],
                "details": json.loads(row["details_json"] or "{}"),
                "created_at": row["created_at"],
            }
            for row in runtime_errors
        ],
        "timestamps": {
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "completed_at": job["completed_at"],
            "cancelled_at": job["cancelled_at"],
            "failed_at": job["failed_at"],
        },
    }


def submit_rewrite(payload: dict[str, Any], *, idempotency_key: str | None = None) -> dict[str, Any]:
    normalized = normalize_rewrite_request(payload)
    request_body = {
        "text": normalized["text"],
        "mode": normalized["mode"],
        "surface_mode": normalized["surface_mode"],
        "query": normalized["query"],
        "candidate_count": normalized["candidate_count"],
        "use_xai_judge": normalized["use_xai_judge"],
    }
    req_hash = request_hash(request_body)
    conn = connect_runtime()

    if idempotency_key:
        record = get_idempotency_record(conn, key=idempotency_key)
        if record:
            if record["request_hash"] != req_hash:
                raise RuntimeApiError(
                    "IDEMPOTENCY_KEY_REUSED",
                    "Idempotency key was already used for a different request.",
                    phase="request",
                    status=409,
                )
            return _job_response(conn, record["job_id"])

    created_at = now_iso()
    job_id = make_runtime_id("brw")
    create_job(
        conn,
        job={
            "id": job_id,
            "status": "accepted",
            "request_hash": req_hash,
            "source_text": normalized["text"],
            "mode": normalized["mode"],
            "surface_mode": normalized["surface_mode"],
            "query": normalized["query"],
            "candidate_count": normalized["candidate_count"],
            "judge_enabled": normalized["use_xai_judge"] and judge_enabled(),
            "generation_provider": GENERATION_PROVIDER,
            "generation_model": GENERATION_MODEL,
            "judge_provider": JUDGE_PROVIDER if normalized["use_xai_judge"] and judge_enabled() else "",
            "judge_model": active_judge_model() if normalized["use_xai_judge"] and judge_enabled() else "",
            "created_at": created_at,
            "updated_at": created_at,
        },
    )
    if idempotency_key:
        create_idempotency_record(conn, key=idempotency_key, request_hash=req_hash, job_id=job_id, created_at=created_at)

    try:
        update_job_state(conn, job_id=job_id, status="generating", updated_at=now_iso())
        generated = _run_generation(
            source_text=normalized["text"],
            mode=normalized["mode"],
            query=normalized["query"],
            surface_mode=normalized["surface_mode"],
            candidate_count=normalized["candidate_count"],
        )

        update_job_state(conn, job_id=job_id, status="reranking", updated_at=now_iso())
        scored = heuristic_rerank(generated)
        xai_scores: dict[str, float] = {}
        if normalized["use_xai_judge"] and judge_enabled():
            update_job_state(conn, job_id=job_id, status="judging", updated_at=now_iso())
            xai_scores = run_xai_judge_scores(
                source_text=generated.get("source_text", normalized["text"]),
                preferred_bucket=generated.get("preferred_bucket", ""),
                donor_snippets=generated.get("donor_snippets", []),
                candidates=generated.get("candidates", []),
                xai_model=active_judge_model(),
            )
            scored = merge_xai_scores(scored, xai_scores)

        records = [_candidate_record(job_id, idx, item, generated) for idx, item in enumerate(scored)]
        replace_candidates(conn, job_id=job_id, candidates=records)

        winner_candidate_id = records[0]["id"] if records else None
        update_job_state(
            conn,
            job_id=job_id,
            status="completed",
            updated_at=now_iso(),
            completed_at=now_iso(),
            winner_candidate_id=winner_candidate_id,
        )

        return _job_response(conn, job_id)
    except RuntimeApiError:
        raise
    except Exception as exc:
        error_time = now_iso()
        create_runtime_error(
            conn,
            error={
                "id": make_runtime_id("bre"),
                "job_id": job_id,
                "phase": "runtime",
                "code": "RUNTIME_EXECUTION_FAILED",
                "message": str(exc),
                "details": {},
                "created_at": error_time,
            },
        )
        update_job_state(conn, job_id=job_id, status="failed", updated_at=error_time, failed_at=error_time)
        raise RuntimeApiError(
            "RUNTIME_EXECUTION_FAILED",
            str(exc),
            phase="runtime",
            status=500,
        )


def get_job_response(job_id: str) -> dict[str, Any]:
    conn = connect_runtime()
    return _job_response(conn, job_id)


def choose_candidate(job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(payload.get("candidate_id", "") or "")
    if not candidate_id:
        raise RuntimeApiError("MISSING_CANDIDATE_ID", "Field `candidate_id` is required.", phase="request", status=400)
    actor = payload.get("actor") or {}
    actor_type = str(actor.get("type", "client") or "client")
    actor_id = str(actor.get("id", "") or "")
    reason = str(payload.get("reason", "") or "")

    conn = connect_runtime()
    job = get_job(conn, job_id=job_id)
    if not job:
        raise RuntimeApiError("JOB_NOT_FOUND", f"Job `{job_id}` not found.", phase="runtime", status=404)
    if job["status"] not in {"completed", "chosen"}:
        raise RuntimeApiError("JOB_NOT_CHOOSEABLE", "Job is not in a chooseable terminal state.", phase="runtime", status=409)

    candidates = {row["id"]: row for row in list_candidates(conn, job_id=job_id)}
    if candidate_id not in candidates:
        raise RuntimeApiError("CANDIDATE_NOT_FOUND", f"Candidate `{candidate_id}` not found for this job.", phase="runtime", status=404)

    choice_id = make_runtime_id("brch")
    created_at = now_iso()
    create_choice(
        conn,
        choice={
            "id": choice_id,
            "job_id": job_id,
            "candidate_id": candidate_id,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "reason": reason,
            "created_at": created_at,
        },
    )
    update_job_state(
        conn,
        job_id=job_id,
        status="chosen",
        updated_at=created_at,
        chosen_candidate_id=candidate_id,
    )
    response = _job_response(conn, job_id)
    return {
        "job_id": response["job_id"],
        "status": response["status"],
        "winner_candidate_id": response["winner_candidate_id"],
        "chosen_candidate_id": response["chosen_candidate_id"],
        "choice": response["choice_history"][0] if response["choice_history"] else None,
    }
