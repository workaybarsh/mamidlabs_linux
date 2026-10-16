# Değişiklik Günlüğü

Bu dosya kullanıcıya görünen değişiklikleri listeler. Biçim
[Keep a Changelog](https://keepachangelog.com/tr/1.1.0/) temellidir ve sürümler
[Anlamsal Sürümleme](https://semver.org/lang/tr/) izler.

Sürümün tek kaynağı `mamidlabs/__init__.py` içindeki `__version__` ve
`pyproject.toml` içindeki `version` alanıdır (ikisi eşit olmalıdır).

## [1.0.0] — 2026-10-16

### Eklendi
- **MamidLabs Linux sürümü.** Windows sürümünün (`MamidLabsTR` / `MamidLabsENG`)
  tam Linux portu: WinForms/PowerShell yerine tek dilde **Python 3.12 + PySide6
  (Qt6)** masaüstü uygulaması.
- Qt6 ana pencere: akışlı sohbet, profil/sağlayıcı/model seçicileri, İnternet /
  Ajan / Tam erişim çipleri, model başlat-durdur, araç onay penceresi.
- API bağlantıları penceresi; anahtarlar tercihen **Secret Service (keyring)**
  üzerinden, yoksa `0600` izinli ayar dosyasında saklanır.
- Komut satırı arayüzü: `python -m mamidlabs {doctor,profiles,manage}`.
- Bash kurulum/yönetim betikleri: `install-mamidlabs.sh` (aşamalı),
  `manage-mamidlabs.sh`, `uninstall-mamidlabs.sh`, `smoke-test.sh`.
- `.desktop` başlatıcısı ve SVG simge.
- Çekirdek modüller: `paths` (XDG kurulum kökü), `settings`, `profiles`,
  `providers` (OpenAI ↔ Claude dönüştürücüleri + akış), `manage`
  (`ModelManager`, VRAM kapısı, ComfyUI/orphan temizliği), `inference`
  (sohbet döngüsü, araç döngüsü, onay, bağlam sıkıştırma), `tools`
  (araç kaydı + kapılar + web başarısızlık dürüstlüğü), `chart`, `runner`.
- Python işçileri Linux'a taşındı (web, belge, OCR, medya, whisper/transcriber,
  `mtp_inject`, `hf-hub`, `api-media`); kurulum kökü artık `MAMIDLABS_ROOT`'tan
  okunur (`__file__`'dan türetilmez).
- 78 birim testi (`pytest`).

### Değişti (Windows sürümüne göre)
- Windows **DPAPI** yerine OS anahtar zinciri / `0600` dosya.
- Windows **PowerShell 7 gömülü çalışma zamanı** yerine sistem Python'u
  (kurulum kökünde `runtime/` yok).
- Windows **WinForms** yerine **Qt6**; `System.Drawing` grafikleri yerine
  **matplotlib**.
- 7-Zip yolu `7z`/`7za` (PATH); PDF yazı tipleri DejaVu; HTTP User-Agent
  `X11; Linux x86_64`.

### Korundu
- Profil takma adları (`qwen3.8-27b-max` / `-flash`, `qwen3.5-9b-lite`), model
  kimlikleri, araç adları, sunucu argüman demetleri, MTP, VRAM kapısı ve
  ComfyUI yaşam döngüsü — Windows sürümüyle birebir.
