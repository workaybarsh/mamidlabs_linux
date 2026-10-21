# MamidLabs — Linux

A fully **local**, multimodal AI workspace. In a single Qt6 window it offers chat,
web search, document reading/creation, OCR, image understanding, image generation,
photo editing, video generation, chart drawing and audio transcription. The language
model runs on **llama.cpp** (`llama-server`), the image/video models on **ComfyUI**,
on the user's **NVIDIA** GPU. OpenAI, Claude, Gemini, DeepSeek and custom
OpenAI-compatible endpoints are optional API providers.

This repository is the **Linux port** of the Windows edition (`MamidLabsTR` /
`MamidLabsENG`). Because WinForms/PowerShell do not run on Linux, the application was
rewritten from scratch in a single language (**Python 3.12 + PySide6/Qt6**); it uses
the same engines (llama.cpp, ComfyUI) and the same Python tools (web, document, OCR,
media, transcription).

Repository: `github.com/workaybarsh/mamidlabs_linux` · Default install root:
`~/.local/share/mamidlabs` (override with `MAMIDLABS_ROOT`).

---

## Features

| Capability | How it works |
|---|---|
| Chat (streaming) | Local `llama-server` (llama.cpp) or an API provider; thinking + answer shown separately |
| Web search / page reading | `ddgs` + page extraction; **does not fabricate when it fails**, reports honestly |
| Document reading / creation | Reads PDF, Word, Excel, PowerPoint, ZIP, RAR; creates PDF/DOCX/PPTX/XLSX |
| OCR | PaddleOCR (GPU for images, CPU for PDF) — optional component |
| Image understanding | Reads images with the model's vision projector (mmproj) |
| Image generation / editing | Local ComfyUI (Krea-2 Turbo; identity editing MAX/FLASH) or API |
| Video generation | Local ComfyUI (Wan 2.2 TI2V 5B) or API |
| Chart drawing | matplotlib; bar/line/pie/scatter/function (safe expression evaluator) |
| Audio transcription | faster-whisper `large-v3-tr` + AST sound events + optional speaker diarization |
| Tool calling | `search_web`, `fetch_page`, `read_document`, `create_document`, `generate_image`, `generate_video`, `generate_chart`, `ask_model`, bound-folder tools, `run_command` |
| Approval flow | Write/execute tools ask for user permission; not asked when the "Full access" chip is on |
| API providers | openai, claude, gemini, deepseek, custom (OpenAI-compatible) |

**Safety behaviour (same as the Windows edition):** no document/image/video/chart is
produced unless requested; if the web search fails or current information is requested
while the internet is unavailable, the model **says so explicitly instead of making
things up**; `read_document` is only offered while there is document context.

---

## Requirements

- **Linux** (x86-64), Python **3.11–3.13** (3.12 recommended), `git`, `curl`, `unzip`, `p7zip-full`
- **NVIDIA** GPU + driver (for image/video and fast chat). Runs in CPU-only mode but is very slow.
- Disk: **LITE ~36 GB**, **MAX/FLASH ~52 GB** (models + ComfyUI + environments)
- RAM: 16 GB recommended (LITE also runs on ~8 GB)

---

## Installation

### Prebuilt package (.deb)

Download the latest version's `.deb` package directly:

- **Download:** [`mamidlabs.deb`](https://github.com/workaybarsh/mamidlabs_linux/releases/latest/download/mamidlabs.deb)

```bash
sudo apt install ./mamidlabs.deb
mamidlabs-setup        # or "MamidLabs Setup" from the application menu
```

### Setup wizard (recommended)

The **MamidLabs Setup** icon in the application menu (or
`./scripts/mamidlabs-setup.sh`) opens a **Qt6 wizard** that measures the hardware and
suggests a suitable profile:

> language (English / Türkçe) → welcome → licence → install folder → hardware report →
> profile (LITE / PRO / download later / own model–API) → (own models) →
> (API) → (components) → ready → install → summary → finish

The wizard writes the language choice into `settings/api.json`, saves its own model
paths and component choices, and leaves the real work to
`scripts/install-mamidlabs.sh`; it reads progress from `logs/kurulum-adim.txt`. When
there is no graphical desktop (no `DISPLAY`/`WAYLAND_DISPLAY`) it prints a clear
message and suggests the terminal script.

The `.deb` package installs the wizard too:

```bash
packaging/linux/build-deb.sh                 # packaging/linux/Output/mamidlabs_<version>_all.deb
sudo apt install ./packaging/linux/Output/mamidlabs_*_all.deb
mamidlabs-setup                              # or "MamidLabs Setup" from the application menu
```

Details: [`packaging/linux/README.md`](packaging/linux/README.md).

### From the terminal

```bash
git clone https://github.com/workaybarsh/mamidlabs_linux.git
cd mamidlabs_linux
./scripts/install-mamidlabs.sh --profile flash --language en
```

Installation stages: `preflight → layout → llama → python → comfyui → models → verify`.
Use `--stage` to run them separately; for example, to only update the program files:

```bash
./scripts/install-mamidlabs.sh --stage layout
```

Useful options:

| Option | Effect |
|---|---|
| `--root <path>` | Install root (default `~/.local/share/mamidlabs`) |
| `--profile max\|flash\|lite` | Model download profile (default: no download) |
| `--language en\|tr` | Interface language (default `en`); written to `settings/api.json` |
| `--skip-media` | Skip ComfyUI and the image/video components |
| `--skip-audio` | Skip the audio transcription environment (`venv/asr`) |
| `--skip-ocr` | Skip the OCR environment (`venv/ocr`) |
| `--skip-models` | Skip the language-model download |
| `--no-desktop` | Do not install the `.desktop` launcher |
| `--no-cuda` | CPU-only torch |
| `--force` | Reinstall what already exists |

Install root layout:

```
~/.local/share/mamidlabs/
  llama.cpp/<build>/llama-server   pinned llama.cpp build
  models/                          GGUF language models (+ mmproj)
  ComfyUI/                         pinned-commit ComfyUI + models/
  venv/{app,imagegen,asr,ocr}/     Python environments (each for its own job)
  tools/{hf-home,downloads,pip-cache}/
  settings/api.json                all user settings (secrets 0600)
  chats/  outputs/  logs/          chats, generated files, logs
  mamidlabs-launch                 launcher (target of the desktop shortcut)
```

---

## Usage

Start the application:

```bash
~/.local/share/mamidlabs/mamidlabs-launch
```

Or **MamidLabs** from the application menu (the installer places the `.desktop`
launcher under `~/.local/share/applications`).

Model management:

```bash
./scripts/manage-mamidlabs.sh start flash    # start the local model
./scripts/manage-mamidlabs.sh stop           # stop
./scripts/manage-mamidlabs.sh status         # active profile
./scripts/manage-mamidlabs.sh comfy          # start ComfyUI (for media)
./scripts/manage-mamidlabs.sh closecomfy     # close the idle ComfyUI
./scripts/manage-mamidlabs.sh doctor         # inspect the installation
./scripts/manage-mamidlabs.sh profiles       # profile status
```

Command line (without the GUI):

```bash
python -m mamidlabs doctor
python -m mamidlabs profiles --json
python -m mamidlabs manage start --profile lite
```

---

## Uninstallation

```bash
./scripts/uninstall-mamidlabs.sh                  # everything (asks)
./scripts/uninstall-mamidlabs.sh --keep-user-data # keeps settings/chats/models
./scripts/uninstall-mamidlabs.sh --dry-run        # only show
```

The uninstaller only touches the install root, the `.desktop` launcher and the icon;
it deletes no file outside the root.

---

## Hardware facts (measured, from the Windows edition)

| | 16 GB (RTX 5060 Ti) MAX/FLASH | 8 GB (RTX 4060 Laptop) LITE |
|---|---|---|
| Chat | ~42–58 tok/s (MTP on) | ~97 tok/s (with MTP on 16 GB) |
| Image (`yeni` mode), end to end | 60–95 s | 68–139 s |
| Photo editing (`kimlik_duzenle` mode) | 74–160 s | **not supported** (does not fit in 8 GB) |

By default ComfyUI runs **only during media generation** and is closed before the
language model loads (it holds neither VRAM nor RAM while idle).

---

## Tests

```bash
python -m pip install pytest -r requirements/app.txt
python -m pytest -q          # 152 tests; does not require PySide6 (Qt is only needed for the wizard tests)
```

When PySide6 is installed, the wizard window is also tested headlessly
(`QT_QPA_PLATFORM=offscreen`); when it is not installed those tests are skipped.
End-to-end verification (on an installed root, with real models):

```bash
./scripts/smoke-test.sh --profile flash
```

---

## Contributing and development

**[AGENTS.md](AGENTS.md)** explains how the codebase is started, how the pieces talk
to each other and the known pitfalls. When you add a feature, update `AGENTS.md` and
`CHANGELOG.md` in the same commit.

---

## Licence

The MamidLabs source code is licensed under the **PolyForm Strict License 1.0.0**
(source-available; **non-commercial** use only). You may not distribute, modify or
create derivative works of the software; commercial use requires prior written
permission from the rights holder. Copyright belongs to Aybars Haydar Altuntaş. For
details see the [LICENSE](LICENSE) file and
https://polyformproject.org/licenses/strict/1.0.0.
The models used (Qwen, Krea 2, Krea 2 Identity Edit LoRA, Wan 2.2, etc.) and the
third-party components (llama.cpp, ComfyUI, ComfyUI-GGUF, comfyui-krea2edit, etc.)
are subject to their own licences; this licence does not cover them.
