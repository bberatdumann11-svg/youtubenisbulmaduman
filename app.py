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
from youtube_niche_researcher.strategy_engine import (
    adapt_idea,
    build_niche_path,
    detect_opportunity_gaps,
    generate_persona,
    score_evergreen,
    score_global_appeal,
    score_idea_value,
)
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
    st.session_state["last_result"] = result

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

st.divider()
st.header("Strateji Laboratuvarı")
st.write("Burada bulunan fikirleri rastgele değil, kanıtlanmış YouTube mekaniklerine göre süzebilirsin.")

last_result = st.session_state.get("last_result")

with st.expander("1. Arz-Talep Boşluğu ve Fırsat Dedektörü", expanded=False):
    st.write("Abonesine göre normalden çok izlenen videoları yakalar.")
    if last_result:
        gaps = detect_opportunity_gaps(last_result.videos, last_result.channels, last_result.analyses)
        if gaps:
            st.dataframe(
                [
                    {
                        "Fırsat puanı": gap.score,
                        "Seviye": gap.band,
                        "Video": gap.title,
                        "Kanal": gap.channel,
                        "İzlenme": gap.views,
                        "Abone": gap.subscribers,
                        "İzlenme / abone": gap.views_per_subscriber,
                        "Sebep": gap.reason,
                        "Link": gap.url,
                    }
                    for gap in gaps[:25]
                ],
                use_container_width=True,
            )
        else:
            st.info("Son araştırmada güçlü arz-talep boşluğu bulunamadı. Daha geniş konu veya daha fazla video deneyebilirsin.")
    else:
        st.info("Önce bir araştırma çalıştır. Sonuçlar burada otomatik analiz edilecek.")

with st.expander("2. Niş Daraltma Hiyerarşisi", expanded=False):
    col1, col2 = st.columns(2)
    broad_category = col1.text_input("1. Geniş kategori", value="Finans", key="niche_broad")
    monetization_angle = col2.text_input("2. Alt alan", value="Para Kazanma", key="niche_angle")
    audience = col1.text_input("3. Kime hitap ediyor?", value="Maaşından memnun olmayan çalışanlar", key="niche_audience")
    specific_problem = col2.text_input(
        "4. Tek ve net problem",
        value="YouTube ile ek gelir başlatmak istiyor ama nereden başlayacağını bilmiyor",
        key="niche_problem",
    )
    path = build_niche_path(broad_category, monetization_angle, audience, specific_problem)
    st.write("Daraltılmış niş yolu:")
    for index, level in enumerate(path.levels, start=1):
        st.write(f"{index}. {level}")
    st.success(f"Son niş: {path.final_niche}")
    if path.warning:
        st.warning(path.warning)

with st.expander("3. Hedef Kitle Kişisi", expanded=False):
    persona = generate_persona(path.final_niche, audience, specific_problem)
    st.write(f"Ad: **{persona.name}**")
    st.write(f"Yaş: **{persona.age}**")
    st.write(f"Gündelik durum: {persona.daily_context}")
    st.write("En büyük problemleri:")
    for pain in persona.biggest_pains:
        st.write(f"- {pain}")
    st.write("İçerik vaadi:")
    for promise in persona.content_promises:
        st.write(f"- {promise}")

with st.expander("4. Fikir Çiftçiliği ve Nişler Arası Uyarlama", expanded=False):
    source_niche = st.text_input("Fikrin geldiği alan", value="kripto", key="source_niche")
    target_niche = st.text_input("Kendi alanın", value="iş fikirleri", key="target_niche")
    original_title = st.text_input("Başarılı başlık örneği", value="En hızlı kazandıran 10 coin", key="original_title")
    adaptation = adapt_idea(original_title, source_niche, target_niche)
    st.write(f"Başlık iskeleti: **{adaptation.pattern}**")
    st.success(adaptation.adapted_title)
    st.caption(adaptation.why_it_might_work)

with st.expander("5. Video Değeri ve Fikir Filtreleme", expanded=False):
    col1, col2 = st.columns(2)
    dream = col1.slider("Rüya sonucu ne kadar güçlü?", 1, 10, 8)
    probability = col2.slider("Başarı olasılığı ne kadar inandırıcı?", 1, 10, 7)
    time_window = col1.slider("Sonuca ulaşma süresi ne kadar kısa?", 1, 10, 5)
    effort = col2.slider("Çaba/fedakarlık ne kadar düşük?", 1, 10, 4)
    checklist = {
        "Fikir heyecanlandırıyor mu?": st.checkbox("Fikir heyecanlandırıyor", value=True),
        "Mümkün mü?": st.checkbox("Gerçekçi ve yapılabilir", value=True),
        "İzlenme kanıtı var mı?": st.checkbox("Benzer videolarda izlenme kanıtı var", value=True),
        "Paketlenebilir mi?": st.checkbox("Kapak ve başlıkla güçlü paketlenebilir", value=True),
        "Genel çekiciliği var mı?": st.checkbox("Sadece çok dar bir kişiye değil, daha geniş kitleye de çekici", value=False),
    }
    idea_score = score_idea_value(dream, probability, time_window, effort, checklist)
    st.metric("Toplam fikir puanı", f"{idea_score.total_score}/100")
    st.write(f"Karar: **{idea_score.verdict}**")
    st.caption(idea_score.formula)
    if idea_score.missing_items:
        st.warning("Eksik kalanlar: " + ", ".join(idea_score.missing_items))

with st.expander("6. Evergreen İçerik Puanlayıcısı", expanded=False):
    evergreen_title = st.text_input("Video fikri", value="Complex Finance Explained for Beginners", key="evergreen_title")
    evergreen_desc = st.text_area("Kısa açıklama", value="A simple documentary style explanation.", key="evergreen_desc")
    evergreen = score_evergreen(evergreen_title, evergreen_desc)
    st.metric("Evergreen puanı", f"{evergreen.score}/100")
    st.write(f"Etiket: **{evergreen.label}**")
    if evergreen.positive_signals:
        st.success("Güçlü sinyaller: " + ", ".join(evergreen.positive_signals))
    if evergreen.negative_signals:
        st.warning("Geçicilik riski: " + ", ".join(evergreen.negative_signals))

with st.expander("7. Global Hitap Analizi", expanded=False):
    col1, col2 = st.columns(2)
    visual = col1.slider("Dil olmadan görselle anlaşılabilir mi?", 1, 10, 7)
    culture = col2.slider("Tek kültüre ne kadar bağlı?", 1, 10, 3)
    translation = col1.slider("Farklı dile çevirmek kolay mı?", 1, 10, 8)
    cpm = col2.slider("Alım gücü yüksek pazarlara uygun mu?", 1, 10, 7)
    complexity = col1.slider("Üretim karmaşıklığı ne kadar yüksek?", 1, 10, 5)
    global_result = score_global_appeal(
        visual_without_language=visual,
        culture_specificity=culture,
        translation_ease=translation,
        high_cpm_market_fit=cpm,
        production_complexity=complexity,
    )
    st.metric("Global hitap puanı", f"{global_result.score}/100")
    st.write(f"Etiket: **{global_result.label}**")
    for signal in global_result.signals:
        st.success(signal)
    for warning in global_result.warnings:
        st.warning(warning)
