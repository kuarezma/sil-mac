# ⚡ SIL (`sil-mac`)
> **Next-Gen macOS Deep Optimizer, AI Model Hunter & Developer Powerhouse (v2.0.0 PRO)**  
> *Mole (`mo`) alternatifi: 24-bit TrueColor Cyberpunk TUI, Apple Silicon Native, Gerçek Zamanlı Silme Telemetrisi ve Yapay Zeka Önbellek Avcısı.*

[![macOS](https://img.shields.io/badge/Platform-macOS%20(Apple%20Silicon%20%2F%20Intel)-00f0ff.svg?style=for-the-badge&logo=apple)](https://github.com/kuarezma/sil-mac)
[![Python](https://img.shields.io/badge/Python-3.9%2B-38bdf8.svg?style=for-the-badge&logo=python)](https://github.com/kuarezma/sil-mac)
[![License](https://img.shields.io/badge/License-MIT-10b981.svg?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Version-2.0.0%20Pro-a855f7.svg?style=for-the-badge)](https://github.com/kuarezma/sil-mac)

---

## 🌟 Neden `sil`? (Mole vs. SIL)

Popüler `mole` (`mo`) aracı basit bir Bash betiğidir ve günümüzün modern yapay zeka & geliştirici dünyasında yetersiz kalmaktadır. **`sil`**, Mole'ün tüm yeteneklerini devralır ve çok daha ileri taşır:

| Özellik / Kapsam | Mole (`mo`) | ⚡ SIL (`sil` / `nexus`) |
| :--- | :--- | :--- |
| **Görsel Tasarım & UI** | 📜 Düz metin, temel ANSI renkler | 💎 **24-bit TrueColor Cyberpunk TUI, Canlı HUD, Sparkline Grafikler & Yön Tuşları** |
| **🤖 AI & Yerel Model Radarı** | ❌ **Yok (Sıfır AI desteği)** | ✅ **Ollama, Hugging Face Hub, MLX, PyTorch, Whisper, GGUF/Safetensors & Yetim Blob Temizliği** |
| **💻 Dev Monorepo Purge** | Yalnızca `node_modules` | ✅ **Xcode DerivedData/Simulators, Android Gradle, Node, Rust (`target`), Python (`.venv`), Go, Docker** |
| **🗑️ Akıllı Kaldırıcı & Yetim Avcısı** | Basit silme | ✅ **Derin Kalıntı Tespiti + Önceden Silinmiş Uygulamaların Sahipsiz Veri Avcısı (Orphan Hunter)** |
| **⚡ Apple Silicon Telemetrisi** | Kısıtlı metin | ✅ **M-Serisi SoC, Anlık Çekirdek Matrisi (C1-C8), Unified RAM Baskısı (Pressure), Pil & NVMe Sağlığı** |
| **📡 Port & Hayalet Süreçler** | ❌ Yok | ✅ **Dinlenen TCP Portları, Bellek Sömüren Süreçler & Tek Tuşla `kill` Yeteneği** |
| **🩺 MacBook Sağlık & Derin Optimizasyon** | ❌ Yok | ✅ **0-100 Canlı Sağlık Skoru, 1-Tıkla İyileştirme, Termal Kontrol, APFS Snapshot, Font & Spotlight Onarımı, LaunchAgents Denetimi** |
| **🚀 macOS Servis Optimizasyonu** | Temel | ✅ **DNS Flush, RAM Purge, QuickLook Reset, LaunchServices Onarımı, Touch ID Sudo & Homebrew Bakımı** |
| **📊 Canlı Silme & Sonuç Raporu** | ❌ Yok | ✅ **Gerçek Zamanlı İlerleme Çubuğu + İşlem Sonu Detaylı Döküm Tablosu & Kutlama Kartı** |

---

## 🕹️ Arayüz ve Navigasyon

Terminalinizi açıp doğrudan **`sil`** yazın:

```bash
sil
```

### ⌨️ Klavye Kontrolleri
- **`↑` / `↓`** *(veya `k` / `j`)*: Seçenekler arasında dikey gezinme
- **`Space` (Boşluk)**: Çoklu seçim listelerinde öğeleri işaretle / kaldır `[✔]`
- **`a`**: Tüm öğeleri tek tuşla seç
- **`Enter`**: Seçimi onayla ve işlemi başlat
- **`Esc`** *(veya `Ctrl+C`)*: Bir önceki menüye dön / mevcut işlemi iptal et

Her ekranın başlık çerçevesi risk seviyesini gösterir: 🟢 **yeşil** = salt okunur/güvenli (Donanım Paneli, Sağlık Raporu, Denetim Günlüğü), 🟠 **turuncu** = sistemi değiştiren/geri alınması zor işlemler (Port & Süreç Radarı, Uygulama Kaldırıcı, Optimizasyon), **camgöbeği** = standart önbellek/dosya temizliği (her zaman kendi onayıyla korunur).

---

## 🚀 Modüller ve Doğrudan Komutlar

İster interaktif menüden seçim yapın, isterseniz doğrudan alt modülü çalıştırın:

```bash
sil            # 🎛️ Ana interaktif kontrol merkezini açar
sil health     # 🩺 MacBook Sağlık Raporu & Derin Optimizasyon (0-100 Sağlık Skoru, 1-Tıkla İyileştirme)
sil optimize   # 🚀 macOS Servis Optimizasyonu, RAM Purge, DNS, QuickLook, Font & APFS Bakımı
sil ai         # 🤖 AI & Yerel Model Radarı (Hugging Face, Ollama, MLX, Torch, Whisper)
sil dev        # 💻 Geliştirici Önbellekleri (Xcode, Android, Node, Rust, Python, Go)
sil clean      # 🧹 macOS Sistem Önbellekleri, Günlükler, Tarayıcılar, Çöp Kutusu
sil apps       # 🗑️ Kalıntısız Uygulama Kaldırıcı ve Silinmiş Uygulama Artık Avcısı
sil status     # ⚡ Apple Silicon SoC, Çekirdek Matrisi, RAM Baskısı, Pil ve NVMe SSD
sil ports      # 📡 Dinlenen TCP Portları, Bellek Sömüren Süreçler ve Sonlandırma (Kill)
sil quick      # ✨ Hızlı & Güvenli Akıllı Temizlik
sil log        # 🗒️ Silme Denetim Günlüğünü görüntüle (ne, ne zaman, nereden silindi)
```

### 🧪 Simülasyon Modu (`--dry-run`)

Herhangi bir modülü, hiçbir dosyayı gerçekten silmeden ne olacağını görmek için `--dry-run` ile çalıştırabilirsiniz:

```bash
sil clean --dry-run
sil quick --dry-run
```

Simülasyon modunda öğeler seçilip "silme" onaylanır, gerçek boyut hesaplanır ve rapor gösterilir — ama disk üzerinde hiçbir şey değişmez, ve işlem denetim günlüğüne yazılmaz.

### ⚙️ Yapılandırma (`config.json`)

Nexus ilk çalıştırmada `~/Library/Application Support/Nexus/config.json` dosyasını varsayılan değerlerle oluşturur. Bu dosyayı elle düzenleyerek tarama dizinlerini ve boyut eşiklerini özelleştirebilirsiniz — örneğin `dev_cleaner.scan_dirs` listesine kendi proje klasörünüzü ekleyebilir veya `ai_radar.loose_model_threshold_mb` eşiğini düşürebilirsiniz. Dosya bozuk/geçersiz olursa Nexus sessizce varsayılanlara döner, çökmez.

### 🗒️ Denetim Günlüğü

Her gerçek silme işlemi `~/Library/Application Support/Nexus/deletion_log.jsonl` dosyasına kaydedilir (zaman, kategori, orijinal konum, boyut, durum). Bu bir "geri al" mekanizması değildir — Nexus alanı hemen boşaltmak için dosyaları kalıcı olarak siler — ama yanlışlıkla silinen önemli bir şeyi Time Machine gibi gerçek bir yedekten tam yoluyla geri kurtarmanızı sağlar. Son kayıtları görmek için:

```bash
sil log
```

---

## 📦 Kurulum (Installation)

### 1. Hızlı Kurulum (Tek Komut)
```bash
git clone https://github.com/kuarezma/sil-mac.git ~/sil-mac
cd ~/sil-mac && ./install.sh
```

### 2. Pip ile Kurulum (Geliştirici Modu)
```bash
git clone https://github.com/kuarezma/sil-mac.git
cd sil-mac
pip install -e .
```

Kurulum tamamlandığında `sil`, `nexus` ve `mo+` komutları sisteminize global olarak eklenir.

### 3. Geliştirici Bağımlılıkları & Testler

Test paketi (`pytest`) çekirdek kuruluma dahil değildir; `dev` opsiyonel grubuyla eklenir:

```bash
# uv ile (önerilen)
uv pip install -e ".[dev]"

# ya da pip ile (pyproject extras)
pip install -e ".[dev]"

# ya da düz requirements dosyasıyla
pip install -r requirements-dev.txt
```

Testleri çalıştırmak için:
```bash
pytest
```

---

## 🏗️ Proje Mimarisi

```text
sil-mac/
├── bin/
│   └── sil                      # Doğrudan çalıştırılabilir ikili kabuk
├── nexus/
│   ├── __init__.py
│   ├── main.py                  # CLI ana kontrol merkezi ve argüman ayrıştırıcı
│   ├── banner.py                # 24-bit TrueColor Cyberpunk HUD başlığı
│   ├── effects.py               # Sparkline grafikleri, gradyan motoru ve kutlama efektleri
│   ├── deletion_engine.py       # Gerçek zamanlı canlı silme akışı ve sonuç raporlama motoru
│   ├── menu_helpers.py          # Lazer hizalı yön tuşları menü kontrolcüsü (wcwidth destekli)
│   ├── ai_radar.py              # Yapay zeka modelleri ve yetim blob tarayıcısı
│   ├── dev_cleaner.py           # Çoklu ekosistem geliştirici monorepo temizleyicisi
│   ├── system_cleaner.py        # macOS sistem önbellekleri, loglar ve çöp temizleyicisi
│   ├── app_uninstaller.py       # Akıllı uygulama kaldırıcı ve sahipsiz veri avcısı
│   ├── hardware_dashboard.py    # Apple Silicon M-Serisi donanım ve telemetri paneli
│   ├── port_radar.py            # Açık TCP portları ve hayalet süreç radarı
│   ├── optimizer.py             # DNS, RAM purge, QuickLook ve sistem servis optimize edici
│   └── ui_helpers.py            # Rich tema paleti, gauge göstergeleri ve biçimlendiriciler
├── tests/                       # Kapsamlı birim test paketi (81 test, %100 izole)
│   ├── test_ai_radar.py
│   ├── test_app_uninstaller.py
│   ├── test_app_uninstaller_orphans.py
│   ├── test_app_uninstaller_scanning.py
│   ├── test_config.py
│   ├── test_deletion_engine.py
│   ├── test_dev_cleaner.py
│   ├── test_dry_run.py
│   ├── test_effects.py
│   ├── test_hardware_dashboard.py
│   ├── test_log_viewer.py
│   ├── test_main.py
│   ├── test_optimizer.py
│   ├── test_port_radar.py
│   ├── test_system_cleaner.py
│   └── test_ui_helpers.py
├── install.sh                   # Tek tuşla kurulum betiği
├── pyproject.toml               # Modern Python paketleme yapılandırması ([dev] opsiyonel grubu dahil)
├── requirements.txt             # Çekirdek (runtime) bağımlılıklar
├── requirements-dev.txt         # requirements.txt + pytest (test/geliştirme bağımlılığı)
└── LICENSE                      # MIT Lisansı
```

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) altında açık kaynak olarak lisanslanmıştır.  
Geliştirici: **Uğur Yaşayan** ([@kuarezma](https://github.com/kuarezma))

---

## Değişiklik Notları (Changelog)

- **🩺 MacBook Sağlık & Derin Optimizasyon Paketi**: 0-100 canlı donanım & kararlılık sağlık skoru, 1-Tıkla tam MacBook canlandırma/iyileştirme, APFS Time Machine snapshot temizliği (`tmutil thinlocalsnapshots`), font önbellek onarımı, Spotlight tazeleme ve yetim LaunchAgents denetleyicisi eklendi.
- **Apple Silicon Bellek & Telemetri Hassasiyeti**: macOS sayfa boyutu (`16384` bytes) dinamik tespiti eklendi, RAM katmanları gerçek değerleriyle senkronize edildi.
- **APFS Data Volume Disk Tespiti**: Depolama alanı `/System/Volumes/Data` üzerinden gerçek kullanıcı ve uygulama disk doluluğunu yansıtacak şekilde optimize edildi.
- **Gelişmiş Pil ve Güç Durumu**: `ioreg` ve `pmset` entegrasyonu ile gerçek döngü sayısı, tasarım kapasitesi ve sağlık yüzdesi hesaplaması eklendi.
- **Hızlı Temizlik Filtreleme**: `_quick_clean` içerisindeki AI yetimleri ve geçici dosya etiketlemeleri tam uyumlu hale getirildi.
- **Port ve Süreç İsimleri**: `lsof +c 0` ile süreç isimlerinin 9 karakterde kesilmesi önlendi, tam süreç adları sağlandı.
- **Modern Touch ID Sudo Entegrasyonu**: macOS Sonoma ve Sequoia uyumlu `sudo_local` mekanizması eklendi.
- **Genişletilmiş Test Paketi**: 90 adet %100 izole birim testi ile tüm modüller uçtan uca doğrulandı.

## Test

```bash
pytest
```
