# GitHub'a Yükleme ve Linkten Paylaşma Rehberi

Bu rehber kod bilmeyen kullanım için yazıldı. Yavaş yavaş git; acele edersen yanlış klasörü seçip yine büyük dosya hatası alırsın.

## 1. Gördüğün Hata Ne Demek?

GitHub şu hatayı veriyorsa:

```text
Yowza, that’s a big file. Try again with a file smaller than 25MB.
```

Bu şunu demek:

```text
Seçtiğin dosyalardan biri GitHub'ın tarayıcıdan yükleme sınırını aşıyor.
```

Bu projede büyük dosyalar şuralarda:

```text
.venv
tools
reports
```

Bunlar GitHub'a yüklenmeyecek.

## 2. Önce Temiz Paket Hazırla

Bu dosyaya çift tıkla:

```text
07_github_paketi_hazirla.bat
```

Bu işlem şu klasörü oluşturur:

```text
github_paketi
```

GitHub'a sadece bu klasörün içindeki dosyaları yükleyeceksin.

Şunu GitHub'a yükleme:

```text
github_paketi.zip
```

Zip dosyası sadece yedek/taşıma içindir. GitHub web sitesine repo dosyası olarak zip yüklemek doğru yol değil.

## 3. GitHub'da Yeni Proje Sayfası Oluştur

1. GitHub'a gir.
2. Sağ üstteki `+` işaretine bas.
3. `New repository` seç.
4. Repository name alanına şunu yaz:

```text
youtube-nis-radar
```

5. `Public` seçersen herkes kodları görebilir.
6. `Private` seçersen sadece sen görebilirsin.
7. `Add a README file` seçeneğini işaretleme.
8. `Create repository` butonuna bas.

## 4. Dosyaları GitHub'a Yükle

Repo oluşturulduktan sonra GitHub sana boş bir sayfa gösterir.

Şunu bul:

```text
uploading an existing file
```

O yazıya tıkla.

Sonra bilgisayarda şu klasörü aç:

```text
C:\Users\berat\OneDrive\Belgeler\New project\github_paketi
```

Dikkat: `New project` klasörünü komple seçme. `github_paketi` klasörünün içine gir.

`github_paketi` içindeki her şeyi seç:

```text
Ctrl + A
```

Sonra seçili dosyaları GitHub sayfasına sürükle.

Yükleme bitince sayfanın altına in ve yeşil butona bas:

```text
Commit changes
```

## 5. Bunları Asla Yükleme

Şunları seçersen hata alırsın veya proje gereksiz şişer:

```text
.venv
tools
reports
.env
github_paketi.zip
```

Özellikle şunlar büyük dosya hatası çıkarır:

```text
tools\cloudflared.exe
.venv\Lib\site-packages\...
```

## 6. GitHub Linki Uygulama Linki Değildir

Önemli nokta:

```text
GitHub = dosyaların durduğu yer
Render = uygulamanın çalıştığı yer
```

Yani GitHub'a yükleyince uygulama otomatik olarak çalışmaz. Herkesin linkten açması için Render'a bağlaman gerekir.

## 7. Render ile Online Yapma

GitHub'a yükleme bittikten sonra:

1. Render'a gir.
2. `New` butonuna bas.
3. `Web Service` seç.
4. GitHub hesabını bağla.
5. `youtube-nis-radar` reposunu seç.
6. Render proje dosyalarını otomatik görür. Çünkü bu projede `Dockerfile` ve `render.yaml` hazır.
7. Ortam değişkenleri bölümüne şunları ekle:

```text
YOUTUBE_API_KEY = YouTube erişim anahtarın
APP_PASSWORD = panel için belirleyeceğin şifre
```

8. Deploy / Create Web Service butonuna bas.
9. İşlem bitince Render sana bir link verir.

O link artık panel linkindir.

## 8. Panel Şifresi

`APP_PASSWORD` çok önemli. Çünkü uygulama online olunca linki bilen herkes panele gelmiş olur.

Örnek:

```text
APP_PASSWORD = benim-gizli-panel-sifrem
```

Bu şifreyi GitHub'a yazma. Sadece Render'ın gizli ayarlar kısmına yaz.

## 9. En Sık Yapılan Hata

Yanlış:

```text
New project klasörünün tamamını GitHub'a sürüklemek
```

Doğru:

```text
Önce 07_github_paketi_hazirla.bat çalıştır
Sonra sadece github_paketi içindekileri GitHub'a sürükle
```

Bu kadar. Takıldığın yer olursa ekran görüntüsündeki hatayı aynen at, ona göre bir sonraki adımı söylerim.

