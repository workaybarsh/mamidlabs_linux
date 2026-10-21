# Installation guide (Linux)

This guide explains how to install, start, update and remove MamidLabs on Linux.
For detailed technical information see [technical-notes.md](technical-notes.md).

## 1. Prerequisites

| Requirement | Note |
|---|---|
| Linux x86-64 | Ubuntu 22.04+/24.04, Fedora, Debian, Arch-like distributions |
| Python 3.11–3.13 | 3.12 is recommended. `python3 -m venv` must work (the `python3-venv` package) |
| `git`, `curl` (or `wget`), `unzip` | For the ComfyUI and llama.cpp downloads |
| `p7zip-full` | Reading RAR archives (`7z`/`7za`) — optional |
| NVIDIA GPU + driver | For image/video generation and fast chat. Works CPU-only but is slow |
| `libsecret` (GNOME Keyring etc.) | To store API keys in the OS keyring — optional |

One line per distribution:

```bash
# Debian/Ubuntu
sudo apt install python3 python3-venv git curl unzip p7zip-full

# Fedora
sudo dnf install python3 git curl unzip p7zip

# Arch
sudo pacman -S python git curl unzip p7zip
```

## 2. Installation

```bash
git clone https://github.com/workaybarsh/mamidlabs_linux.git
cd mamidlabs_linux
./scripts/install-mamidlabs.sh --profile flash
```

If you do not pass `--profile`, the program files and engines are installed but the
**language model is not downloaded**; later you can check the status with
`./scripts/manage-mamidlabs.sh profiles` and download it.

### Stages

The installer runs the following stages in order (`--stage` selects them):

| Stage | What it does |
|---|---|
| `preflight` | Checks Python/git/disk/GPU/7-Zip |
| `layout` | `venv/app`, the application package, the launcher, `.desktop` + icon |
| `llama` | Downloads the pinned `llama.cpp` (`b10998`) `llama-server` |
| `python` | Creates the `venv/imagegen`, `venv/asr`, `venv/ocr` environments |
| `comfyui` | Pinned-commit ComfyUI + `ComfyUI-GGUF` + `comfyui-krea2edit` |
| `models` | Downloads the language model + mmproj when `--profile` is given |
| `verify` | Inspects the installation (`python -m mamidlabs doctor`) |

Examples:

```bash
# Only refresh the program files (update)
./scripts/install-mamidlabs.sh --stage layout

# Lightweight install without media/audio/OCR
./scripts/install-mamidlabs.sh --profile lite --skip-media --skip-ocr

# Install under a different root
./scripts/install-mamidlabs.sh --root /opt/mamidlabs --profile max
```

## 3. First run

```bash
~/.local/share/mamidlabs/mamidlabs-launch
```

or **MamidLabs** from the application menu.

On first launch:

1. Choose the profile in the **Profile** box at the top (MAX / FLASH / LITE).
2. Press **Start model**; wait until the status bar says "Ready".
3. Type your message and press **Send** (or `Ctrl+Enter`).

### Chips

| Chip | When on |
|---|---|
| **Internet** | Web search and page-reading tools are offered |
| **Agent** | Bound-folder tools and `ask_model` are offered |
| **Full access** | No approval is asked for write/execute tools |

## 4. API providers (optional)

Menu → **API connections…**. Pick one of the openai / claude / gemini / deepseek /
custom rows and enter the key. Keys are stored preferably in the **OS keyring**
(Secret Service), otherwise in `settings/api.json` with `0600` permissions. `custom`
is your own OpenAI-compatible endpoint (Ollama, LM Studio, vLLM…); enter the base
URL, the key is optional.

## 5. Management

```bash
./scripts/manage-mamidlabs.sh start [max|flash|lite]  # start the model
./scripts/manage-mamidlabs.sh stop                    # stop
./scripts/manage-mamidlabs.sh status                  # active profile
./scripts/manage-mamidlabs.sh comfy                   # start ComfyUI
./scripts/manage-mamidlabs.sh closecomfy              # close the idle ComfyUI
./scripts/manage-mamidlabs.sh doctor                  # inspect the installation
./scripts/manage-mamidlabs.sh profiles                # profile status
```

## 6. Update

1. Close the application.
2. Pull the repository: `git pull`
3. Refresh the program files: `./scripts/install-mamidlabs.sh --stage layout`

User data (`settings/`, `chats/`, `models/`, `outputs/`) is preserved.

## 7. Removal

```bash
./scripts/uninstall-mamidlabs.sh                  # everything (asks for confirmation)
./scripts/uninstall-mamidlabs.sh --keep-user-data # keeps settings/chats/models
./scripts/uninstall-mamidlabs.sh --dry-run        # only show
```

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| "PySide6 not found" | `./scripts/install-mamidlabs.sh --stage layout` |
| "Not enough free VRAM" | Close desktop applications/the browser; switch to the LITE profile |
| The model does not load | `python -m mamidlabs doctor`; check the logs: `logs/` |
| Image generation does not work | `./scripts/manage-mamidlabs.sh comfy`; ComfyUI logs: `logs/comfyui.*.log` |
| Audio transcription fails | Is `venv/asr` installed? It may have been skipped with `--skip-audio` |
| Web search does not work | Turn on the Internet chip; when offline the model does not make things up and says so |

The logs are under `~/.local/share/mamidlabs/logs/`:
`llama-server-*.std{out,err}.log`, `comfyui.{out,err}.log`, `audit.jsonl`,
`smoke-test-son.json`.
