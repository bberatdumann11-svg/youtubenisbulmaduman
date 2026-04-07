from __future__ import annotations

from .models import ChannelRecord, VideoRecord
from .niche_extractor import extract_niches
from .pipeline import ResearchConfig, ResearchResult
from .scoring import analyze_video


def build_demo_result() -> ResearchResult:
    config = ResearchConfig(seed_keywords=["mythology", "luxury"], expand_queries=True)
    channels = {
        "c1": ChannelRecord(
            channel_id="c1",
            title="Ancient Story Lab",
            subscriber_count=42_000,
            video_count=180,
            view_count=21_000_000,
            description="Faceless mythology documentaries and narrated ancient stories.",
            uploads_playlist_id=None,
        ),
        "c2": ChannelRecord(
            channel_id="c2",
            title="Ultra Luxury Files",
            subscriber_count=18_500,
            video_count=95,
            view_count=8_200_000,
            description="Luxury lifestyle lists, billionaire assets, yacht and mansion stories.",
            uploads_playlist_id=None,
        ),
    }
    videos = [
        VideoRecord(
            video_id="demo1",
            title="The Dark Truth About Medusa",
            channel_id="c1",
            channel_title="Ancient Story Lab",
            published_at="2026-01-12T10:00:00Z",
            duration_seconds=812,
            view_count=1_250_000,
            like_count=31_000,
            comment_count=1800,
            thumbnail_url=None,
            url="https://www.youtube.com/watch?v=demo1",
            description="A narrated mythology documentary about Greek legends.",
            tags=["mythology", "greek mythology", "documentary"],
            seed_keyword="mythology",
            source_query="mythology documentary",
        ),
        VideoRecord(
            video_id="demo2",
            title="Why Hades Was Feared For Centuries",
            channel_id="c1",
            channel_title="Ancient Story Lab",
            published_at="2025-12-01T10:00:00Z",
            duration_seconds=743,
            view_count=780_000,
            like_count=20_000,
            comment_count=950,
            thumbnail_url=None,
            url="https://www.youtube.com/watch?v=demo2",
            description="Faceless ancient mythology story explained.",
            tags=["mythology", "hades", "ancient"],
            seed_keyword="mythology",
            source_query="dark mythology",
        ),
        VideoRecord(
            video_id="demo3",
            title="Inside The Most Expensive Yachts In The World",
            channel_id="c2",
            channel_title="Ultra Luxury Files",
            published_at="2026-02-20T09:00:00Z",
            duration_seconds=665,
            view_count=510_000,
            like_count=9_200,
            comment_count=440,
            thumbnail_url=None,
            url="https://www.youtube.com/watch?v=demo3",
            description="Luxury lifestyle list about billionaire yachts.",
            tags=["luxury", "billionaire", "yacht"],
            seed_keyword="luxury",
            source_query="luxury",
        ),
    ]
    recent = {"c1": videos[:2], "c2": videos[2:]}
    analyses = {
        video.video_id: analyze_video(video, channels.get(video.channel_id), channel_recent_videos=recent.get(video.channel_id, []))
        for video in videos
    }
    niches = extract_niches(videos, channels, analyses, limit=5)
    sorted_videos = sorted(videos, key=lambda video: analyses[video.video_id].opportunity_score, reverse=True)
    return ResearchResult(
        config=config,
        videos=sorted_videos,
        channels=channels,
        analyses=analyses,
        niches=niches,
        recent_videos_by_channel=recent,
    )
