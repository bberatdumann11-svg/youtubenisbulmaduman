from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .language_filter import looks_like_english_title
from .models import ChannelRecord, NicheReport, VideoAnalysis, VideoRecord
from .niche_extractor import extract_niches
from .query_planner import build_queries
from .scoring import analyze_video
from .youtube_api import YouTubeClient


@dataclass(slots=True)
class ResearchConfig:
    seed_keywords: list[str]
    days_back: int = 365
    max_search_results_per_query: int = 25
    region_code: str = "US"
    relevance_language: str = "en"
    duration_modes: list[str] = field(default_factory=lambda: ["medium", "long"])
    expand_queries: bool = False
    custom_queries: list[str] = field(default_factory=list)
    channel_limit: int = 20
    channel_recent_limit: int = 30
    exclude_shorts: bool = True
    exclude_non_latin_titles: bool = True
    min_latin_title_ratio: float = 0.8
    niche_limit: int = 5

    @property
    def published_after(self) -> str:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.days_back)
        return cutoff.replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class ResearchResult:
    config: ResearchConfig
    videos: list[VideoRecord]
    channels: dict[str, ChannelRecord]
    analyses: dict[str, VideoAnalysis]
    niches: list[NicheReport]
    recent_videos_by_channel: dict[str, list[VideoRecord]]


def run_research(client: YouTubeClient, config: ResearchConfig) -> ResearchResult:
    video_meta: dict[str, tuple[str, str]] = {}
    video_ids: list[str] = []

    for seed in config.seed_keywords:
        for query in build_queries(seed, expand=config.expand_queries, custom_queries=config.custom_queries):
            for duration_mode in config.duration_modes:
                search_items = client.search_videos(
                    query,
                    published_after=config.published_after,
                    region_code=config.region_code,
                    relevance_language=config.relevance_language,
                    video_duration=duration_mode,
                    max_results=config.max_search_results_per_query,
                )
                for item in search_items:
                    video_id = item.get("id", {}).get("videoId")
                    if video_id and video_id not in video_meta:
                        video_meta[video_id] = (seed, query)
                        video_ids.append(video_id)

    videos = client.videos(video_ids)
    for video in videos:
        seed, source_query = video_meta.get(video.video_id, (None, None))
        video.seed_keyword = seed
        video.source_query = source_query

    if config.exclude_shorts:
        videos = [video for video in videos if not video.is_probable_short]
    videos = filter_videos_by_language(videos, config)

    channel_ids = list(dict.fromkeys(video.channel_id for video in videos if video.channel_id))
    channels = {channel.channel_id: channel for channel in client.channels(channel_ids)}

    prelim = {
        video.video_id: analyze_video(video, channels.get(video.channel_id), channel_recent_videos=[])
        for video in videos
    }
    top_channel_ids = rank_candidate_channels(videos, prelim)[: config.channel_limit]
    recent_videos_by_channel = collect_recent_channel_videos(client, channels, top_channel_ids, config)

    analyses = {
        video.video_id: analyze_video(
            video,
            channels.get(video.channel_id),
            channel_recent_videos=recent_videos_by_channel.get(video.channel_id, []),
        )
        for video in videos
    }
    niches = extract_niches(videos, channels, analyses, limit=config.niche_limit)
    return ResearchResult(
        config=config,
        videos=sorted(videos, key=lambda item: analyses[item.video_id].opportunity_score, reverse=True),
        channels=channels,
        analyses=analyses,
        niches=niches,
        recent_videos_by_channel=recent_videos_by_channel,
    )


def rank_candidate_channels(videos: list[VideoRecord], analyses: dict[str, VideoAnalysis]) -> list[str]:
    best_by_channel: dict[str, float] = {}
    for video in videos:
        analysis = analyses.get(video.video_id)
        if not analysis:
            continue
        best_by_channel[video.channel_id] = max(best_by_channel.get(video.channel_id, 0), analysis.opportunity_score)
    return [
        channel_id
        for channel_id, _score in sorted(best_by_channel.items(), key=lambda item: item[1], reverse=True)
        if channel_id
    ]


def collect_recent_channel_videos(
    client: YouTubeClient,
    channels: dict[str, ChannelRecord],
    channel_ids: list[str],
    config: ResearchConfig,
) -> dict[str, list[VideoRecord]]:
    recent: dict[str, list[VideoRecord]] = {}
    for channel_id in channel_ids:
        channel = channels.get(channel_id)
        if not channel or not channel.uploads_playlist_id:
            continue
        ids = client.playlist_video_ids(channel.uploads_playlist_id, max_results=config.channel_recent_limit)
        videos = client.videos(ids)
        if config.exclude_shorts:
            videos = [video for video in videos if not video.is_probable_short]
        videos = filter_videos_by_language(videos, config)
        recent[channel_id] = videos
    return recent


def filter_videos_by_language(videos: list[VideoRecord], config: ResearchConfig) -> list[VideoRecord]:
    if not config.exclude_non_latin_titles:
        return videos
    return [
        video
        for video in videos
        if looks_like_english_title(video.title, min_latin_ratio=config.min_latin_title_ratio)
    ]
