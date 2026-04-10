#!/usr/bin/env python3
"""Run Apify actors for Brotherizer collection workflows."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests

API_BASE = "https://api.apify.com/v2"


def api_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def normalize_actor_id(actor_id: str) -> str:
    return actor_id.replace("/", "~")


def run_actor_sync_dataset_items(token: str, actor_id: str, run_input: dict[str, Any]) -> list[dict[str, Any]]:
    url = f"{API_BASE}/acts/{normalize_actor_id(actor_id)}/run-sync-get-dataset-items"
    resp = requests.post(url, headers=api_headers(token), json=run_input, timeout=300)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    return [data]


def validate_token(token: str) -> dict[str, Any]:
    url = f"{API_BASE}/users/me"
    resp = requests.get(url, headers=api_headers(token), timeout=60)
    resp.raise_for_status()
    return resp.json()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--actor", default="apify/website-content-crawler")
    parser.add_argument("--input-file", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-token", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("APIFY_API_TOKEN", "").strip()
    if not token:
        print("Missing APIFY_API_TOKEN", file=sys.stderr)
        return 1

    if args.validate_token:
        info = validate_token(token)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return 0

    if not args.input_file:
        print("--input-file is required unless --validate-token is used", file=sys.stderr)
        return 1

    run_input = json.loads(args.input_file.read_text())
    items = run_actor_sync_dataset_items(token, args.actor, run_input)

    rendered = json.dumps(items, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
