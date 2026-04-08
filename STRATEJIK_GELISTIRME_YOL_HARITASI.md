# Stratejik Geliştirme Yol Haritası

Bu doküman, YouTube Niş Radar uygulamasına eklenecek stratejik mekanikleri tarif eder. Amaç rastgele fikir üretmek değil; YouTube'da kanıtlanmış sinyalleri yakalayıp üretilebilir, dar, uzun ömürlü ve globalleşebilir fikirleri seçmektir.

## Genel Mimari

```text
Ana konu
-> YouTube veri toplama
-> Video ve kanal zenginleştirme
-> Arz-talep boşluğu
-> Niş daraltma
-> Persona
-> Fikir çiftçiliği
-> Değer denklemi
-> Evergreen puanı
-> Global hitap puanı
-> Final içerik fırsatı
```

Birincil veri kaynağı YouTube Data API v3 olmalı:

- `search.list`: Arama sonucu toplar. `q`, `type=video`, `order=viewCount`, `publishedAfter`, `videoDuration`, `regionCode`, `relevanceLanguage` kullanılır.
- `videos.list`: Video başlığı, açıklama, thumbnail, süre ve istatistikleri alır. `snippet`, `statistics`, `contentDetails` gerekir.
- `channels.list`: Abone sayısı, kanal bilgisi ve uploads playlist bilgisini alır.
- `playlistItems.list`: Kanalın son videolarını alır.
- `commentThreads.list`: İleri sürümde izleyici acısı ve itirazlarını yorumlardan çıkarmak için kullanılabilir.

YouTube Analytics API yalnızca yetkili kanal sahibi verilerinde kullanışlıdır. Rakip kanal analizi için genel Data API yeterlidir.

## 1. Arz-Talep Boşluğu ve Fırsat Dedektörü

Amaç: Kanalın abone sayısına göre aşırı yüksek izlenen videoları yakalamak.

Örnek:

```text
51.000.000 izlenme / 170.000 abone = 300x
```

Bu, kanalın mevcut kitlesinden çok daha büyük bir talebe temas ettiğini gösterir.

Önerilen matematik:

```text
views_per_subscriber = video_views / channel_subscribers

ratio_component = log10(max(ratio, 1)) / log10(100) * 45
volume_component = log10(max(views, 10000) / 10000) / log10(1000) * 35
underdog_component = channel_subs < 250k ? 20 : channel_subs < 1M ? 10 : 4

gap_score = clamp(ratio_component + volume_component + underdog_component, 0, 100)
```

Ekran:

- Fırsat puanı
- Video başlığı
- Kanal
- Abone
- İzlenme
- İzlenme / abone oranı
- Sebep
- Video linki

Mevcut kod entegrasyonu:

```text
src/youtube_niche_researcher/strategy_engine.py
detect_opportunity_gaps()
```

## 2. Niş Daraltma Hiyerarşisi

Kullanıcı "Finans" gibi geniş başlıkta kalmamalı. En az 4 seviye zorunlu olmalı:

```text
1. Geniş kategori
2. Alt alan
3. Hedef kişi
4. Tek ve net problem
```

Örnek:

```text
Finans
-> Para Kazanma
-> Maaşından memnun olmayan çalışanlar
-> YouTube ile ek gelir başlatmak istiyor ama nereden başlayacağını bilmiyor
```

Veri modeli:

```sql
CREATE TABLE niche_paths (
  id TEXT PRIMARY KEY,
  broad_category TEXT NOT NULL,
  sub_category TEXT NOT NULL,
  audience TEXT NOT NULL,
  specific_problem TEXT NOT NULL,
  final_niche TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

Mevcut kod entegrasyonu:

```text
build_niche_path()
```

## 3. Hedef Kitle Kişisi

Persona genel topluluk değil, tek insan gibi düşünülmeli.

Alanlar:

```text
Ad
Yaş
Gündelik durum
İlgi alanları
En büyük problemler
İçerik vaadi
```

Her fikir şu soruya cevap vermeli:

```text
Bu video persona'nın hangi günlük problemini çözüyor?
```

Veri modeli:

```sql
CREATE TABLE personas (
  id TEXT PRIMARY KEY,
  niche_path_id TEXT,
  name TEXT,
  age_range TEXT,
  daily_context TEXT,
  interests_json TEXT,
  pains_json TEXT,
  content_promises_json TEXT
);
```

Mevcut kod entegrasyonu:

```text
generate_persona()
```

## 4. Fikir Çiftçiliği ve Karıştırılabilir Nişler

Amaç: Bir nişte çalışan başlık iskeletini başka nişe taşımak.

Örnek:

```text
Kaynak: Kripto
Başlık: En hızlı kazandıran 10 coin
Hedef: İş fikirleri
Çıktı: En hızlı kazandıran 10 iş fikri
```

Algoritma:

```text
1. Başlıktaki paket tipini bul: liste, merak açığı, nasıl yapılır, neden anlatısı.
2. Kaynak nesneyi bul: coin, hisse, egzersiz, araç, uygulama.
3. Hedef niş nesnesiyle değiştir.
4. Vaadi koru: hızlı kazandıran, kolay başlayan, gizli gerçek, en pahalı, en riskli.
5. Son başlığı değer denkleminden geçir.
```

Veri modeli:

```sql
CREATE TABLE idea_adaptations (
  id TEXT PRIMARY KEY,
  source_niche TEXT,
  target_niche TEXT,
  original_title TEXT,
  adapted_title TEXT,
  pattern TEXT,
  score REAL,
  created_at TEXT
);
```

Mevcut kod entegrasyonu:

```text
adapt_idea()
```

## 5. Video Değeri ve Fikir Filtreleme

Değer denklemi:

```text
(Rüya Sonucu x Başarı Olasılığı) / (Zaman Zarfı x Çaba)
```

Uygulama skoru:

```text
value_score = clamp(raw_value * 10, 0, 100)
checklist_score = geçen_madde_sayısı / 5 * 100
total_score = value_score * 0.65 + checklist_score * 0.35
```

5'te 5 kuralı:

```text
1. Fikir heyecanlandırıyor mu?
2. Mümkün mü?
3. İzlenme kanıtı var mı?
4. Paketlenebilir mi?
5. Genel çekiciliği var mı?
```

Karar:

```text
75+  = yayına aday
55-74 = iyileştir
0-54 = ele
```

Veri modeli:

```sql
CREATE TABLE idea_scores (
  id TEXT PRIMARY KEY,
  idea_title TEXT,
  dream_result INTEGER,
  success_probability INTEGER,
  time_window INTEGER,
  effort INTEGER,
  checklist_json TEXT,
  total_score REAL,
  verdict TEXT
);
```

Mevcut kod entegrasyonu:

```text
score_idea_value()
```

## 6. Evergreen İçerik Puanlayıcısı

Pozitif sinyaller:

```text
history
ancient
mythology
explained
documentary
beginner
basics
how to
why
psychology
business model
```

Negatif sinyaller:

```text
today
breaking
latest
2026
drama
rumor
leak
update
news
```

Skor:

```text
evergreen_score = 55 + pozitif_sinyal * 8 - negatif_sinyal * 12
```

Veri modeli:

```sql
CREATE TABLE evergreen_scores (
  id TEXT PRIMARY KEY,
  idea_title TEXT,
  score REAL,
  label TEXT,
  positive_signals_json TEXT,
  negative_signals_json TEXT
);
```

Mevcut kod entegrasyonu:

```text
score_evergreen()
```

## 7. Global Hitap Analizi

Amaç: İçerik yerel mi kalır, yoksa dil/kültür bariyeri düşük şekilde global büyüyebilir mi?

Girdi sinyalleri:

```text
Dil olmadan görselle anlaşılabilirlik
Tek kültüre bağlılık
Çeviriye uygunluk
Alım gücü yüksek pazarlara uygunluk
Üretim karmaşıklığı
```

Skor:

```text
global_score =
  visual_without_language * 0.30
  + (10 - culture_specificity) * 0.20
  + translation_ease * 0.20
  + high_cpm_market_fit * 0.20
  + (10 - production_complexity) * 0.10
```

Veri modeli:

```sql
CREATE TABLE global_appeal_scores (
  id TEXT PRIMARY KEY,
  niche_id TEXT,
  visual_without_language INTEGER,
  culture_specificity INTEGER,
  translation_ease INTEGER,
  high_cpm_market_fit INTEGER,
  production_complexity INTEGER,
  score REAL,
  label TEXT
);
```

Mevcut kod entegrasyonu:

```text
score_global_appeal()
```

## Final Ağırlıklı Skor

İleri sürümde bütün sinyaller tek skor altında birleşmeli:

```text
final_score =
  opportunity_gap_score * 0.30
  + idea_value_score * 0.25
  + evergreen_score * 0.20
  + global_appeal_score * 0.15
  + packaging_score * 0.10
  - factual_risk_penalty
```

## UI/UX Akışı

Araştırma ekranı:

- Ana konu gir
- Son kaç güne bakılsın
- Her aramada kaç video incelensin
- Yabancı alfabelerdeki başlıkları ele
- Araştırmayı başlat

Strateji Laboratuvarı:

- Arz-talep fırsat tablosu
- Niş daraltma formu
- Persona kartı
- Fikir çiftçiliği formu
- Değer denklemi puanlayıcı
- Evergreen puanlayıcı
- Global hitap puanlayıcı

Final karar ekranı:

- En iyi 5 fikir
- Her fikir için fırsat puanı
- Değer puanı
- Evergreen puanı
- Global puanı
- Risk etiketi
- İlk 10 video başlığı önerisi

## Geliştirme Aşamaları

Sürüm 1:

- Rule-based strateji motoru
- Streamlit içinde Strateji Laboratuvarı
- Arz-talep boşluğu tablosu
- Niş daraltma
- Persona üretimi
- Fikir uyarlama
- Değer denklemi
- Evergreen ve global puan

Sürüm 2:

- SQLite ile kayıt sistemi
- Fikirleri kaydet / karşılaştır
- Son araştırmayı geçmiş araştırmayla kıyasla
- Her niş için final içerik planı üret

Sürüm 3:

- LLM destekli başlık format madenciliği
- Thumbnail pattern analizi
- Yorumlardan persona acısı çıkarımı
- Çoklu pazar karşılaştırması: US, UK, CA, AU
- Haftalık otomatik niş radar raporu

