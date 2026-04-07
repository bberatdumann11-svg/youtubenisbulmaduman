from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from youtube_niche_researcher.demo import build_demo_result
from youtube_niche_researcher.display import turkish_ai_label, turkish_risk_label
from youtube_niche_researcher.exporters import export_csv, export_json
from youtube_niche_researcher.pipeline import ResearchConfig, run_research
from youtube_niche_researcher.report_generator import build_markdown_report, write_markdown_report
from youtube_niche_researcher.youtube_api import YouTubeApiError, YouTubeClient


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def require_panel_password() -> None:
    password = os.getenv("APP_PASSWORD", "").strip()
    if not password or st.session_state.get("panel_unlocked"):
        return

    st.title("YouTube Niş Radar")
    st.info("Bu panel internete açılmış. Devam etmek için belirlediğin şifreyi gir.")
    entered = st.text_input("Panel şifresi", type="password")
    if st.button("Giriş yap", type="primary"):
        if entered == password:
            st.session_state["panel_unlocked"] = True
            st.rerun()
        else:
            st.error("Şifre yanlış.")
    st.stop()


load_dotenv(Path(".env"))
st.set_page_config(page_title="YouTube Niş Radar", layout="wide")
require_panel_password()

st.title("YouTube Niş Radar")
st.write("Geniş konuları gir, sistem YouTube'da fırsat olabilecek kanal ve video modellerini bulsun.")

with st.sidebar:
    st.header("Araştırma Ayarları")
    api_key = st.text_input(
        "YouTube erişim anahtarı",
        value=os.getenv("YOUTUBE_API_KEY", ""),
        type="password",
        help="YouTube verisini çekmek için gerekli anahtar. Yoksa aşağıdaki örnek veri seçeneğiyle deneyebilirsin.",
    )
    topic_text = st.text_area(
        "Ana konular",
        value="mythology\nluxury",
        help="Her satıra bir konu yaz. Örnek: mythology, luxury, horror, history.",
    )
    days = st.number_input("Son kaç güne bakılsın?", min_value=30, max_value=1095, value=365, step=30)
    videos_per_search = st.slider(
        "Her aramada kaç video incelensin?",
        min_value=5,
        max_value=50,
        value=20,
        step=5,
    )
    try_related_searches = st.checkbox(
        "Benzer aramaları da dene",
        value=False,
        help="Örneğin mythology yazınca mythology documentary, mythology explained gibi ek aramalar da yapılır.",
    )
    include_shorts = st.checkbox("Kısa videoları da dahil et", value=False)
    only_english_titles = st.checkbox(
        "Yabancı alfabelerdeki başlıkları ele",
        value=True,
        help="Açık kalırsa टाइटैनिक का सच gibi Latin alfabesi dışı başlıklı videolar rapora girmez.",
    )
    use_demo = st.checkbox("YouTube anahtarı olmadan örnek verilerle dene", value=False)
    run = st.button("Araştırmayı başlat", type="primary")

if run:
    topics = [line.strip() for line in topic_text.splitlines() if line.strip()]
    try:
        if use_demo:
            result = build_demo_result()
        else:
            if not api_key:
                st.error("YouTube erişim anahtarı gerekli. Anahtarın yoksa örnek verilerle deneyebilirsin.")
                st.stop()
            if not topics:
                st.error("En az bir ana konu gir.")
                st.stop()
            config = ResearchConfig(
                seed_keywords=topics,
                days_back=int(days),
                max_search_results_per_query=int(videos_per_search),
                expand_queries=try_related_searches,
                exclude_shorts=not include_shorts,
                exclude_non_latin_titles=only_english_titles,
            )
            with st.spinner("YouTube verileri toplanıyor, kanallar inceleniyor ve fırsatlar puanlanıyor..."):
                result = run_research(YouTubeClient(api_key), config)
    except YouTubeApiError as exc:
        st.error(str(exc))
        st.stop()

    output_dir = Path("reports/latest")
    report_path = write_markdown_report(result, output_dir)
    csv_path = export_csv(result, output_dir)
    json_path = export_json(result, output_dir)

    st.success(f"Rapor hazır: {report_path}")
    st.caption(f"Tablo dosyası: {csv_path} | Ham veri: {json_path}")

    st.subheader("En Umut Verici Nişler")
    for niche in result.niches:
        with st.expander(f"{niche.name} - {niche.score}/100", expanded=True):
            st.write(f"Yapay zeka uygunluğu: **{turkish_ai_label(niche.ai_suitability)}**")
            st.write(f"Risk seviyesi: **{turkish_risk_label(niche.risk_level)}**")
            st.write(f"Tahmini seri kapasitesi: **{niche.estimated_series_size}+ video**")
            st.write("Neden umut verici:")
            for reason in niche.why_promising:
                st.write(f"- {reason}")
            st.write("Örnek video formatları:")
            for pattern in niche.example_formats:
                st.write(f"- {pattern}")
            st.write("Başlangıç başlık fikirleri:")
            for angle in niche.starting_angles:
                st.write(f"- {angle}")

    st.subheader("Video Fırsatları")
    rows = []
    for video in result.videos:
        analysis = result.analyses[video.video_id]
        channel = result.channels.get(video.channel_id)
        rows.append(
            {
                "Fırsat puanı": analysis.opportunity_score,
                "Video başlığı": video.title,
                "Kanal": video.channel_title,
                "Abone": channel.subscriber_count if channel else None,
                "İzlenme": video.view_count,
                "İzlenme / abone": analysis.views_per_subscriber,
                "Yapay zeka uygunluğu": turkish_ai_label(analysis.ai_suitability),
                "Risk": turkish_risk_label(analysis.factual_risk),
                "Video linki": video.url,
            }
        )
    st.dataframe(rows, use_container_width=True)

    st.subheader("Rapor Metni")
    st.code(build_markdown_report(result), language="markdown")
else:
    st.info(
        "Sol panelden ana konuları yazıp araştırmayı başlat. YouTube erişim anahtarın yoksa örnek verilerle deneyebilirsin."
    )
