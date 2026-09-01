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
| **🚀 macOS Optimizasyonu** | Temel | ✅ **DNS Flush, RAM Purge, QuickLook Reset, LaunchServices Onarımı, Touch ID Sudo** |
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
- **`q`** *(veya `Ctrl+C`)*: Bir önceki menüye dön / çıkış yap

---

## 🚀 Modüller ve Doğrudan Komutlar

İster interaktif menüden seçim yapın, isterseniz doğrudan alt modülü çalıştırın:

```bash
sil            # 🎛️ Ana interaktif kontrol merkezini açar
sil ai         # 🤖 AI & Yerel Model Radarı (Hugging Face, Ollama, MLX, Torch, Whisper)
sil dev        # 💻 Geliştirici Önbellekleri (Xcode, Android, Node, Rust, Python, Go)
sil clean      # 🧹 macOS Sistem Önbellekleri, Günlükler, Tarayıcılar, Çöp Kutusu
sil apps       # 🗑️ Kalıntısız Uygulama Kaldırıcı ve Silinmiş Uygulama Artık Avcısı
sil status     # ⚡ Apple Silicon SoC, Çekirdek Matrisi, RAM Baskısı, Pil ve NVMe SSD
sil ports      # 📡 Dinlenen TCP Portları, Bellek Sömüren Süreçler ve Sonlandırma (Kill)
sil optimize   # 🚀 DNS Temizliği, RAM Senkronizasyonu, QuickLook ve Finder Onarımı
sil quick      # ✨ Hızlı & Güvenli Akıllı Temizlik
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
├── install.sh                   # Tek tuşla kurulum betiği
├── pyproject.toml               # Modern Python paketleme yapılandırması
├── requirements.txt             # Bağımlılıklar
└── LICENSE                      # MIT Lisansı
```

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) altında açık kaynak olarak lisanslanmıştır.  
Geliştirici: **Uğur Yaşayan** ([@kuarezma](https://github.com/kuarezma))
