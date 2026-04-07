from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean, median

from .models import ChannelRecord, NicheReport, VideoAnalysis, VideoRecord
from .text_tools import extract_title_pattern, titlecase_phrase, top_terms


NICHE_RULES: list[tuple[str, set[str]]] = [
    ("Mitoloji / Efsane Hikayeleri", {"mythology", "myth", "legend", "greek", "god", "gods", "ancient"}),
    ("Korku / Gizem Hikayeleri", {"horror", "scary", "mystery", "dark", "creepy", "haunted"}),
    ("Lüks / Yaşam Tarzı Listeleri", {"luxury", "rich", "richest", "expensive", "billionaire", "mansion", "yacht"}),
    ("İş Dünyası / Şirket Belgeselleri", {"business", "company", "startup", "brand", "bankrupt", "failed", "rise"}),
    ("Tarih Belgeselleri", {"history", "empire", "war", "ancient", "king", "queen", "civilization"}),
    ("Yapay Zeka / Teknoloji Açıklamaları", {"ai", "artificial", "technology", "tech", "robot", "future", "software"}),
]

SEARCH_BASE_BY_LABEL = {
    "Mitoloji / Efsane Hikayeleri": "mythology legend stories",
    "Korku / Gizem Hikayeleri": "horror mystery stories",
    "Lüks / Yaşam Tarzı Listeleri": "luxury lifestyle lists",
    "İş Dünyası / Şirket Belgeselleri": "business company documentary",
    "Tarih Belgeselleri": "history documentary",
    "Yapay Zeka / Teknoloji Açıklamaları": "ai technology explained",
    "Genel Anlatım / Açıklama Videoları": "explained documentary stories",
}


def extract_niches(
    videos: list[VideoRecord],
    channels: dict[str, ChannelRecord],
    analyses: dict[str, VideoAnalysis],
    *,
    limit: int = 5,
) -> list[NicheReport]:
    grouped: dict[str, list[VideoRecord]] = defaultdict(list)
    for video in videos:
        if video.video_id not in analyses:
            continue
        grouped[classify_niche_label(video)].append(video)

    reports: list[NicheReport] = []
    for label, niche_videos in grouped.items():
        niche_analyses = [analyses[video.video_id] for video in niche_videos if video.video_id in analyses]
        if not niche_analyses:
            continue
        channel_names = unique([channels.get(video.channel_id).title if channels.get(video.channel_id) else video.channel_title for video in niche_videos])
        patterns = unique([extract_title_pattern(video.title) for video in niche_videos])[:5]
        titles = [video.title for video in niche_videos]
        terms = top_terms(titles, limit=6)
        score = calculate_niche_score(niche_analyses, niche_videos)
        ai_suitability = majority([analysis.ai_suitability for analysis in niche_analyses])
        risk_level = majority([analysis.factual_risk for analysis in niche_analyses])
        why = build_why_promising(niche_analyses, niche_videos, patterns)
        reports.append(
            NicheReport(
                name=label if label != "Genel Anlatım / Açıklama Videoları" else fallback_label(niche_videos),
                score=round(score, 2),
                seed_keywords=unique([video.seed_keyword or "" for video in niche_videos if video.seed_keyword]),
                example_channels=channel_names[:5],
                example_videos=unique(titles)[:5],
                example_formats=patterns,
                repeat_search_terms=build_repeat_terms(label, terms),
                ai_suitability=ai_suitability,
                risk_level=risk_level,
                why_promising=why,
                starting_angles=build_starting_angles(label, terms),
                estimated_series_size=estimate_series_size(terms, niche_videos),
            )
        )
    return sorted(reports, key=lambda item: item.score, reverse=True)[:limit]


def classify_niche_label(video: VideoRecord) -> str:
    tokens = set(top_terms([f"{video.title} {video.description} {' '.join(video.tags)}"], limit=20))
    seed = (video.seed_keyword or "").lower()
    tokens.add(seed)
    for label, keywords in NICHE_RULES:
        if tokens & keywords:
            return label
    return "Genel Anlatım / Açıklama Videoları"


def calculate_niche_score(analyses: list[VideoAnalysis], videos: list[VideoRecord]) -> float:
    opportunity = median([analysis.opportunity_score for analysis in analyses])
    ai_score = mean(ai_value(analysis.ai_suitability) for analysis in analyses) * 15
    risk_penalty = mean(risk_value(analysis.factual_risk) for analysis in analyses) * 15
    channel_diversity = min(len({video.channel_id for video in videos}) / 5, 1) * 10
    repeatability = mean(analysis.repeatable_format_score for analysis in analyses)
    demand = min(median([video.view_count for video in videos]) / 1_000_000, 1) * 10
    return max(0, min(100, opportunity * 0.55 + ai_score + channel_diversity + demand + repeatability - risk_penalty))


def build_why_promising(
    analyses: list[VideoAnalysis],
    videos: list[VideoRecord],
    patterns: list[str],
) -> list[str]:
    why: list[str] = []
    median_views = int(median([video.view_count for video in videos]))
    high_ratio = [analysis.views_per_subscriber for analysis in analyses if analysis.views_per_subscriber and analysis.views_per_subscriber >= 10]
    if median_views >= 100_000:
        why.append(f"Medyan örnek video izlenmesi güçlü: {median_views:,}".replace(",", "."))
    if high_ratio:
        why.append("Düşük aboneli kanallarda yüksek izlenme sinyali var.")
    if patterns:
        why.append("Tekrar edilebilir başlık/format şablonları yakalanıyor.")
    if mean(analysis.faceless_probability for analysis in analyses) >= 0.6:
        why.append("Faceless üretim ihtimali yüksek görünüyor.")
    if not why:
        why.append("Talep sinyali var, ancak daha fazla örnekle doğrulanmalı.")
    return why


def build_repeat_terms(label: str, terms: list[str]) -> list[str]:
    base = SEARCH_BASE_BY_LABEL.get(label, " ".join(label.replace("/", " ").lower().split()))
    candidates = [
        base,
        f"{base} explained",
        f"{base} documentary",
    ]
    if "stories" not in base:
        candidates.append(f"{base} stories")
    candidates.extend(f"{term} explained" for term in terms[:4])
    return unique(candidates)[:8]


def build_starting_angles(label: str, terms: list[str]) -> list[str]:
    subject = titlecase_phrase(pick_subject(terms)) if terms else "{Topic}"
    if "Mitoloji" in label:
        return [
            f"The Dark Truth About {subject}",
            f"Why {subject} Was Feared For Centuries",
            f"The Most Brutal Punishments In Ancient Mythology",
        ]
    if "Korku" in label or "Gizem" in label:
        return [
            f"The Disturbing Story Behind {subject}",
            f"3 Unsolved Mysteries That Still Make No Sense",
            f"The Creepiest Legend Nobody Can Explain",
        ]
    if "Lüks" in label:
        return [
            f"Inside The Most Expensive {subject} Ever Built",
            f"How Billionaires Really Spend Money On {subject}",
            f"Top 10 Luxury Assets Only The Richest People Own",
        ]
    if "İş Dünyası" in label:
        return [
            f"The Rise And Fall Of {subject}",
            f"How {subject} Quietly Took Over The Market",
            f"Why This Billion-Dollar Company Suddenly Collapsed",
        ]
    if "Tarih" in label:
        return [
            f"The Forgotten History Of {subject}",
            f"Why This Ancient Empire Disappeared",
            f"The Battle That Changed Everything",
        ]
    if "Teknoloji" in label:
        return [
            f"How {subject} Is Changing Everything",
            f"The Dark Side Of This New Technology",
            f"Why Everyone Is Suddenly Talking About {subject}",
        ]
    return [
        f"Why {subject} Is More Interesting Than It Looks",
        f"The Hidden Story Behind {subject}",
        f"{subject} Explained In 10 Minutes",
    ]


def estimate_series_size(terms: list[str], videos: list[VideoRecord]) -> int:
    return max(10, min(100, len(set(terms)) * 8 + len({video.channel_id for video in videos}) * 5))


def pick_subject(terms: list[str]) -> str:
    generic = {
        "dark",
        "truth",
        "explained",
        "documentary",
        "story",
        "stories",
        "expensive",
        "world",
        "most",
        "inside",
        "feared",
        "centuries",
        "ancient",
        "luxury",
        "mythology",
    }
    for term in terms:
        if term not in generic:
            return term
    return terms[0] if terms else "{topic}"


def fallback_label(videos: list[VideoRecord]) -> str:
    terms = top_terms([video.title for video in videos], limit=3)
    if not terms:
        return "Genel Anlatım / Açıklama Videoları"
    return f"{titlecase_phrase(' '.join(terms))} Explainer"


def majority(values: list[str]) -> str:
    if not values:
        return "unknown"
    return Counter(values).most_common(1)[0][0]


def unique(values: list[str]) -> list[str]:
    return [value for value in dict.fromkeys(value for value in values if value)]


def ai_value(value: str) -> float:
    return {"AI-only friendly": 1, "AI-assisted only": 0.6, "not suitable for AI-only": 0.1}.get(value, 0.5)


def risk_value(value: str) -> float:
    return {"low": 0, "medium": 0.45, "high": 1}.get(value, 0.45)
