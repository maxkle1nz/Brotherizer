#!/usr/bin/env python3
"""Collect public YouTube comment threads into NDJSON for Brotherizer."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

API_BASE = "https://www.googleapis.com/youtube/v3"


def load_targets(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError("targets file must be a JSON list")
    return data


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def iter_video_ids_for_channel(api_key: str, channel_id: str, max_videos: int) -> list[str]:
    video_ids: list[str] = []
    page_token = ""
    session = requests.Session()

    while len(video_ids) < max_videos:
        params = {
            "key": api_key,
            "part": "id",
            "channelId": channel_id,
            "order": "date",
            "type": "video",
            "maxResults": min(50, max_videos - len(video_ids)),
        }
        if page_token:
            params["pageToken"] = page_token
        resp = session.get(f"{API_BASE}/search", params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        for item in payload.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                video_ids.append(video_id)
        page_token = payload.get("nextPageToken", "")
        if not page_token:
            break
    return video_ids


def iter_video_ids_for_query(
    api_key: str,
    query: str,
    max_videos: int,
    region_code: str = "",
    relevance_language: str = "",
) -> list[str]:
    video_ids: list[str] = []
    page_token = ""
    session = requests.Session()

    while len(video_ids) < max_videos:
        params = {
            "key": api_key,
            "part": "id",
            "q": query,
            "order": "relevance",
            "type": "video",
            "maxResults": min(50, max_videos - len(video_ids)),
        }
        if region_code:
            params["regionCode"] = region_code
        if relevance_language:
            params["relevanceLanguage"] = relevance_language
        if page_token:
            params["pageToken"] = page_token
        resp = session.get(f"{API_BASE}/search", params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        for item in payload.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                video_ids.append(video_id)
        page_token = payload.get("nextPageToken", "")
        if not page_token:
            break
    return video_ids


def fetch_comment_threads(
    api_key: str,
    video_id: str,
    max_comments: int,
    search_terms: str = "",
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page_token = ""
    session = requests.Session()

    while len(items) < max_comments:
        params = {
            "key": api_key,
            "part": "snippet,replies",
            "videoId": video_id,
            "textFormat": "plainText",
            "order": "relevance",
            "maxResults": min(100, max_comments - len(items)),
        }
        if search_terms:
            params["searchTerms"] = search_terms
        if page_token:
            params["pageToken"] = page_token

        resp = session.get(f"{API_BASE}/commentThreads", params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        items.extend(payload.get("items", []))
        page_token = payload.get("nextPageToken", "")
        if not page_token:
            break
    return items[:max_comments]


def flatten_thread(source: dict[str, Any], video_id: str, thread: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    snippet = thread.get("snippet", {})
    top = snippet.get("topLevelComment", {}).get("snippet", {})
    top_id = thread.get("id", "")
    if top.get("textDisplay"):
        out.append(
            {
                "platform": "youtube",
                "source_kind": "comment",
                "channel_id": source.get("channel_id", ""),
                "channel_label": source.get("label", ""),
                "video_id": video_id,
                "thread_id": top_id,
                "comment_id": top_id,
                "reply_to_comment_id": "",
                "author": top.get("authorDisplayName", ""),
                "author_channel_id": top.get("authorChannelId", {}).get("value", ""),
                "text": top.get("textDisplay", "").strip(),
                "like_count": top.get("likeCount", 0),
                "published_at": top.get("publishedAt", ""),
                "updated_at": top.get("updatedAt", ""),
                "is_reply": False,
                "lang_hint": source.get("lang", ""),
                "topic_tags": source.get("topic_tags", []),
                "audience_mode": "comment-like",
            }
        )

    for reply in thread.get("replies", {}).get("comments", []):
        rs = reply.get("snippet", {})
        if not rs.get("textDisplay"):
            continue
        out.append(
            {
                "platform": "youtube",
                "source_kind": "reply",
                "channel_id": source.get("channel_id", ""),
                "channel_label": source.get("label", ""),
                "video_id": video_id,
                "thread_id": top_id,
                "comment_id": reply.get("id", ""),
                "reply_to_comment_id": top_id,
                "author": rs.get("authorDisplayName", ""),
                "author_channel_id": rs.get("authorChannelId", {}).get("value", ""),
                "text": rs.get("textDisplay", "").strip(),
                "like_count": rs.get("likeCount", 0),
                "published_at": rs.get("publishedAt", ""),
                "updated_at": rs.get("updatedAt", ""),
                "is_reply": True,
                "lang_hint": source.get("lang", ""),
                "topic_tags": source.get("topic_tags", []),
                "audience_mode": "reply-like",
            }
        )

    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--max-videos", type=int, default=5)
    parser.add_argument("--max-comments", type=int, default=200)
    parser.add_argument("--sleep-ms", type=int, default=200)
    args = parser.parse_args()

    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        print("Missing YOUTUBE_API_KEY", file=sys.stderr)
        return 1

    targets = load_targets(args.targets)
    ensure_parent(args.out)
    total_rows = 0

    with args.out.open("w", encoding="utf-8") as handle:
        for source in targets:
            channel_id = source.get("channel_id", "").strip()
            query = source.get("query", "").strip()
            if not channel_id and not query:
                continue
            if channel_id:
                video_ids = iter_video_ids_for_channel(api_key, channel_id, args.max_videos)
            else:
                video_ids = iter_video_ids_for_query(
                    api_key=api_key,
                    query=query,
                    max_videos=args.max_videos,
                    region_code=source.get("region_code", "").strip(),
                    relevance_language=source.get("relevance_language", "").strip(),
                )
            for video_id in video_ids:
                try:
                    threads = fetch_comment_threads(
                        api_key=api_key,
                        video_id=video_id,
                        max_comments=args.max_comments,
                        search_terms=source.get("search_terms", "").strip(),
                    )
                    for thread in threads:
                        for row in flatten_thread(source, video_id, thread):
                            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                            total_rows += 1
                except requests.HTTPError as exc:
                    source_ref = channel_id or query
                    print(f"[warn] {source_ref} {video_id}: {exc}", file=sys.stderr)
                time.sleep(args.sleep_ms / 1000)

    print(json.dumps({"ok": True, "rows_written": total_rows, "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
