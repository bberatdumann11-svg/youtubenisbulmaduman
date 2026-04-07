from youtube_niche_researcher.demo import build_demo_result


def test_demo_result_has_niches() -> None:
    result = build_demo_result()
    assert result.niches
    assert result.videos[0].video_id in result.analyses

