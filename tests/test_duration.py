from youtube_niche_researcher.duration import parse_iso8601_duration


def test_parse_iso8601_duration_minutes_seconds() -> None:
    assert parse_iso8601_duration("PT12M34S") == 754


def test_parse_iso8601_duration_hours() -> None:
    assert parse_iso8601_duration("PT1H02M03S") == 3723

