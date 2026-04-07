# YouTube Niş Radar

Bu araç, faceless YouTube kanalı için niş araştırmasını hızlandırır.

Kod bilmeden kullanmak için önce şunu aç:

```text
BASIT_KULLANIM.md
```

## En Kolay Yol

1. `01_kurulum.bat` dosyasına çift tıkla.
2. Sonra `02_demo_calistir.bat` dosyasına çift tıkla.
3. Görsel panel için `03_paneli_ac.bat` dosyasına çift tıkla.
4. İnternetten geçici link almak için `05_internetten_paylas.bat` dosyasına çift tıkla.
5. Kalıcı online yayın için `06_kalici_yayin_rehberi_ac.bat` dosyasına çift tıkla.
6. GitHub'a yüklemek için önce `07_github_paketi_hazirla.bat` dosyasına çift tıkla.

## Program Ne Yapar?

- Girdiğin ana konuları YouTube'da araştırır.
- Son 1 yıl içindeki popüler normal videolara odaklanır.
- Çok kısa videoları istersen dışarıda bırakır.
- Kanal abonesi düşük ama videosu yüksek izlenmiş fırsatları bulur.
- Aynı formatı tekrar tekrar yapan kanalları yakalamaya çalışır.
- Yapay zeka ile üretime uygun görünen nişleri öne çıkarır.
- Latin alfabesi dışı başlıklı videoları varsayılan olarak eler.
- Sonunda rapor, tablo ve ham veri dosyası üretir.

## Çıktılar

Raporlar burada oluşur:

```text
reports\latest\
```

İçinde genelde şunlar olur:

```text
report.md
videos.csv
research_result.json
```

## Gerçek YouTube Verisi İçin

Gerçek veri çekmek için YouTube erişim anahtarı gerekir. Bunu program içinde “YouTube erişim anahtarı” alanına yazabilirsin.

Ana konu örnekleri:

```text
mythology
luxury
horror
history
business
technology
```

## Güvenlik Notu

`05_internetten_paylas.bat` internetten erişilebilen geçici bir link üretir. Bu dosya çalışırken senden panel şifresi ister. Linki herkese açık paylaşma.
