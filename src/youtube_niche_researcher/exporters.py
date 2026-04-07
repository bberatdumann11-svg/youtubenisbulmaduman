from __future__ import annotations

import csv
import json
from pathlib import Path

from .display import turkish_ai_label, turkish_risk_label
from .models import dataclass_to_dict
from .pipeline import ResearchResult


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def export_json(result: ResearchResult, output_dir: Path) -> Path:
    ensure_dir(output_dir)
    path = output_dir / "research_result.json"
    payload = {
        "config": dataclass_to_dict(result.config),
        "videos": [dataclass_to_dict(video) for video in result.videos],
        "channels": {key: dataclass_to_dict(value) for key, value in result.channels.items()},
        "analyses": {key: dataclass_to_dict(value) for key, value in result.analyses.items()},
        "niches": [dataclass_to_dict(niche) for niche in result.niches],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def export_csv(result: ResearchResult, output_dir: Path) -> Path:
    ensure_dir(output_dir)
    path = output_dir / "videos.csv"
    fieldnames = [
        "firsat_puani",
        "ana_konu",
        "arama_metni",
        "video_basligi",
        "kanal_adi",
        "abone_sayisi",
        "izlenme",
        "izlenme_abone_orani",
        "yayin_tarihi",
        "sure_saniye",
        "gunluk_izlenme_hizi",
        "faceless_ihtimali",
        "yapay_zeka_uygunlugu",
        "risk",
        "video_linki",
        "thumbnail_linki",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for video in result.videos:
            channel = result.channels.get(video.channel_id)
            analysis = result.analyses[video.video_id]
            writer.writerow(
                {
                    "firsat_puani": analysis.opportunity_score,
                    "ana_konu": video.seed_keyword,
                    "arama_metni": video.source_query,
                    "video_basligi": video.title,
                    "kanal_adi": video.channel_title,
                    "abone_sayisi": channel.subscriber_count if channel else None,
                    "izlenme": video.view_count,
                    "izlenme_abone_orani": analysis.views_per_subscriber,
                    "yayin_tarihi": video.published_at,
                    "sure_saniye": video.duration_seconds,
                    "gunluk_izlenme_hizi": analysis.velocity,
                    "faceless_ihtimali": analysis.faceless_probability,
                    "yapay_zeka_uygunlugu": turkish_ai_label(analysis.ai_suitability),
                    "risk": turkish_risk_label(analysis.factual_risk),
                    "video_linki": video.url,
                    "thumbnail_linki": video.thumbnail_url,
                }
            )
    return path
