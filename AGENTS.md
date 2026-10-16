# MamidLabs · Geliştirici ve yapay zekâ ajanları için altyapı rehberi (Linux)

Bu dosya MamidLabs Linux sürümü üzerinde çalışan geliştiriciler ve yapay zekâ
ajanları için tek doğru kaynaktır. Kod tabanının nasıl başlatıldığını, parçaların
nasıl konuştuğunu, nerede ne durduğunu ve bilinen tuzakları anlatır.

> **Zorunlu kural:** Yeni bir özellik eklediğinde, bir davranışı değiştirdiğinde ya
> da yeni bir tuzak bulduğunda **aynı commit'te** bu dosyayı güncelle: ilgili
> bölümü düzelt ve en alttaki [Değişiklik günlüğü](#15-değişiklik-günlüğü)'ne bir
> satır ekle. Kullanıcıya görünen değişiklikler `CHANGELOG.md`'ye de yazılır. Kod
> ile bu dosya çelişirse **kod doğrudur**; çelişkiyi fark eden bu dosyayı düzeltir.

Kullanıcıyla iletişim dili **Türkçe**dir. Kod yorumları ve betik metinleri Türkçedir.

---

## 1. Ürün tek paragrafta

MamidLabs, Linux'ta tamamen yerel çalışan çok modlu bir yapay zekâ çalışma
alanıdır. Tek bir Qt6 penceresinde sohbet, web araması, belge okuma/üretimi, OCR,
görsel anlama, görsel üretimi, fotoğraf düzenleme, video üretimi, grafik çizimi ve
ses dökümü sunar. Dil modeli `llama.cpp` (`llama-server`), görsel/video modelleri
`ComfyUI` üzerinde, kullanıcının NVIDIA ekran kartında çalışır. OpenAI, Claude,
Gemini, DeepSeek ve OpenAI uyumlu özel uçlar isteğe bağlı API sağlayıcılarıdır.
Depo: `github.com/workaybarsh/mamidlabs_linux`. Varsayılan kurulum kökü
`~/.local/share/mamidlabs`.

Bu sürüm, Windows sürümünün (`MamidLabsTR` / `MamidLabsENG`) **Linux portudur**:
WinForms/PowerShell yerine **Python 3.12 + PySide6 (Qt6)**. Sabitler, davranışlar
ve araç kümesi Windows sürümüyle birebir tutulur.

## 2. Depo haritası

| Yol | İçerik |
|---|---|
| `mamidlabs/__main__.py` | Giriş noktası: `doctor`, `profiles`, `manage` alt komutları; aksi halde GUI |
| `mamidlabs/ui/app.py` | Qt6 `QApplication` + ana pencere kurulumu |
| `mamidlabs/ui/main_window.py` | Ana pencere, sohbet, profil/sağlayıcı seçicileri, çipler, `TurnWorker`/`ManageWorker` |
| `mamidlabs/ui/settings_dialog.py` | API bağlantıları penceresi, anahtar doğrulama |
| `mamidlabs/ui/theme.py` | Qt stil sayfası |
| `mamidlabs/core/paths.py` | XDG kurulum kökü ve tüm yollar |
| `mamidlabs/core/settings.py` | `api.json` deposu (atomik yazım, `0600`), `SecretStore`, `secret_backend` |
| `mamidlabs/core/profiles.py` | Profil kataloğu, takma adlar, hedef yollar, eksik dosyalar |
| `mamidlabs/core/providers.py` | Sağlayıcı tablosu, OpenAI ↔ Claude dönüştürücüleri, akış (SSE) |
| `mamidlabs/core/manage.py` | `ModelManager`: başlat/durdur, VRAM kapısı, `server_args`, ComfyUI/orphan temizliği, `FileLock` |
| `mamidlabs/core/inference.py` | `InferenceEngine`: sohbet döngüsü, sistem istemi, araç döngüsü, onay, sıkıştırma, web dürüstlüğü |
| `mamidlabs/core/tools.py` | `ToolRegistry` (kapılar + işleyiciler), `WebTracker`, `MediaBridge` |
| `mamidlabs/core/chart.py` | matplotlib grafik üretimi + güvenli ifade çözümleyici |
| `mamidlabs/core/runner.py` | `WorkerRunner`: işçileri JSON stdin/stdout ile çalıştırır |
| `mamidlabs/workers/` | Platformdan bağımsız Python işçileri (aşağıya bakın) |
| `scripts/install-mamidlabs.sh` | Aşamalı kurulum |
| `scripts/manage-mamidlabs.sh` | Model/ComfyUI yönetimi, doctor, profiles |
| `scripts/uninstall-mamidlabs.sh` | Tam kaldırma (kök dışına dokunmaz) |
| `scripts/smoke-test.sh` | Gerçek modellerle uçtan uca doğrulama |
| `packaging/mamidlabs.desktop`, `packaging/mamidlabs.svg` | Masaüstü başlatıcı ve simge |
| `requirements/{app,imagegen,asr,ocr}.txt` | Python paketleri (sabit sürümler) |
| `tests/` | pytest (78 test) |
| `docs/` | `kurulum.md`, `teknik-notlar.md` |
| `.github/workflows/tests.yml` | CI (ubuntu-latest, Python 3.12) |
| `AGENTS.md` | Bu rehber. Kurulum köküne kopyalanmaz. |

### İşçiler (`mamidlabs/workers/`)

Tek-atımlık JSON stdin/stdout sözleşmesi. Her işçi kendi sanal ortamında çalışır.

| İşçi | Ortam | İş |
|---|---|---|
| `mamidlabs-agent-tools.py` | app | Web araması (`ddgs`), sayfa okuma, referans görsel |
| `office-tools.py` | app | PDF/Word/Excel/PPTX/ZIP/RAR okuma, PDF/DOCX/PPTX/XLSX üretimi |
| `ocr-tools.py` | ocr | PaddleOCR |
| `media-tools.py` | imagegen | Video kare çıkarma (PyAV) |
| `api-media.py` | app | API ile görsel/video üretimi |
| `hf-hub.py` | app | Hugging Face indirme (boyut doğrulamalı) |
| `mtp_inject.py` | app | LITE GGUF'una MTP/nextn başlığı ekleme |
| `whisper-tools.py` | asr | Ses dökümü (`transcriber/` paketini çağırır) |
| `transcriber/` | asr | faster-whisper + AST + pyannote hattı |
| `_root.py` | — | İşçilerin kurulum kökünü okuması (`MAMIDLABS_ROOT` → XDG) |

## 3. Kurulum kökü düzeni

```
~/.local/share/mamidlabs/
  llama.cpp/b10998/llama-server     sabit llama.cpp yapısı
  models/                           GGUF dil modelleri (+ mmproj)
  ComfyUI/                          sabit commit; custom_nodes: ComfyUI-GGUF, comfyui-krea2edit
  venv/{app,imagegen,asr,ocr}/      Python ortamları (bin/python)
  tools/{hf-home,downloads,pip-cache,backup}/
  settings/api.json                 tüm kullanıcı ayarları (gizli anahtarlar 0600)
  chats/  outputs/{images,videos,documents,charts,refs,thumbs,input}/
  logs/                             llama-server-*.std{out,err}.log, comfyui.*.log, audit.jsonl
  mamidlabs-launch                  başlatıcı
```

Windows'ta olduğu gibi **gömülü bir çalışma zamanı yok** (`runtime/` yoktur):
uygulama sistem Python'u ile çalışır.

## 4. Başlatma zinciri

1. `.desktop` → `~/.local/share/mamidlabs/mamidlabs-launch`.
2. Başlatıcı: `MAMIDLABS_ROOT` ayarlar, `venv/app/bin/python -m mamidlabs` çalıştırır.
3. `mamidlabs/__main__.py` argümanları ayrıştırır; alt komut yoksa `ui/app.py:main`.
4. `ui/app.py`: `Paths`, `Settings`, `QApplication`, `MainWindow`.
5. `MainWindow` yolları hazırlar, `ModelManager`/`ToolRegistry`/`InferenceEngine` kurar.
6. Kullanıcı profili seçip **Modeli başlat**'a basınca `ManageWorker` → `ModelManager.start`.
7. Uygulama kapanınca sunucu ve boştaki ComfyUI kapatılır (VRAM boşalır).

## 5. Süreçler ve portlar

| Süreç | Port | Sahibi |
|---|---|---|
| `llama-server` | 8080 | `core/manage.py` (`ModelManager`) |
| ComfyUI | 8188 | medya köprüsü / `manage-mamidlabs.sh comfy` |
| Ses döküm işçisi | rastgele (127.0.0.1) | `core/inference.py` |

**Profiller** (`core/profiles.py`; takma adlar Windows'la aynı):

| Profil | Alias | Önemli bayraklar |
|---|---|---|
| MAX | `qwen3.8-27b-max` | ctx 32768, predict 8192, gpu-layers 99, q4_0 KV, cache-reuse 256, batch 512/256, threads 6/12, `--mmproj --no-mmproj-offload --image-min-tokens 1024`, `--reasoning-effort xhigh`, MTP varsa `--spec-type draft-mtp` |
| FLASH | `qwen3.8-27b-flash` | aynı dosyalar; `--reasoning-effort low` |
| LITE | `qwen3.5-9b-lite` | ctx `liteContext` (32768), predict 8192, batch 256/128, threads 4/8, `--image-min-tokens 512`, `--reasoning-effort low`, MTP varsa `--spec-type draft-mtp` |

MAX ve FLASH aynı dosyaları kullanır → arayüzde tek "Qwen3.8 MAX" girdisi
(`catalog_for_display`). Kimliğe göre arama tam kataloğu (`get_profile`) kullanır.

**MTP.** `--spec-type draft-mtp` yalnızca GGUF gerçekten MTP/`nextn` katmanı
taşıyorsa eklenir (`manage.gguf_has_mtp`); taşımayan modele verilirse llama.cpp
açılmaz. LITE'ın 9B GGUF'u başlığı dönüşümde kaybeder, indirmede `mtp_inject.py`
ile geri eklenir. `settings.mtp=false` ile kapatılır.

**VRAM kapısı** (`manage.ModelManager`): gereken = model dosyası + pay. MAX/FLASH
pay **750 MiB**, tolerans **0** (boş < gereken → hata). LITE pay **300 MiB**,
tolerans **1024 MiB** (uyarı bandı `[gereken-1024, gereken)`). Görsel projektör üç
profilde de CPU'da (`--no-mmproj-offload`), bütçeye girmez. Model yüklenmeden önce
artık GPU işçileri (`Stop-OrphanWorkers`) kapatılır.

**ComfyUI yaşam döngüsü:** varsayılan **yalnızca medya üretiminde** çalışır
(`comfyKeepAlive=false`); dil modeli yüklenmeden önce kapatılır. LITE'ta
`comfyKeepAlive=true` ile açık tutulabilir. Kaçak/mükerrer örnekler süreç
**köklerine** göre sayılır (ComfyUI bir süreç çiftidir); `:8188`'i dinleyen tek
örnek korunur.

## 6. Sohbet isteğinin akışı

1. Kullanıcı gönderir → `MainWindow._send` → `TurnWorker` (`QThread`).
2. `InferenceEngine.build_job_messages`: sabit `SYSTEM_PROMPT` + geçmiş. Eski
   turlardaki görsel verisi atılır, yerine not konur. Tura özel ipuçları sistem
   istemine değil, **son kullanıcı mesajının başına** eklenir (KV önbellek öneki
   bozulmasın).
3. `run_turn` olaylar üretir (`event` sinyali ile arayüze): `thinking`, `answer`,
   `status`, `tool`, `denied`, `error`, `done`, `cancelled`.
4. **Araçlar** (`core/tools.py`): `search_web`, `fetch_page`, `read_document`,
   `read_images_ocr`, `create_document`, `generate_image`, `generate_video`,
   `generate_chart`, `find_reference_image`, `ask_model`, `list_bound_files`,
   `read_bound_file`, `write_bound_file`, `run_command`. Araçlar niyete ve
   çiplere göre sunulur; üretim araçları çağrı anında yeniden denetlenir.
5. **Onay:** yazma/çalıştırma araçları `approve` geri çağrısıyla sorulur
   (`TurnWorker._approve` → `approval_needed` sinyali → `QMessageBox`). 10 dk
   zaman aşımı → red. "Tam erişim" çipi açıksa sorulmaz.
6. **`done` olayı** o turda eklenen `assistant.tool_calls` ve `tool` mesajlarını
   `data` alanında taşır; arayüz bunları kalıcı geçmişe ekler. Bu yapılmazsa
   sonraki turda istemci öneki sunucununkinden farklı olur ve bağlam baştan
   işlenir.
7. Bağlam eşiğine yaklaşılınca `compact_turn_messages` en eski araç çıktılarını
   kısaltır (mesaj silinmez; `tool_calls`/`tool` eşleşmesi bozulmaz).

### Web başarısızlığı dürüstlüğü

Karar **web denendi VE hiç başarılı çağrı olmadı** koşuluna bağlıdır
(`WebTracker.unavailable = fail_count > 0 and not success`). Kısmi başarı
(ör. 7 çağrının 4'ü başarılı) başarısızlık **sayılmaz**. ≥2 hatada web araçları
kilitlenir (`should_lock_tools = fail_count >= 2 and not success`).
`add_failure_note` başarı varsa erken döner. Güncel bilgi isteyen turda web yoksa
modelin metni kullanılmaz, dürüst mesaj gösterilir; uydurma atıflar
(`strip_fabricated_citations`) ayıklanır.

## 7. Görsel, fotoğraf düzenleme ve video

- Model `generate_image` çağırınca `MediaBridge` (arayüzün sağladığı köprü)
  ComfyUI'yi sürer. Dil modeli yalnızca istemi yazar.
- **Modlar** (`generate_image.mode`): `yeni` (metinden), `yeniden_uret` /
  `stil_referansi` (eklenen görselden), `kimlik_duzenle` (Krea 2 Identity Edit
  LoRA; **yalnızca MAX/FLASH** — 8 GB LITE'ta sunulmaz).
- Video: Wan 2.2 TI2V 5B; modlar `metin`, `gorsel`, `video`.
- Harici model dosyaları kopyalanmadan kullanılır: ComfyUI
  `--extra-model-paths-config`.
- API medya: görsel/video sağlayıcısı API ise `api-media.py`.

## 8. API sağlayıcıları

- Tek tablo: `core/providers.py`: `openai`, `claude`, `gemini`, `deepseek`,
  `custom`. Yeni sağlayıcı = tabloya bir satır (+ gerekirse dönüştürücü).
- **`custom`** ("Özel (OpenAI uyumlu)"): Ollama, LM Studio, vLLM vb. Taban adres
  ayarlardan okunur; **anahtar isteğe bağlıdır** (boşsa `Authorization` gitmez).
- **Claude:** `thinking` gönderilmez; `tool_choice` yalnızca gövdede varsa `auto`;
  `max_tokens` alt sınırı 16000; araç döngüsünde imzalı `thinking` blokları
  `ClaudeStream` ile toplanıp ilk `tool_use` kimliği üzerinden geri gönderilir.
- **DeepSeek** görsel kabul etmez; `image_url` parçaları metin notuna indirilir.
- Anahtarlar tercihen **OS anahtar zincirinde** (`keyring` / Secret Service),
  yoksa `settings/api.json` içinde `0600` izinle. `Settings.secret_backend`
  hangisinin kullanıldığını bildirir.

## 9. Profiller, katalog ve indirme

- `core/profiles.py`: her profil için dosya listesi (`target` köke göreli, `repo`,
  `revision`, `filename`, `bytes`).
- İndirme boyutları: LITE ~36 GB, MAX/FLASH ~52 GB. `hf-hub.py` boyutu `bytes` ile
  doğrular ve eksik dosyayı kaldığı yerden sürer. `HF_HOME` kökün altındadır.
- Profil durumu yalnızca dosyanın **varlığına** bakar, boyut karşılaştırmaz.
- **Profil silme:** yalnızca o profile **özel** dosyalar silinir
  (`unique_targets`); paylaşılanlar korunur. MAX ve FLASH aynı küme olduğundan
  takma ad sayılır.

## 10. Kurulum, güncelleme ve kaldırma

- `install-mamidlabs.sh [--root] [--profile] [--stage a,b] [--skip-media]
  [--skip-audio] [--skip-ocr] [--skip-models] [--no-desktop] [--no-cuda] [--force]`.
  Aşamalar: `preflight`, `layout`, `llama`, `python`, `comfyui`, `models`, `verify`.
- `layout` program dosyalarını, başlatıcıyı, `.desktop` ve simgeyi kurar; ayrıca
  `mamidlabs-launch` başlatıcısını yazar.
- Sabit sürümler: llama.cpp `b10998`, ComfyUI `b0f4b7b`, ComfyUI-GGUF `6ea2651`,
  comfyui-krea2edit `86f886d`, torch cu130.
- **Kaldırma:** `uninstall-mamidlabs.sh [--keep-user-data] [--dry-run] [--yes]`.
  Yalnızca köke, `.desktop`'a ve simgeye dokunur; sistem/kullanıcı klasörlerinde
  çalışmayı reddeder.
- **Güncelleme:** uygulamayı kapat → `git pull` → `install-mamidlabs.sh --stage layout`.
- **Sürüm ve yayım:** sürümün tek kaynağı `mamidlabs/__init__.py:__version__` ve
  `pyproject.toml:version` (eşit olmalı). Yeni sürüm: ikisini artır, `CHANGELOG.md`'ye
  bölüm ekle, `v<sürüm>` etiketini it.

## 11. Ayarlar ve kullanıcı verisi

`settings/api.json` (uygulama bellekte tutar, değişince ve çıkışta yazar;
**uygulama açıkken elle düzenleme ezilir**):

- Model seçimi: `selected`, `selectedModel`, `selectedLocalModel`, `localProfile`.
- Sağlayıcılar: `providers.<id>.{key, model, models, contextLimit, baseUrl}`.
- Kendi modellerin: `localModels`, `imageLocalModel`, `videoLocalModel`,
  `imageProvider`, `videoProvider`, `externalMediaModels`.
- Arayüz: `uiPreferences.{internet, agent, accessMode}`, `firstRunApiSettings`.
- LITE: `liteModel`, `liteContext`.
- Medya: `comfyKeepAlive` (varsayılan `false`).
- Ses: `audioEvents` (varsayılan `true`).
- Diğer: `mtp` (varsayılan `true`), `boundFolder`.
- Gizli anahtarlar: OS anahtar zinciri ya da bu dosyada (`0600`).

Sohbetler `chats/` altında saklanır. `logs/audit.jsonl`: araç çağrıları kaydı
(içerik değil; yol/komut kimliği).

## 12. Testler

```bash
python -m pip install pytest -r requirements/app.txt
python -m pytest -q          # 78 test; PySide6 gerektirmez (GUI içe aktarılmaz)
./scripts/smoke-test.sh --profile flash
```

- `conftest.py` `MAMIDLABS_ROOT`'u geçici bir köke yönlendirir; testler
  `__file__`'dan bağımsız çalışır.
- Testler PySide6'yı **içe aktarmaz**; çekirdek mantık saf Python'dur. GUI
  yalnızca gerçek bir masaüstünde (smoke testinin arayüz adımlarında) çalışır.
- `manage.FileLock` Linux'ta `fcntl`, Windows'ta `msvcrt` kullanır (testler
  Windows'ta da içe aktarılabilir).
- **Smoke testi adımları:** `doctor`, `sunucu_baslat`, `saglik`, `sohbet`,
  `grafik`, `cevrimdisi`, `mtp`, `ocr`, `gorsel`, `video`, `sunucu_durdur`.
  Sonuç `logs/smoke-test-son.json`'a yazılır.
- **CI:** her push/PR'da `tests.yml` (ubuntu-latest, Python 3.12).

## 13. Donanım gerçekleri (ölçülmüş)

| | 16 GB MAX/FLASH | 8 GB LITE |
|---|---|---|
| Sohbet | ~42–58 tok/s (MTP açık) | ~97 tok/s (16 GB'ta MTP ile) |
| Görsel (`yeni`) | 60–95 sn | 68–139 sn |
| Fotoğraf düzenleme | 74–160 sn | **desteklenmiyor** |
| Medya sonrası geçiş | oran ~1,0 | oran ~1,0 |

27B model GPU'da **~15350 MiB** yer kaplar (dosya 14.600 MiB; KV cache q4_0 +
hesap tamponları + MTP draft bağlamı). MAX/FLASH payı bu yüzden **750 MiB**:
model ancak tam sığacaksa yüklenir ve tüm boş VRAM'i kullanır.

**8 GB'ta `kimlik_duzenle` neden yok:** Krea2EditGroundedEncode metin/görsel
kodlayıcıyı (~5 GB) ve difüzyon modelini (~7,5 GB) aynı grafikte tutar; 5 + 7,5 GB
> 8 GB. Bu yüzden LITE'ta mod hiç sunulmaz.

**Ses dökümü ve VRAM:** ses hattı GPU'da ~3,9 GB tutar; 27B (~15350 MiB) ile aynı
16 GB karta sığmaz → döküm öncesi dil modeli kapatılır (mecburi swap). Kalan CUDA
bağlamı ~140 MiB ölçüldü; bu yüzden sıcak ses işçisi dil modeli geri yüklenmeden
önce durdurulur, tur sonunda arka planda yeniden başlar.

## 14. Kritik tuzaklar

1. **Kurulum kökünü `__file__`'dan türetme.** Linux'ta paket `site-packages`
   içinde yaşar; işçiler kökü `MAMIDLABS_ROOT` → XDG varsayılanı ile okur
   (`workers/_root.py`). İşçiye yeni yol eklerken sabit yol yazma.
2. **KV önbellek eşleşmesi.** Arayüzün sakladığı mesaj dizisi, sunucunun o turda
   işlediğiyle bayt bayt aynı olmalı. Araç çağrısı/sonucu saklanmazsa ya da sistem
   istemi tura göre değişirse bağlam her turda baştan işlenir. Tura özel metni son
   kullanıcı mesajına koy.
3. **VRAM payı profile göre** (MAX/FLASH 750 MiB tolerans 0; LITE 300 MiB tolerans
   1024 MiB). Model yüklenmeden önce boştaki ComfyUI **her zaman** kapatılır
   (MAX/FLASH'ta MTP draft bağlamı CPU'ya taşarsa sohbet ~6 tok/s'ye düşer).
   Kaçak ComfyUI örnekleri 27B'yi paylaşılan belleğe taşır.
4. **ComfyUI bir süreç çiftidir** (venv başlatıcı + base python çocuğu). Kaçak
   kararı süreç **sayısıyla** değil **kökleriyle** verilir; tek sağlıklı örnek zaten
   2 süreçtir.
5. **`fcntl` Linux'a özgüdür.** `manage.FileLock` tembel içe aktarır ve Windows'ta
   `msvcrt`'ye düşer; testler bu yüzden Windows'ta da geçer.
6. **`done.data` boş olabilir.** İşçi araç çağrısı yokken boş liste koyar; arayüz
   `if data:` koruması kullanır (boş diziyi koşulsuz birleştirme).
7. **Tek görsel kuralı.** Sohbete aynı anda yalnızca bir görsel gider (çoklu görsel
   yalnızca OCR ile).
8. **`settings/api.json`'u uygulama açıkken elle değiştirme;** çıkışta bellekteki
   kopya yazılır.
9. **`run_command` `/bin/bash -lc` ile çalışır** ve kullanıcı onayı ister. Kabuk
   kaçışları Windows'taki `.cmd` tuzaklarından farklıdır; komutu tek satır tut.
10. **PySide6 yalnızca gerçek masaüstünde gerekir.** Çekirdek testler GUI'yi içe
    aktarmaz; CI'da PySide6 kurulmadan da geçer.
11. **Sürüm iki yerde:** `mamidlabs/__init__.py:__version__` ve
    `pyproject.toml:version`. İkisini birlikte artır.
12. **`.desktop` başlatıcısı `@ROOT@` yer tutucusu içerir;** kurulum `sed` ile
    gerçek kökle değiştirir. Doğrudan kopyalamayın.

## 15. Değişiklik yaparken kontrol listesi

- [ ] İlgili testleri çalıştır; yeni davranışa test ekle (`python -m pytest -q`).
- [ ] Kullanıcıya görünen metin Türkçe ve doğru karakterlerle mi?
- [ ] Kurulum/kaldırma etkisi: yeni dosya ya da klasör kökün dışına yazıyor mu?
      Yazıyorsa kaldırıcıya ekle. Varsayılan olarak her şey kökün altında kalmalı.
- [ ] `README.md`, `docs/kurulum.md`, `docs/teknik-notlar.md`, `CHANGELOG.md` ve
      **bu dosya** güncel mi?
- [ ] Sunucu argümanları ya da profil sabitleri değişti mi? (Windows sürümüyle
      hizayı koru.)
- [ ] Sürüm çıkarılacaksa: `__version__` + `pyproject.toml`, CHANGELOG bölümü ve
      `v<sürüm>` etiketi aynı mı?

## 16. Değişiklik günlüğü

Her özellik/değişiklik için bir satır ekle (en yeni üstte).

| Tarih | Değişiklik | Dosyalar |
|---|---|---|
| 2026-10-16 | **Linux sürümü ilk kez yazıldı (1.0.0).** Windows sürümü (PowerShell + WinForms) Linux'ta çalışmadığı için uygulama tek dilde (Python 3.12 + PySide6/Qt6) baştan yazıldı; sabitler, davranışlar ve araç kümesi Windows sürümüyle birebir korundu. Çekirdek (`paths`, `settings`, `profiles`, `providers`, `manage`, `inference`, `tools`, `chart`, `runner`), Qt6 arayüzü, taşınan Python işçileri, bash kurulum/yönetim/kaldırma/smoke betikleri, `.desktop` + simge, dokümanlar ve 78 test eklendi. Windows'a özgü parçalar Linux karşılıklarıyla değiştirildi: DPAPI → OS anahtar zinciri / `0600`; gömülü PowerShell 7 → sistem Python; WinForms → Qt6; `System.Drawing` → matplotlib; `%ProgramFiles%\7-Zip` → PATH'teki `7z`/`7za`; PDF yazı tipleri → DejaVu. | tümü |
