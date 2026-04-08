from youtube_niche_researcher.models import VideoRecord
from youtube_niche_researcher.pipeline import ResearchConfig, filter_videos_by_language


def test_filter_videos_by_language_removes_blocked_script_title() -> None:
    config = ResearchConfig(seed_keywords=["titanic"])
    videos = [
        VideoRecord(
            video_id="ok",
            title="The Dark Truth About Titanic",
            channel_id="c1",
            channel_title="Channel",
            published_at="2026-01-01T00:00:00Z",
            duration_seconds=600,
            view_count=1000,
            like_count=None,
            comment_count=None,
            thumbnail_url=None,
            url="https://example.com/ok",
        ),
        VideoRecord(
            video_id="bad",
            title="टाइटैनिक का सच",
            channel_id="c1",
            channel_title="Channel",
            published_at="2026-01-01T00:00:00Z",
            duration_seconds=600,
            view_count=1000,
            like_count=None,
            comment_count=None,
            thumbnail_url=None,
            url="https://example.com/bad",
        ),
    ]
    filtered = filter_videos_by_language(videos, config)
    assert [video.video_id for video in filtered] == ["ok"]
