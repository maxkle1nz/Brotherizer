#!/usr/bin/env python3
"""Local embedding helper using Ollama."""

from __future__ import annotations

import argparse
import json
from typing import Any

import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/embeddings"


def embed_text(text: str, model: str = "nomic-embed-text") -> list[float]:
    resp = requests.post(
        OLLAMA_URL,
        json={"model": model, "prompt": text},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["embedding"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--model", default="nomic-embed-text")
    args = parser.parse_args()
    print(json.dumps({"model": args.model, "embedding": embed_text(args.text, args.model)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
