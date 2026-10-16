# Kurulum kılavuzu (Linux)

Bu kılavuz MamidLabs'ı Linux'a kurmayı, başlatmayı, güncellemeyi ve kaldırmayı
anlatır. Ayrıntılı teknik bilgi için [teknik-notlar.md](teknik-notlar.md).

## 1. Ön koşullar

| Gereksinim | Not |
|---|---|
| Linux x86-64 | Ubuntu 22.04+/24.04, Fedora, Debian, Arch benzeri dağıtımlar |
| Python 3.11–3.13 | 3.12 önerilir. `python3 -m venv` çalışmalı (`python3-venv` paketi) |
| `git`, `curl` (veya `wget`), `unzip` | ComfyUI ve llama.cpp indirmeleri için |
| `p7zip-full` | RAR arşivi okuma (`7z`/`7za`) — isteğe bağlı |
| NVIDIA GPU + sürücü | Görsel/video üretimi ve hızlı sohbet için. CPU-only çalışır ama yavaştır |
| `libsecret` (GNOME Keyring vb.) | API anahtarlarını OS anahtar zincirinde saklamak için — isteğe bağlı |

Dağıtıma göre tek satır:

```bash
# Debian/Ubuntu
sudo apt install python3 python3-venv git curl unzip p7zip-full

# Fedora
sudo dnf install python3 git curl unzip p7zip

# Arch
sudo pacman -S python git curl unzip p7zip
```

## 2. Kurulum

```bash
git clone https://github.com/workaybarsh/mamidlabs_linux.git
cd mamidlabs_linux
./scripts/install-mamidlabs.sh --profile flash
```

`--profile` vermezseniz program dosyaları ve motorlar kurulur ama **dil modeli
indirilmez**; sonradan `./scripts/manage-mamidlabs.sh profiles` ile durumu görüp
indirebilirsiniz.

### Aşamalar

Kurulum sırayla şu aşamaları çalıştırır (`--stage` ile seçilebilir):

| Aşama | Yaptığı iş |
|---|---|
| `preflight` | Python/git/disk/GPU/7-Zip denetimi |
| `layout` | `venv/app`, uygulama paketi, başlatıcı, `.desktop` + simge |
| `llama` | Sabitlenmiş `llama.cpp` (`b10998`) `llama-server` indirir |
| `python` | `venv/imagegen`, `venv/asr`, `venv/ocr` ortamları |
| `comfyui` | Sabit commit ComfyUI + `ComfyUI-GGUF` + `comfyui-krea2edit` |
| `models` | `--profile` verilmişse dil modeli + mmproj indirir |
| `verify` | Kurulumu denetler (`python -m mamidlabs doctor`) |

Örnekler:

```bash
# Yalnızca program dosyalarını tazele (güncelleme)
./scripts/install-mamidlabs.sh --stage layout

# Medya/ses/OCR olmadan hafif kurulum
./scripts/install-mamidlabs.sh --profile lite --skip-media --skip-ocr

# Farklı köke kur
./scripts/install-mamidlabs.sh --root /opt/mamidlabs --profile max
```

## 3. İlk çalıştırma

```bash
~/.local/share/mamidlabs/mamidlabs-launch
```

ya da uygulama menüsünden **MamidLabs**.

İlk açılışta:

1. Üstteki **Profil** kutusundan profili seçin (MAX / FLASH / LITE).
2. **Modeli başlat** düğmesine basın; durum çubuğu "Hazır" olana kadar bekleyin.
3. Mesajınızı yazıp **Gönder**'e basın (veya `Ctrl+Enter`).

### Çipler

| Çip | Açıkken |
|---|---|
| **İnternet** | Web araması ve sayfa okuma araçları sunulur |
| **Ajan** | Bağlı klasör araçları ve `ask_model` sunulur |
| **Tam erişim** | Yazma/çalıştırma araçları için onay sorulmaz |

## 4. API sağlayıcıları (isteğe bağlı)

Menü → **API bağlantıları…**. openai / claude / gemini / deepseek / custom
satırlarından birini seçip anahtarı girin. Anahtarlar tercihen **OS anahtar
zincirinde** (Secret Service), yoksa `settings/api.json` içinde `0600` izinle
saklanır. `custom`, OpenAI uyumlu kendi ucunuzdur (Ollama, LM Studio, vLLM…);
taban adresi girin, anahtar isteğe bağlıdır.

## 5. Yönetim

```bash
./scripts/manage-mamidlabs.sh start [max|flash|lite]  # modeli başlat
./scripts/manage-mamidlabs.sh stop                    # durdur
./scripts/manage-mamidlabs.sh status                  # etkin profil
./scripts/manage-mamidlabs.sh comfy                   # ComfyUI başlat
./scripts/manage-mamidlabs.sh closecomfy              # boştaki ComfyUI'yi kapat
./scripts/manage-mamidlabs.sh doctor                  # kurulum denetimi
./scripts/manage-mamidlabs.sh profiles                # profil durumu
```

## 6. Güncelleme

1. Uygulamayı kapatın.
2. Depoyu çekin: `git pull`
3. Program dosyalarını tazeleyin: `./scripts/install-mamidlabs.sh --stage layout`

Kullanıcı verisi (`settings/`, `chats/`, `models/`, `outputs/`) korunur.

## 7. Kaldırma

```bash
./scripts/uninstall-mamidlabs.sh                  # tümü (onay ister)
./scripts/uninstall-mamidlabs.sh --keep-user-data # ayarlar/sohbetler/modeller kalır
./scripts/uninstall-mamidlabs.sh --dry-run        # yalnızca göster
```

## 8. Sorun giderme

| Belirti | Çözüm |
|---|---|
| "PySide6 bulunamadı" | `./scripts/install-mamidlabs.sh --stage layout` |
| "Yetersiz boş VRAM" | Masaüstü uygulamalarını/tarayıcıyı kapatın; LITE profiline geçin |
| Model yüklenmiyor | `python -m mamidlabs doctor`; günlüklere bakın: `logs/` |
| Görsel üretimi çalışmıyor | `./scripts/manage-mamidlabs.sh comfy`; ComfyUI günlükleri: `logs/comfyui.*.log` |
| Ses dökümü hata veriyor | `venv/asr` kurulu mu? `--skip-audio` ile atlanmış olabilir |
| Web araması çalışmıyor | İnternet çipini açın; çevrimdışıysa model uydurmaz, bunu bildirir |

Günlükler `~/.local/share/mamidlabs/logs/` altındadır:
`llama-server-*.std{out,err}.log`, `comfyui.{out,err}.log`, `audit.jsonl`,
`smoke-test-son.json`.
