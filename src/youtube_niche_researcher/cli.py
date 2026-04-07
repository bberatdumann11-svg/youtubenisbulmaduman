from __future__ import annotations

import argparse
import os
from pathlib import Path

from .demo import build_demo_result
from .display import turkish_ai_label, turkish_risk_label
from .exporters import export_csv, export_json
from .pipeline import ResearchConfig, run_research
from .report_generator import write_markdown_report
from .youtube_api import YouTubeApiError, YouTubeClient


def main() -> None:
    load_dotenv(Path(".env"))
    parser = build_parser()
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if args.demo:
        result = build_demo_result()
    else:
        if not args.seed:
            parser.error("En az bir ana konu verin veya --demo kullanın.")
        api_key = args.api_key or os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            parser.error("YouTube erişim anahtarı bulunamadı. .env dosyasına ekleyin veya --api-key ile verin.")
        config = ResearchConfig(
            seed_keywords=args.seed,
            days_back=args.days,
            max_search_results_per_query=args.max_results,
            region_code=args.region,
            relevance_language=args.language,
            duration_modes=args.duration or ["medium", "long"],
            expand_queries=args.expand,
            custom_queries=args.query or [],
            channel_limit=args.channel_limit,
            channel_recent_limit=args.channel_recent_limit,
            exclude_shorts=not args.include_shorts,
            exclude_non_latin_titles=not args.include_foreign_titles,
            niche_limit=args.niche_limit,
        )
        client = YouTubeClient(api_key)
        try:
            result = run_research(client, config)
        except YouTubeApiError as exc:
            raise SystemExit(str(exc)) from exc

    report_path = write_markdown_report(result, output_dir)
    csv_path = export_csv(result, output_dir)
    json_path = export_json(result, output_dir)

    print("Araştırma tamamlandı.")
    print(f"Rapor: {report_path}")
    print(f"CSV:   {csv_path}")
    print(f"JSON:  {json_path}")
    if result.niches:
        print("")
        print("Top nişler:")
        for niche in result.niches:
            print(
                f"- {niche.name}: {niche.score}/100, "
                f"{turkish_ai_label(niche.ai_suitability)}, risk={turkish_risk_label(niche.risk_level)}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Faceless YouTube niş araştırma aracı")
    parser.add_argument("seed", nargs="*", help="Ana konular. Örn: mythology luxury horror")
    parser.add_argument("--api-key", help="YouTube erişim anahtarı. Verilmezse YOUTUBE_API_KEY okunur.")
    parser.add_argument("--days", type=int, default=365, help="Kaç gün geriye bakılsın?")
    parser.add_argument("--max-results", type=int, default=25, help="Her aramada kaç video alınsın?")
    parser.add_argument("--region", default="US", help="YouTube regionCode")
    parser.add_argument("--language", default="en", help="YouTube relevanceLanguage")
    parser.add_argument(
        "--duration",
        action="append",
        choices=["short", "medium", "long", "any"],
        default=None,
        help="YouTube videoDuration filtresi. Birden fazla verilebilir.",
    )
    parser.add_argument("--expand", action="store_true", help="Benzer aramaları da dene.")
    parser.add_argument("--query", action="append", help="Ek özel arama metni. Birden fazla verilebilir.")
    parser.add_argument("--include-shorts", action="store_true", help="90 sn altı videoları filtreleme.")
    parser.add_argument("--include-foreign-titles", action="store_true", help="Latin alfabesi dışı başlıkları dahil et.")
    parser.add_argument("--channel-limit", type=int, default=20, help="Son video analizi yapılacak maksimum kanal.")
    parser.add_argument("--channel-recent-limit", type=int, default=30, help="Kanal başına son kaç video incelensin?")
    parser.add_argument("--niche-limit", type=int, default=5, help="Rapora alınacak niş sayısı.")
    parser.add_argument("--output-dir", default="reports/latest", help="Çıktı klasörü.")
    parser.add_argument("--demo", action="store_true", help="API gerektirmeyen örnek veriyle çalıştır.")
    return parser


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


if __name__ == "__main__":
    main()
