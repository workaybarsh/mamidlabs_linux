# MamidLabs — Linux

Tamamen **yerel**, çok modlu bir yapay zekâ çalışma alanı. Tek bir Qt6 penceresinde
sohbet, web araması, belge okuma/üretimi, OCR, görsel anlama, görsel üretimi,
fotoğraf düzenleme, video üretimi, grafik çizimi ve ses dökümü sunar. Dil modeli
**llama.cpp** (`llama-server`), görsel/video modelleri **ComfyUI** üzerinde,
kullanıcının **NVIDIA** ekran kartında çalışır. OpenAI, Claude, Gemini, DeepSeek
ve OpenAI uyumlu özel uçlar isteğe bağlı API sağlayıcılarıdır.

Bu depo, Windows sürümünün (`MamidLabsTR` / `MamidLabsENG`) **Linux portudur**.
WinForms/PowerShell Linux'ta çalışmadığı için uygulama tek dilde
(**Python 3.12 + PySide6/Qt6**) baştan yazılmış; aynı motorları (llama.cpp,
ComfyUI) ve aynı Python araçlarını (web, belge, OCR, medya, döküm) kullanır.

Depo: `github.com/workaybarsh/mamidlabs_linux` · Varsayılan kurulum kökü:
`~/.local/share/mamidlabs` (`MAMIDLABS_ROOT` ile değiştirilir).

---

## Özellikler

| Yetenek | Nasıl çalışır |
|---|---|
| Sohbet (akışlı) | Yerel `llama-server` (llama.cpp) ya da API sağlayıcısı; düşünme + yanıt ayrı gösterilir |
| Web araması / sayfa okuma | `ddgs` + sayfa çıkarma; **başarısızsa uydurmaz**, dürüst bildirir |
| Belge okuma / üretimi | PDF, Word, Excel, PowerPoint, ZIP, RAR okuma; PDF/DOCX/PPTX/XLSX üretimi |
| OCR | PaddleOCR (GPU görsel, CPU PDF) — isteğe bağlı bileşen |
| Görsel anlama | Modelin görsel projektörü (mmproj) ile görsel okuma |
| Görsel üretimi / düzenleme | Yerel ComfyUI (Krea-2 Turbo; kimlik düzenleme MAX/FLASH) veya API |
| Video üretimi | Yerel ComfyUI (Wan 2.2 TI2V 5B) veya API |
| Grafik çizimi | matplotlib; bar/line/pie/scatter/function (güvenli ifade çözümleyici) |
| Ses dökümü | faster-whisper `large-v3-tr` + AST ses olayları + opsiyonel konuşmacı ayrımı |
| Araç çağırma | `search_web`, `fetch_page`, `read_document`, `create_document`, `generate_image`, `generate_video`, `generate_chart`, `ask_model`, bağlı klasör araçları, `run_command` |
| Onay akışı | Yazma/çalıştırma araçları kullanıcı izni ister; "Tam erişim" çipi açıksa sorulmaz |
| API sağlayıcıları | openai, claude, gemini, deepseek, custom (OpenAI uyumlu) |

**Güvenlik davranışları (Windows sürümüyle aynı):** İstenmeden belge/görsel/video/grafik
üretilmez; web araması başarısızsa ya da İnternet kapalıyken güncel bilgi istenirse
model **uydurmak yerine** bunu açıkça bildirir; `read_document` yalnızca belge
bağlamı varken sunulur.

---

## Gereksinimler

- **Linux** (x86-64), Python **3.11–3.13** (3.12 önerilir), `git`, `curl`, `unzip`, `p7zip-full`
- **NVIDIA** GPU + sürücü (görsel/video ve hızlı sohbet için). CPU-only modda çalışır ama çok yavaştır.
- Disk: **LITE ~36 GB**, **MAX/FLASH ~52 GB** (modeller + ComfyUI + ortamlar)
- RAM: 16 GB önerilir (LITE ~8 GB'ta da çalışır)

---

## Kurulum

### Hazır paket (.deb)

En son sürümün `.deb` paketini doğrudan indirin:

- **İndir:** [`mamidlabs.deb`](https://github.com/workaybarsh/mamidlabs_linux/releases/latest/download/mamidlabs.deb)

```bash
sudo apt install ./mamidlabs.deb
mamidlabs-setup        # ya da uygulama menüsünden "MamidLabs Kurulum"
```

### Kurulum sihirbazı (önerilen)

Uygulama menüsündeki **MamidLabs Kurulum** simgesi (ya da `./scripts/mamidlabs-setup.sh`)
donanımı ölçüp uygun profili öneren bir **Qt6 sihirbazı** açar:

> dil (Türkçe / English) → karşılama → lisans → kurulum klasörü → donanım raporu →
> profil (LITE / PRO / şimdi indirme / kendi modelin–API) → (kendi modellerin) →
> (API) → (bileşenler) → hazır → kurulum → özet → bitiş

Sihirbaz dil seçimini `settings/api.json`'a yazar, kendi model yollarını ve
bileşen seçimlerini kaydeder ve gerçek işi `scripts/install-mamidlabs.sh`'e
bırakır; ilerlemeyi `logs/kurulum-adim.txt`'ten okur. Grafik masaüstü yoksa
(`DISPLAY`/`WAYLAND_DISPLAY` yoksa) anlaşılır bir mesaj verip terminal betiğini
önerir.

`.deb` paketi de sihirbazı kurar:

```bash
packaging/linux/build-deb.sh                 # packaging/linux/Output/mamidlabs_<sürüm>_all.deb
sudo apt install ./packaging/linux/Output/mamidlabs_*_all.deb
mamidlabs-setup                              # ya da uygulama menüsünden "MamidLabs Kurulum"
```

Ayrıntı: [`packaging/linux/README.md`](packaging/linux/README.md).

### Terminalden

```bash
git clone https://github.com/workaybarsh/mamidlabs_linux.git
cd mamidlabs_linux
./scripts/install-mamidlabs.sh --profile flash --language tr
```

Kurulum aşamaları: `preflight → layout → llama → python → comfyui → models → verify`.
Ayrı ayrı çalıştırmak için `--stage` kullanın; örneğin yalnızca program dosyalarını
güncellemek için:

```bash
./scripts/install-mamidlabs.sh --stage layout
```

Faydalı seçenekler:

| Seçenek | Etki |
|---|---|
| `--root <yol>` | Kurulum kökü (varsayılan `~/.local/share/mamidlabs`) |
| `--profile max\|flash\|lite` | Model indirme profili (varsayılan: indirmez) |
| `--language tr\|en` | Arayüz dili; `settings/api.json`'a yazılır |
| `--skip-media` | ComfyUI ve görsel/video bileşenlerini atla |
| `--skip-audio` | Ses dökümü ortamını (`venv/asr`) atla |
| `--skip-ocr` | OCR ortamını (`venv/ocr`) atla |
| `--skip-models` | Dil modeli indirmeyi atla |
| `--no-desktop` | `.desktop` başlatıcısını kurma |
| `--no-cuda` | CPU-only torch |
| `--force` | Var olanı yeniden kur |

Kurulum kökü düzeni:

```
~/.local/share/mamidlabs/
  llama.cpp/<build>/llama-server   sabitlenmiş llama.cpp yapısı
  models/                          GGUF dil modelleri (+ mmproj)
  ComfyUI/                         sabit commit ComfyUI + models/
  venv/{app,imagegen,asr,ocr}/     Python ortamları (her biri kendi işi için)
  tools/{hf-home,downloads,pip-cache}/
  settings/api.json                tüm kullanıcı ayarları (gizli anahtarlar 0600)
  chats/  outputs/  logs/          sohbetler, üretilen dosyalar, günlükler
  mamidlabs-launch                başlatıcı (masaüstü kısayolunun hedefi)
```

---

## Kullanım

Uygulamayı başlat:

```bash
~/.local/share/mamidlabs/mamidlabs-launch
```

Ya da uygulama menüsünden **MamidLabs** (kurulum `.desktop` başlatıcısını
`~/.local/share/applications` altına koyar).

Model yönetimi:

```bash
./scripts/manage-mamidlabs.sh start flash    # yerel modeli başlat
./scripts/manage-mamidlabs.sh stop           # durdur
./scripts/manage-mamidlabs.sh status         # etkin profil
./scripts/manage-mamidlabs.sh comfy          # ComfyUI başlat (medya için)
./scripts/manage-mamidlabs.sh closecomfy     # boştaki ComfyUI'yi kapat
./scripts/manage-mamidlabs.sh doctor         # kurulumu denetle
./scripts/manage-mamidlabs.sh profiles       # profil durumu
```

Komut satırı (GUI olmadan):

```bash
python -m mamidlabs doctor
python -m mamidlabs profiles --json
python -m mamidlabs manage start --profile lite
```

---

## Kaldırma

```bash
./scripts/uninstall-mamidlabs.sh                  # tümü (sorar)
./scripts/uninstall-mamidlabs.sh --keep-user-data # ayarlar/sohbetler/modeller kalır
./scripts/uninstall-mamidlabs.sh --dry-run        # yalnızca göster
```

Kaldırıcı yalnızca kurulum köküne, `.desktop` başlatıcısına ve simgeye dokunur;
kök dışındaki hiçbir dosyayı silmez.

---

## Donanım gerçekleri (ölçülmüş, Windows sürümünden)

| | 16 GB (RTX 5060 Ti) MAX/FLASH | 8 GB (RTX 4060 Laptop) LITE |
|---|---|---|
| Sohbet | ~42–58 tok/s (MTP açık) | ~97 tok/s (16 GB'ta MTP ile) |
| Görsel (`yeni`), uçtan uca | 60–95 sn | 68–139 sn |
| Fotoğraf düzenleme (`kimlik_duzenle`) | 74–160 sn | **desteklenmiyor** (8 GB'a sığmaz) |

ComfyUI varsayılan olarak **yalnızca medya üretiminde** çalışır ve dil modeli
yüklenmeden önce kapatılır (boşta ne VRAM ne RAM tutar).

---

## Testler

```bash
python -m pip install pytest -r requirements/app.txt
python -m pytest -q          # 152 test; PySide6 gerektirmez (Qt yalnızca sihirbaz testlerinde lazım)
```

PySide6 kuruluysa sihirbazın penceresi de başsız (`QT_QPA_PLATFORM=offscreen`)
test edilir; kurulu değilse o testler atlanır. Uçtan uca doğrulama (kurulu kökte,
gerçek modellerle):

```bash
./scripts/smoke-test.sh --profile flash
```

---

## Katkı ve geliştirme

Kod tabanının nasıl başlatıldığını, parçaların nasıl konuştuğunu ve bilinen
tuzakları **[AGENTS.md](AGENTS.md)** anlatır. Yeni bir özellik eklediğinizde
aynı commit'te `AGENTS.md` ve `CHANGELOG.md`'yi de güncelleyin.

---

## Lisans

MamidLabs kaynak kodu **PolyForm Strict License 1.0.0** ile lisanslanmıştır (kaynak-açık;
yalnızca **ticari olmayan** kullanım). Yazılımı dağıtamaz, değiştiremez veya üzerinde türev eser
üretemezsiniz; ticari kullanım için Hak Sahibinden önceden yazılı izin gerekir. Telif hakkı
Aybars Haydar Altuntaş'a aittir. Ayrıntılar için [LICENSE](LICENSE) dosyasına ve
https://polyformproject.org/licenses/strict/1.0.0 adresine bakın.
Kullanılan modeller (Qwen, Krea 2, Krea 2 Identity Edit LoRA, Wan 2.2 vb.) ve üçüncü taraf
bileşenler (llama.cpp, ComfyUI, ComfyUI-GGUF, comfyui-krea2edit vb.) kendi lisanslarına tabidir; bu
lisans onları kapsamaz.
