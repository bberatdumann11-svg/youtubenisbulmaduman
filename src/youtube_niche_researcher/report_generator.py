from __future__ import annotations

from pathlib import Path

from .duration import format_duration
from .exporters import ensure_dir
from .display import turkish_ai_label, turkish_risk_label
from .pipeline import ResearchResult


def build_markdown_report(result: ResearchResult) -> str:
    lines: list[str] = []
    lines.append("# YouTube Niş Araştırma Raporu")
    lines.append("")
    lines.append(f"- Ana konular: {', '.join(result.config.seed_keywords)}")
    lines.append(f"- Zaman filtresi: son {result.config.days_back} gün")
    lines.append(f"- Toplam video: {len(result.videos)}")
    lines.append(f"- Toplam kanal: {len(result.channels)}")
    lines.append("")
    lines.append("## En Umut Verici Nişler")
    lines.append("")
    if not result.niches:
        lines.append("Yeterli niş sinyali bulunamadı. Daha geniş ana konular yazmayı veya benzer aramaları açmayı deneyin.")
    for index, niche in enumerate(result.niches, start=1):
        lines.append(f"### {index}. {niche.name} - {niche.score}/100")
        lines.append("")
        lines.append(f"- Yapay zeka uygunluğu: {turkish_ai_label(niche.ai_suitability)}")
        lines.append(f"- Risk seviyesi: {turkish_risk_label(niche.risk_level)}")
        lines.append(f"- Tahmini seri kapasitesi: {niche.estimated_series_size}+ video")
        lines.append(f"- Örnek kanallar: {', '.join(niche.example_channels) or 'Yok'}")
        lines.append("")
        lines.append("Neden umut verici:")
        for reason in niche.why_promising:
            lines.append(f"- {reason}")
        lines.append("")
        lines.append("Örnek video formatları:")
        for pattern in niche.example_formats:
            lines.append(f"- {pattern}")
        lines.append("")
        lines.append("Tekrar aranacak geniş kelimeler:")
        for term in niche.repeat_search_terms:
            lines.append(f"- {term}")
        lines.append("")
        lines.append("Başlangıç başlık açıları:")
        for angle in niche.starting_angles:
            lines.append(f"- {angle}")
        lines.append("")

    lines.append("## En Güçlü Video Fırsatları")
    lines.append("")
    lines.append("| Skor | Video | Kanal | İzlenme | Abone | Oran | Süre | Yapay zeka | Risk |")
    lines.append("| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |")
    for video in result.videos[:25]:
        analysis = result.analyses[video.video_id]
        channel = result.channels.get(video.channel_id)
        subscribers = channel.subscriber_count if channel and channel.subscriber_count is not None else "?"
        ratio = f"{analysis.views_per_subscriber:.1f}x" if analysis.views_per_subscriber is not None else "?"
        title = escape_table(f"[{video.title}]({video.url})")
        lines.append(
            "| "
            f"{analysis.opportunity_score:.1f} | "
            f"{title} | "
            f"{escape_table(video.channel_title)} | "
            f"{video.view_count:,} | "
            f"{subscribers} | "
            f"{ratio} | "
            f"{format_duration(video.duration_seconds)} | "
            f"{turkish_ai_label(analysis.ai_suitability)} | "
            f"{turkish_risk_label(analysis.factual_risk)} |"
        )
    lines.append("")
    lines.append("## Not")
    lines.append("")
    lines.append(
        "Faceless ve yapay zeka uygunluk etiketleri otomatik tahmindir; final karar öncesi örnek videoları manuel kontrol etmek iyi olur."
    )
    return "\n".join(lines)


def write_markdown_report(result: ResearchResult, output_dir: Path) -> Path:
    ensure_dir(output_dir)
    path = output_dir / "report.md"
    path.write_text(build_markdown_report(result), encoding="utf-8")
    return path


def escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
