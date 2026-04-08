from youtube_niche_researcher.language_filter import looks_like_english_title


def test_rejects_devanagari_title() -> None:
    assert not looks_like_english_title("टाइटैनिक का सच")


def test_accepts_english_title() -> None:
    assert looks_like_english_title("The Dark Truth About Titanic")


def test_rejects_romanized_non_english_marker() -> None:
    assert not looks_like_english_title("Titanic ka sach")
