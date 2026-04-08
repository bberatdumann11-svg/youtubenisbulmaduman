from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from .models import ChannelRecord, VideoAnalysis, VideoRecord
from .scoring import clamp
from .text_tools import clean_text, top_terms


@dataclass(slots=True)
class OpportunityGap:
    title: str
    channel: str
    url: str
    views: int
    subscribers: int | None
    views_per_subscriber: float | None
    score: float
    band: str
    reason: str


@dataclass(slots=True)
class NichePath:
    levels: list[str]
    final_niche: str
    warning: str | None = None


@dataclass(slots=True)
class Persona:
    name: str
    age: str
    daily_context: str
    interests: list[str]
    biggest_pains: list[str]
    content_promises: list[str]


@dataclass(slots=True)
class IdeaAdaptation:
    original_title: str
    adapted_title: str
    source_niche: str
    target_niche: str
    pattern: str
    why_it_might_work: str


@dataclass(slots=True)
class IdeaValueScore:
    total_score: float
    value_equation_score: float
    checklist_score: float
    formula: str
    verdict: str
    missing_items: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EvergreenResult:
    score: float
    label: str
    positive_signals: list[str]
    negative_signals: list[str]


@dataclass(slots=True)
class GlobalAppealResult:
    score: float
    label: str
    signals: list[str]
    warnings: list[str]


NICHE_TEMPLATES = {
    "finans": [
        "Finans",
        "Para Kazanma",
        "Sosyal Medyadan Para Kazanma",
        "Maaşından memnun olmayanlar için YouTube'dan para kazanma",
    ],
    "sağlık": [
        "Sağlık",
        "Sağlıklı Yaşam",
        "Evde uygulanabilir rutinler",
        "Yoğun çalışanlar için 10 dakikalık sürdürülebilir rutinler",
    ],
    "saglik": [
        "Sağlık",
        "Sağlıklı Yaşam",
        "Evde uygulanabilir rutinler",
        "Yoğun çalışanlar için 10 dakikalık sürdürülebilir rutinler",
    ],
    "mitoloji": [
        "Mitoloji",
        "Antik hikayeler",
        "Karanlık tanrı ve yaratık hikayeleri",
        "Yetişkin izleyici için faceless mitoloji belgeselleri",
    ],
    "history": [
        "Tarih",
        "Belgesel anlatımı",
        "Unutulmuş imparatorluk ve lider hikayeleri",
        "Harita ve arşiv görselleriyle 10-15 dakikalık tarih belgeselleri",
    ],
}

NICHE_OBJECT_MAP = {
    "kripto": "iş fikri",
    "crypto": "business idea",
    "coin": "iş fikri",
    "coins": "business ideas",
    "altcoin": "side hustle",
    "altcoins": "side hustles",
    "stock": "startup idea",
    "stocks": "startup ideas",
    "fitness": "productivity",
    "workout": "study routine",
    "luxury": "business",
}

EVERGREEN_POSITIVE = {
    "history",
    "ancient",
    "mythology",
    "legend",
    "explained",
    "documentary",
    "beginner",
    "basics",
    "how to",
    "why",
    "timeless",
    "psychology",
    "business model",
}

EVERGREEN_NEGATIVE = {
    "today",
    "breaking",
    "latest",
    "2026",
    "2025",
    "drama",
    "rumor",
    "leak",
    "update",
    "this week",
    "news",
}


def detect_opportunity_gaps(
    videos: list[VideoRecord],
    channels: dict[str, ChannelRecord],
    analyses: dict[str, VideoAnalysis],
    *,
    min_ratio: float = 5,
    min_views: int = 100_000,
) -> list[OpportunityGap]:
    gaps: list[OpportunityGap] = []
    for video in videos:
        channel = channels.get(video.channel_id)
        analysis = analyses.get(video.video_id)
        if not channel or not analysis:
            continue
        ratio = analysis.views_per_subscriber
        if ratio is None or ratio < min_ratio or video.view_count < min_views:
            continue
        score = opportunity_gap_score(video.view_count, channel.subscriber_count, ratio)
        gaps.append(
            OpportunityGap(
                title=video.title,
                channel=channel.title,
                url=video.url,
                views=video.view_count,
                subscribers=channel.subscriber_count,
                views_per_subscriber=ratio,
                score=round(score, 2),
                band=gap_band(score),
                reason=build_gap_reason(video, channel, ratio),
            )
        )
    return sorted(gaps, key=lambda item: item.score, reverse=True)


def opportunity_gap_score(views: int, subscribers: int | None, ratio: float) -> float:
    ratio_component = min(math.log10(max(ratio, 1)) / math.log10(100), 1) * 45
    volume_component = min(math.log10(max(views, 10_000) / 10_000) / math.log10(1000), 1) * 35
    underdog_component = 20 if subscribers and subscribers < 250_000 else 10 if subscribers and subscribers < 1_000_000 else 4
    return clamp(ratio_component + volume_component + underdog_component, 0, 100)


def gap_band(score: float) -> str:
    if score >= 85:
        return "çok güçlü fırsat"
    if score >= 70:
        return "güçlü fırsat"
    if score >= 55:
        return "takibe değer"
    return "zayıf sinyal"


def build_gap_reason(video: VideoRecord, channel: ChannelRecord, ratio: float) -> str:
    subs = channel.subscriber_count if channel.subscriber_count is not None else "gizli"
    return (
        f"{channel.title} kanalında {subs} aboneye karşılık bu video {video.view_count:,} izlenmiş; "
        f"oran yaklaşık {ratio:.1f}x."
    ).replace(",", ".")


def build_niche_path(
    broad_category: str,
    monetization_angle: str,
    audience: str,
    specific_problem: str,
) -> NichePath:
    broad = clean_text(broad_category)
    key = broad.lower()
    if key in NICHE_TEMPLATES and not any([monetization_angle, audience, specific_problem]):
        levels = NICHE_TEMPLATES[key]
    else:
        levels = [
            broad or "Genel kategori",
            clean_text(monetization_angle) or f"{broad} içinde uygulanabilir alt alan",
            clean_text(audience) or "Belirli problemi olan hedef kişi",
            clean_text(specific_problem) or "Tek ve net bir acıya çözüm veren içerik serisi",
        ]
    warning = None
    if len([item for item in levels if item and "Genel" not in item]) < 4:
        warning = "Niş hâlâ geniş. En az 4. seviye tek bir insanın tek bir problemine inmeli."
    return NichePath(levels=levels, final_niche=levels[-1], warning=warning)


def generate_persona(niche: str, audience: str, pain: str) -> Persona:
    niche_terms = top_terms([niche], limit=3)
    interests = niche_terms or ["YouTube", "online gelir", "pratik öğrenme"]
    pain_text = pain or "nereden başlayacağını bilmiyor ve zamanını boşa harcamaktan korkuyor"
    audience_text = audience or "yeni fırsat arayan ama karar vermekte zorlanan biri"
    return Persona(
        name="Mert",
        age="27",
        daily_context=f"{audience_text}. İş/okul temposu arasında hızlı ama güvenilir cevaplar arıyor.",
        interests=interests,
        biggest_pains=[
            pain_text,
            "çok seçenek olduğu için hangi fikre odaklanacağını seçemiyor",
            "izlenme ihtimali olmayan içeriğe emek harcamaktan çekiniyor",
        ],
        content_promises=[
            "karmaşık konuyu sadeleştir",
            "ilk adımı net göster",
            "riskleri saklamadan anlat",
        ],
    )


def adapt_idea(original_title: str, source_niche: str, target_niche: str) -> IdeaAdaptation:
    adapted = original_title
    replacements = build_replacements(source_niche, target_niche)
    for old, new in replacements.items():
        adapted = re.sub(rf"\b{re.escape(old)}\b", new, adapted, flags=re.IGNORECASE)
    if adapted == original_title:
        adapted = f"{extract_pattern(original_title)}: {target_niche}"
    return IdeaAdaptation(
        original_title=original_title,
        adapted_title=adapted,
        source_niche=source_niche,
        target_niche=target_niche,
        pattern=extract_pattern(original_title),
        why_it_might_work="Başarılı paketi korur, nesneyi/vaadi hedef nişe taşır ve rekabeti daha dar bir alana indirir.",
    )


def build_replacements(source_niche: str, target_niche: str) -> dict[str, str]:
    target = clean_text(target_niche).lower() or "iş fikri"
    mapping = dict(NICHE_OBJECT_MAP)
    mapping[clean_text(source_niche).lower()] = target
    mapping["money"] = target
    mapping["para"] = target
    return mapping


def extract_pattern(title: str) -> str:
    lower = title.lower()
    if re.search(r"\b\d+\b", title):
        return "Sayı listesi"
    if lower.startswith("why ") or lower.startswith("neden "):
        return "Neden anlatısı"
    if lower.startswith("how ") or lower.startswith("nasıl "):
        return "Nasıl yapılır"
    if "truth" in lower or "gerçek" in lower:
        return "Gizli gerçek / merak açığı"
    return "Başarılı başlık iskeleti"


def score_idea_value(
    dream_result: int,
    success_probability: int,
    time_window: int,
    effort: int,
    checklist: dict[str, bool],
) -> IdeaValueScore:
    dream = max(dream_result, 1)
    probability = max(success_probability, 1)
    time = max(time_window, 1)
    effort_value = max(effort, 1)
    raw = (dream * probability) / (time * effort_value)
    value_score = clamp(raw * 10, 0, 100)
    checklist_score = (sum(1 for passed in checklist.values() if passed) / max(len(checklist), 1)) * 100
    total = value_score * 0.65 + checklist_score * 0.35
    missing = [label for label, passed in checklist.items() if not passed]
    verdict = "yayına aday" if total >= 75 else "iyileştir" if total >= 55 else "ele"
    return IdeaValueScore(
        total_score=round(total, 2),
        value_equation_score=round(value_score, 2),
        checklist_score=round(checklist_score, 2),
        formula="(Rüya Sonucu x Başarı Olasılığı) / (Zaman Zarfı x Çaba)",
        verdict=verdict,
        missing_items=missing,
    )


def score_evergreen(title: str, description: str = "") -> EvergreenResult:
    text = f" {title} {description} ".lower()
    positives = [word for word in EVERGREEN_POSITIVE if word in text]
    negatives = [word for word in EVERGREEN_NEGATIVE if word in text]
    score = 55 + len(positives) * 8 - len(negatives) * 12
    score = clamp(score, 0, 100)
    label = "uzun vadeli güçlü" if score >= 75 else "orta vadeli" if score >= 55 else "geçici/trend riski"
    return EvergreenResult(
        score=round(score, 2),
        label=label,
        positive_signals=positives,
        negative_signals=negatives,
    )


def score_global_appeal(
    *,
    visual_without_language: int,
    culture_specificity: int,
    translation_ease: int,
    high_cpm_market_fit: int,
    production_complexity: int,
) -> GlobalAppealResult:
    score = (
        visual_without_language * 0.30
        + (10 - culture_specificity) * 0.20
        + translation_ease * 0.20
        + high_cpm_market_fit * 0.20
        + (10 - production_complexity) * 0.10
    ) * 10
    label = "global ölçeklenebilir" if score >= 75 else "kısmen global" if score >= 55 else "yerel kalma riski yüksek"
    signals = []
    warnings = []
    if visual_without_language >= 7:
        signals.append("Dil olmadan da anlaşılabilecek görsel anlatım potansiyeli var.")
    if high_cpm_market_fit >= 7:
        signals.append("Alım gücü yüksek pazarlara uyarlanabilir.")
    if culture_specificity >= 7:
        warnings.append("Kültüre çok bağlı; global yayında açıklama/yeniden paketleme gerekir.")
    if production_complexity >= 8:
        warnings.append("Üretim karmaşıklığı yüksek; seri üretim maliyeti artabilir.")
    return GlobalAppealResult(score=round(score, 2), label=label, signals=signals, warnings=warnings)

