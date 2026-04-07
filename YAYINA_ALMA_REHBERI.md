# Uygulamayı İnternete Açma

En sağlam yol: bu projeyi GitHub'a koyup Render gibi bir serviste yayınlamak.

Bu şekilde bilgisayarın kapalı olsa bile panel linki çalışabilir. Link herkese açılır, ama panel şifre ister.

## Hazır Ayarlar

Bu dosyaları ekledim:

```text
Dockerfile
render.yaml
.streamlit/config.toml
```

Bunlar uygulamayı sunucuda çalıştırmak için gerekli temel dosyalar.

## Render Üzerinden Yayınlama

1. GitHub'da yeni bir repo oluştur.
2. Bu klasördeki projeyi o repo'ya yükle.
3. Render hesabına gir.
4. Yeni web servis oluştur.
5. GitHub repo'nu seç.
6. Ortam değişkenlerine şunları ekle:

```text
YOUTUBE_API_KEY = YouTube erişim anahtarın
APP_PASSWORD = panel için istediğin şifre
```

7. Yayına al.

Yayın bittikten sonra Render sana bir link verir. O linki açan herkes paneli görür, ama şifreyi bilmeden içeri giremez.

## Geçici Link İstersen

Kalıcı yayınla uğraşmadan hızlıca internet linki almak için:

```text
05_internetten_paylas.bat
```

Bu yöntem bilgisayarın açık kaldığı sürece çalışır. Sağlam ve kalıcı çözüm için Render gibi bir sunucuya kurmak daha iyidir.

