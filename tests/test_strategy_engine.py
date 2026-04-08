from youtube_niche_researcher.strategy_engine import (
    adapt_idea,
    opportunity_gap_score,
    score_global_appeal,
    score_idea_value,
)


def test_opportunity_gap_score_marks_large_ratio_as_strong() -> None:
    score = opportunity_gap_score(51_000_000, 170_000, 300)
    assert score >= 85


def test_adapt_idea_replaces_coin_with_business_idea() -> None:
    result = adapt_idea("En hızlı kazandıran 10 coin", "kripto", "iş fikri")
    assert "iş fikri" in result.adapted_title.lower()


def test_idea_value_score_has_verdict() -> None:
    result = score_idea_value(
        8,
        7,
        3,
        3,
        {
            "Fikir heyecanlandırıyor mu?": True,
            "Mümkün mü?": True,
            "İzlenme kanıtı var mı?": True,
            "Paketlenebilir mi?": True,
            "Genel çekiciliği var mı?": True,
        },
    )
    assert result.total_score > 50
    assert result.verdict in {"yayına aday", "iyileştir", "ele"}


def test_idea_value_rewards_shorter_time_and_lower_effort() -> None:
    checklist = {
        "Fikir heyecanlandırıyor mu?": True,
        "Mümkün mü?": True,
        "İzlenme kanıtı var mı?": True,
        "Paketlenebilir mi?": True,
        "Genel çekiciliği var mı?": True,
    }
    hard = score_idea_value(8, 7, 2, 2, checklist)
    easy = score_idea_value(8, 7, 9, 9, checklist)
    assert easy.total_score > hard.total_score


def test_global_score_range() -> None:
    result = score_global_appeal(
        visual_without_language=8,
        culture_specificity=2,
        translation_ease=8,
        high_cpm_market_fit=7,
        production_complexity=5,
    )
    assert 0 <= result.score <= 100
