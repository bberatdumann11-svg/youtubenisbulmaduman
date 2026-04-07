from __future__ import annotations

import json
import time
from collections.abc import Iterable
from typing import TypeVar
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .duration import parse_iso8601_duration
from .models import ChannelRecord, VideoRecord


YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
T = TypeVar("T")


class YouTubeApiError(RuntimeError):
    pass


class YouTubeClient:
    def __init__(self, api_key: str, *, timeout: int = 30, sleep_seconds: float = 0.1) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.sleep_seconds = sleep_seconds

    def search_videos(
        self,
        query: str,
        *,
        published_after: str,
        order: str = "viewCount",
        region_code: str = "US",
        relevance_language: str = "en",
        video_duration: str = "medium",
        max_results: int = 50,
    ) -> list[dict]:
        items: list[dict] = []
        page_token: str | None = None
        remaining = max_results
        while remaining > 0:
            params = {
                "part": "snippet",
                "type": "video",
                "q": query,
                "order": order,
                "publishedAfter": published_after,
                "videoDuration": video_duration,
                "maxResults": min(50, remaining),
                "regionCode": region_code,
                "relevanceLanguage": relevance_language,
                "safeSearch": "none",
            }
            if page_token:
                params["pageToken"] = page_token
            payload = self._get_json("search", params)
            items.extend(payload.get("items", []))
            remaining -= len(payload.get("items", []))
            page_token = payload.get("nextPageToken")
            if not page_token or not payload.get("items"):
                break
            time.sleep(self.sleep_seconds)
        return items

    def videos(self, video_ids: Iterable[str]) -> list[VideoRecord]:
        records: list[VideoRecord] = []
        for chunk in chunks([vid for vid in video_ids if vid], 50):
            payload = self._get_json(
                "videos",
                {
                    "part": "snippet,statistics,contentDetails,status",
                    "id": ",".join(chunk),
                    "maxResults": 50,
                },
            )
            for item in payload.get("items", []):
                record = video_from_api_item(item)
                if record:
                    records.append(record)
            time.sleep(self.sleep_seconds)
        return records

    def channels(self, channel_ids: Iterable[str]) -> list[ChannelRecord]:
        records: list[ChannelRecord] = []
        for chunk in chunks([cid for cid in channel_ids if cid], 50):
            payload = self._get_json(
                "channels",
                {
                    "part": "snippet,statistics,contentDetails,brandingSettings",
                    "id": ",".join(chunk),
                    "maxResults": 50,
                },
            )
            for item in payload.get("items", []):
                record = channel_from_api_item(item)
                if record:
                    records.append(record)
            time.sleep(self.sleep_seconds)
        return records

    def playlist_video_ids(self, playlist_id: str, *, max_results: int = 30) -> list[str]:
        ids: list[str] = []
        page_token: str | None = None
        remaining = max_results
        while remaining > 0:
            params = {
                "part": "contentDetails,snippet",
                "playlistId": playlist_id,
                "maxResults": min(50, remaining),
            }
            if page_token:
                params["pageToken"] = page_token
            payload = self._get_json("playlistItems", params)
            for item in payload.get("items", []):
                video_id = item.get("contentDetails", {}).get("videoId")
                if video_id:
                    ids.append(video_id)
            remaining -= len(payload.get("items", []))
            page_token = payload.get("nextPageToken")
            if not page_token or not payload.get("items"):
                break
            time.sleep(self.sleep_seconds)
        return ids

    def _get_json(self, endpoint: str, params: dict[str, object]) -> dict:
        params = {**params, "key": self.api_key}
        url = f"{YOUTUBE_API_BASE}/{endpoint}?{urlencode(params)}"
        request = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise YouTubeApiError(f"YouTube API error {exc.code}: {body}") from exc


def video_from_api_item(item: dict) -> VideoRecord | None:
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    content = item.get("contentDetails", {})
    status = item.get("status", {})
    if status.get("privacyStatus") not in (None, "public"):
        return None
    video_id = item.get("id")
    if not video_id:
        return None
    thumbnails = snippet.get("thumbnails", {})
    thumbnail_url = (
        thumbnails.get("maxres", {}).get("url")
        or thumbnails.get("high", {}).get("url")
        or thumbnails.get("medium", {}).get("url")
        or thumbnails.get("default", {}).get("url")
    )
    return VideoRecord(
        video_id=video_id,
        title=snippet.get("title", ""),
        channel_id=snippet.get("channelId", ""),
        channel_title=snippet.get("channelTitle", ""),
        published_at=snippet.get("publishedAt", ""),
        duration_seconds=parse_iso8601_duration(content.get("duration", "")),
        view_count=parse_int(stats.get("viewCount")),
        like_count=parse_optional_int(stats.get("likeCount")),
        comment_count=parse_optional_int(stats.get("commentCount")),
        thumbnail_url=thumbnail_url,
        url=f"https://www.youtube.com/watch?v={video_id}",
        description=snippet.get("description", ""),
        tags=snippet.get("tags", []) or [],
    )


def channel_from_api_item(item: dict) -> ChannelRecord | None:
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    content = item.get("contentDetails", {})
    related = content.get("relatedPlaylists", {})
    channel_id = item.get("id")
    if not channel_id:
        return None
    subscriber_count = None
    if not stats.get("hiddenSubscriberCount"):
        subscriber_count = parse_optional_int(stats.get("subscriberCount"))
    return ChannelRecord(
        channel_id=channel_id,
        title=snippet.get("title", ""),
        subscriber_count=subscriber_count,
        video_count=parse_optional_int(stats.get("videoCount")),
        view_count=parse_optional_int(stats.get("viewCount")),
        description=snippet.get("description", ""),
        uploads_playlist_id=related.get("uploads"),
        country=snippet.get("country"),
        custom_url=snippet.get("customUrl"),
    )


def parse_int(value: object) -> int:
    try:
        return int(value) if value is not None else 0
    except (TypeError, ValueError):
        return 0


def parse_optional_int(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def chunks(items: list[T], size: int) -> Iterable[list[T]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]
