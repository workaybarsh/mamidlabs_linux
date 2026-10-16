# MamidLabs Linux paketleme (.deb)

Bu klasör, MamidLabs Linux sürümünün **`.deb` paketini** üretir. Paketin içinde
uygulama kaynakları ve **kurulum sihirbazı** bulunur; paket kurulduktan sonra
uygulama menüsündeki **“MamidLabs Kurulum”** simgesi sihirbazı açar.

## Neden `.deb`

Kurulum (llama.cpp, ComfyUI, ~36–52 GB model) kullanıcıya sorularak yapılmalıdır.
Bu yüzden `.deb` *hazır bir kurulum* değil, **kurulum aracını** dağıtır:

1. `sudo apt install ./mamidlabs_1.0.0_all.deb`
2. Uygulama menüsünden **MamidLabs Kurulum** → sihirbaz:
   dil (TR/EN) → karşılama → lisans → klasör → donanım raporu → profil
   (LITE/PRO/indirme yok/kendi modelin) → (kendi modellerin) → (API) →
   (bileşenler) → hazır → kurulum → özet → bitiş.

## Derleme

```bash
packaging/linux/build-deb.sh
# çıktı: packaging/linux/Output/mamidlabs_1.0.0_all.deb
```

Seçenekler: `--output <dizin>` (çıktı yeri), `--arch <all|amd64>` (varsayılan `all`).

Gereksinim: `dpkg-deb` (`apt install dpkg-dev`). Derleme makinesinde Python
gerekmez; sürüm `mamidlabs/__init__.py` dosyasından okunur.

## Paketin yerleştirdiği dosyalar

| Yol | İçerik |
|---|---|
| `/usr/lib/mamidlabs/mamidlabs` | Python paketi (uygulama + sihirbaz + dil katalogları) |
| `/usr/lib/mamidlabs/scripts` | `install-mamidlabs.sh`, `manage-…`, `smoke-test.sh`, `mamidlabs-setup.sh` |
| `/usr/bin/mamidlabs-setup` | Sihirbaz başlatıcı (`python3 -m mamidlabs.wizard`) |
| `/usr/bin/mamidlabs` | Uygulama başlatıcı (`python3 -m mamidlabs`) |
| `/usr/share/applications/mamidlabs-setup.desktop` | Kurulum sihirbazı simgesi |
| `/usr/share/applications/mamidlabs.desktop` | Uygulama simgesi |
| `/usr/share/icons/hicolor/scalable/apps/mamidlabs.svg` | Simge |

Paket **mimariden bağımsızdır** (`Architecture: all`): içinde derlenmiş ikili yok,
yalnızca Python var. Kurulum kökü varsayılan
`~/.local/share/mamidlabs`'tır (`MAMIDLABS_ROOT` ile değişir).

## Bağımlılıklar

`Depends: python3 (>= 3.11), python3-venv, python3-pyside6.qtwidgets`

`python3-pyside6.qtwidgets` paketi Debian trixie / Ubuntu 24.04 ve sonrasında
vardır. Daha eski bir dağıtımda bu ad yoksa Qt'yi pip ile kurun:

```bash
pip install --break-system-packages PySide6
```

Qt yoksa sihirbaz `wizard.error.no_pyside` mesajını yazıp **2** koduyla çıkar;
kurulum terminalden de yapılabilir:

```bash
/usr/lib/mamidlabs/scripts/install-mamidlabs.sh --profile flash --language tr
```

## Masaüstü olmadan (sunucu/SSH)

Sihirbaz grafik masaüstü ister (`DISPLAY`/`WAYLAND_DISPLAY`); yoksa
`wizard.error.no_display` mesajıyla **1** koduyla çıkar ve terminal betiğini
önnerir. Bu davranış `mamidlabs/wizard/__main__.py` içindedir.
