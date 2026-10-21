# MamidLabs · Infrastructure guide for developers and AI agents (Linux)

This file is the single source of truth for developers and AI agents working on the
MamidLabs Linux edition. It explains how the codebase is started, how the pieces talk
to each other, where everything lives and the known pitfalls.

> **Mandatory rule:** When you add a feature, change a behaviour or find a new pitfall,
> update this file **in the same commit**: fix the relevant section and add a line to
> the [Change log](#16-change-log) at the bottom. User-visible changes are also written
> to `CHANGELOG.md`. If the code and this file disagree, **the code is right**; whoever
> notices the disagreement fixes this file.

The user-facing interface language defaults to **English**; Turkish is available as a
localisation (`tr`). Code comments and script messages are English.

---

## 1. The product in one paragraph

MamidLabs is a multimodal AI workspace that runs entirely locally on Linux. In a
single Qt6 window it offers chat, web search, document reading/creation, OCR, image
understanding, image generation, photo editing, video generation, chart drawing and
audio transcription. The language model runs on `llama.cpp` (`llama-server`), the
image/video models on `ComfyUI`, on the user's NVIDIA GPU. OpenAI, Claude, Gemini,
DeepSeek and custom OpenAI-compatible endpoints are optional API providers.
Repository: `github.com/workaybarsh/mamidlabs_linux`. Default install root:
`~/.local/share/mamidlabs`.

This edition is the **Linux port** of the Windows edition (`MamidLabsTR` /
`MamidLabsENG`): **Python 3.12 + PySide6 (Qt6)** instead of WinForms/PowerShell.
Constants, behaviours and the tool set are kept identical to the Windows edition.

## 2. Repository map

| Path | Contents |
|---|---|
| `mamidlabs/__main__.py` | Entry point: `doctor`, `profiles`, `manage` subcommands; otherwise the GUI |
| `mamidlabs/ui/app.py` | Qt6 `QApplication` + main window setup |
| `mamidlabs/ui/main_window.py` | Main window, chat, profile/provider selectors, chips, `TurnWorker`/`ManageWorker` |
| `mamidlabs/ui/settings_dialog.py` | API connections window, key validation |
| `mamidlabs/ui/theme.py` | Qt style sheet |
| `mamidlabs/core/hwinfo.py` | Hardware measurement + profile recommendation (wizard page 5) |
| `mamidlabs/wizard/` | Setup wizard: `__init__.py` (pure helpers), `setup.py` (Qt6 `QWizard`, 13 pages), `__main__.py` (entry + desktop check) |
| `mamidlabs/core/paths.py` | XDG install root and all paths |
| `mamidlabs/core/settings.py` | `api.json` store (atomic write, `0600`), `SecretStore`, `secret_backend` |
| `mamidlabs/core/profiles.py` | Profile catalog, aliases, target paths, missing files |
| `mamidlabs/core/providers.py` | Provider table, OpenAI ↔ Claude converters, streaming (SSE) |
| `mamidlabs/core/manage.py` | `ModelManager`: start/stop, VRAM gate, `server_args`, ComfyUI/orphan cleanup, `FileLock` |
| `mamidlabs/core/inference.py` | `InferenceEngine`: chat loop, system prompt, tool loop, approval, compaction, web honesty |
| `mamidlabs/core/tools.py` | `ToolRegistry` (gates + handlers), `WebTracker`, `MediaBridge` |
| `mamidlabs/core/chart.py` | matplotlib chart generation + safe expression evaluator |
| `mamidlabs/core/runner.py` | `WorkerRunner`: runs workers over JSON stdin/stdout |
| `mamidlabs/workers/` | Platform-independent Python workers (see below) |
| `scripts/install-mamidlabs.sh` | Staged installation |
| `scripts/manage-mamidlabs.sh` | Model/ComfyUI management, doctor, profiles |
| `scripts/uninstall-mamidlabs.sh` | Full removal (touches nothing outside the root) |
| `scripts/smoke-test.sh` | End-to-end verification with real models |
| `scripts/mamidlabs-setup.sh` | Starts the setup wizard (`python -m mamidlabs.wizard`) |
| `packaging/linux/build-deb.sh` | Builds the `.deb` (application + wizard); `packaging/linux/README.md` |
| `packaging/mamidlabs.desktop`, `packaging/mamidlabs.svg` | Desktop launcher and icon |
| `requirements/{app,imagegen,asr,ocr}.txt` | Python packages (pinned versions) |
| `tests/` | pytest (205 tests) |
| `docs/` | `install.md`, `technical-notes.md` |
| `.github/workflows/tests.yml` | CI (ubuntu-latest, Python 3.12) |
| `.github/workflows/installer.yml` | Release: on a `v*` tag builds the `.deb` and uploads it to the GitHub Release under a fixed name (`mamidlabs.deb`) |
| `AGENTS.md` | This guide. Not copied into the install root. |

### Workers (`mamidlabs/workers/`)

One-shot JSON stdin/stdout contract. Every worker runs in its own virtual environment.

| Worker | Environment | Job |
|---|---|---|
| `mamidlabs-agent-tools.py` | app | Web search (`ddgs`), page reading, reference image |
| `office-tools.py` | app | PDF/Word/Excel/PPTX/ZIP/RAR reading, PDF/DOCX/PPTX/XLSX creation |
| `ocr-tools.py` | ocr | PaddleOCR |
| `media-tools.py` | imagegen | Video frame extraction (PyAV) |
| `api-media.py` | app | Image/video generation through APIs |
| `hf-hub.py` | app | Hugging Face download (size + SHA256 verified, resumes) |
| `mtp_inject.py` | app | Adds the MTP/nextn header to the LITE GGUF |
| `whisper-tools.py` | asr | Audio transcription (calls the `transcriber/` package) |
| `transcriber/` | asr | faster-whisper + AST + pyannote pipeline |
| `rag-tools.py` | app | Local (offline) BM25 search in the bound folder (`search_folder`) |
| `_root.py` | — | Workers reading the install root (`MAMIDLABS_ROOT` → XDG) |

## 3. Install root layout

```
~/.local/share/mamidlabs/
  llama.cpp/b10998/llama-server     pinned llama.cpp build
  models/                           GGUF language models (+ mmproj)
  ComfyUI/                          pinned commit; custom_nodes: ComfyUI-GGUF, comfyui-krea2edit
  venv/{app,imagegen,asr,ocr}/      Python environments (bin/python)
  tools/{hf-home,downloads,pip-cache,backup,rag}/
  settings/api.json                 all user settings (secrets 0600)
  chats/  outputs/{images,videos,documents,charts,refs,thumbs,input}/
  logs/                             llama-server-*.std{out,err}.log, comfyui.*.log, audit.jsonl
  mamidlabs-launch                  launcher
```

As on Windows there is **no bundled runtime** (no `runtime/`): the application runs
with the system Python.

## 4. Startup chain

1. `.desktop` → `~/.local/share/mamidlabs/mamidlabs-launch`.
2. The launcher sets `MAMIDLABS_ROOT` and runs `venv/app/bin/python -m mamidlabs`.
3. `mamidlabs/__main__.py` parses the arguments; without a subcommand, `ui/app.py:main`.
4. `ui/app.py`: `Paths`, `Settings`, `QApplication`, `MainWindow`.
5. `MainWindow` prepares the paths and builds `ModelManager`/`ToolRegistry`/`InferenceEngine`.
6. When the user selects a profile and presses **Start model**, `ManageWorker` → `ModelManager.start`.
7. When the application closes, the server and the idle ComfyUI are shut down (VRAM is released).

## 5. Processes and ports

| Process | Port | Owner |
|---|---|---|
| `llama-server` | 8080 | `core/manage.py` (`ModelManager`) |
| ComfyUI | 8188 | media bridge / `manage-mamidlabs.sh comfy` |
| Audio transcription worker | random (127.0.0.1) | `core/inference.py` |

**Profiles** (`core/profiles.py`; aliases are the same as Windows):

| Profile | Alias | Important flags |
|---|---|---|
| MAX | `qwen3.8-27b-max` | ctx 32768, predict 8192, gpu-layers 99, q4_0 KV, cache-reuse 256, batch 512/256, threads 6/12, `--mmproj --no-mmproj-offload --image-min-tokens 1024`, `--reasoning-effort xhigh`, `--spec-type draft-mtp` when MTP is available |
| FLASH | `qwen3.8-27b-flash` | same files; `--reasoning-effort low` |
| LITE | `qwen3.5-9b-lite` | ctx `liteContext` (32768), predict 8192, batch 256/128, threads 4/8, `--image-min-tokens 512`, `--reasoning-effort low`, `--spec-type draft-mtp` when MTP is available |

MAX and FLASH use the same files → the interface shows a single "Qwen3.8 MAX" entry
(`catalog_for_display`). Lookup by id uses the full catalog (`get_profile`).

**MTP.** `--spec-type draft-mtp` is added only when the GGUF really carries an
MTP/`nextn` block (`manage.gguf_has_mtp`); giving it to a model without one makes
llama.cpp refuse to start. LITE's 9B GGUF loses the header during conversion and gets
it re-added during the download with `mtp_inject.py`. Disabled with `settings.mtp=false`.

**Auto effort (MAX/FLASH).** MAX and FLASH are the same model; the only difference is
the server's `--reasoning-effort` value. Because switching the profile reloads the model
(~15 s), by default (Profiles → **"Auto effort (by question)"**) the effort is given
**per request** via `chat_template_kwargs.reasoning_effort`: short question/greeting →
`low`, medium → `medium`, multi-step maths/code/analysis/comparison → `xhigh`
(`inference.auto_reasoning_effort`). The choice is made **once at the start of a turn**
and stays fixed for the whole turn (so the system prefix does not change and the KV
cache is not broken). When disabled, the server's profile value is used
(`api.json → autoEffort=false`). LITE's template ignores this key; it is never sent to
API providers.

**VRAM gate** (`manage.ModelManager`): required = model file + headroom. MAX/FLASH
headroom **750 MiB**, tolerance **0** (free < required → error). LITE headroom
**300 MiB**, tolerance **1024 MiB** (warning band `[required-1024, required)`). The
vision projector runs on the CPU for all three profiles (`--no-mmproj-offload`) and is
not part of the budget. Before the model loads, leftover GPU workers
(`Stop-OrphanWorkers`) are stopped.

**ComfyUI lifecycle:** by default it runs **only during media generation**
(`comfyKeepAlive=false`); it is closed before the language model loads. On LITE it can
be kept open with `comfyKeepAlive=true`. Leaked/duplicate instances are counted by
process **roots** (ComfyUI is a process pair); the single instance listening on `:8188`
is kept.

## 6. Chat request flow

1. The user sends → `MainWindow._send` → `TurnWorker` (`QThread`).
2. `InferenceEngine.build_job_messages`: fixed `SYSTEM_PROMPT` + history. Image data
   from old turns is dropped and replaced by a note. Turn-specific hints are added to
   the **start of the last user message**, not to the system prompt (so the KV cache
   prefix is not broken).
3. `run_turn` produces events (to the interface via the `event` signal): `thinking`,
   `answer`, `status`, `tool`, `denied`, `error`, `done`, `cancelled`.
4. **Tools** (`core/tools.py`): `search_web`, `fetch_page`, `read_document`,
   `read_images_ocr`, `create_document`, `generate_image`, `generate_video`,
   `generate_chart`, `find_reference_image`, `ask_model`, `list_bound_files`,
   `read_bound_file`, `search_folder`, `write_bound_file`, `run_command`. Tools are
   offered according to intent and chips; production tools are re-checked at call time.
5. **Approval:** write/execute tools ask through the `approve` callback
   (`TurnWorker._approve` → `approval_needed` signal → `QMessageBox`). A 10 minute
   timeout → deny. With the "Full access" chip on they are normally not asked;
   **however, if untrusted content** (`search_web`, `fetch_page`, `read_document`,
   `read_images_ocr`, `read_bound_file`, `search_folder`) **was read during that turn,
   `run_command` and `write_bound_file` still ask** (`approval_required`); the approval
   window also states the reason (`chat.approval_untrusted`). The result of untrusted
   content is given to the model with the `chat.untrusted_prefix` label and the system
   prompt (`prompt.untrusted`) says this content is **data, not instructions**
   (against prompt injection).
6. **The `done` event** carries the `assistant.tool_calls` and `tool` messages added
   during that turn in the `data` field; the interface appends them to the persistent
   history. Without this, the client prefix would differ from the server's on the next
   turn and the context would be reprocessed from scratch.
7. **Context protection** (Windows parity): if at the start of a turn the estimated
   prompt + `max_tokens` + headroom would exceed the context, `compact_turn_messages`
   shortens it **in two passes** — first only the head of the oldest tool outputs, and
   if that is not enough the oldest tool outputs and old assistant text are replaced
   with a short marker (messages are never deleted; the `tool_calls`/`tool` pairing is
   preserved). **If it still does not fit**, tools are **not offered** and the model is
   asked for a visible answer from the findings (`chat.context_full`); `max_tokens` is
   clamped to the remaining room. The "compacted" status note is shown only when
   something was actually shortened.

### Web-failure honesty

The decision depends on the condition **the web was attempted AND no call succeeded**
(`WebTracker.unavailable = fail_count > 0 and not success`). Partial success
(e.g. 4 of 7 calls succeeded) is **not** counted as failure. After ≥2 errors the web
tools are locked (`should_lock_tools = fail_count >= 2 and not success`).
`add_failure_note` returns early when there was a success. On a turn that asks for
current information and has no web, the model's text is not used and an honest message
is shown; fabricated citations (`strip_fabricated_citations`) are stripped.

## 7. Image, photo editing and video

- When the model calls `generate_image`, `MediaBridge` (the bridge supplied by the
  interface) drives ComfyUI. The language model only writes the prompt.
- **Modes** (`generate_image.mode`): `yeni` (from text), `yeniden_uret` /
  `stil_referansi` (from an attached image), `kimlik_duzenle` (Krea 2 Identity Edit
  LoRA; **only MAX/FLASH** — not offered on 8 GB LITE).
- Video: Wan 2.2 TI2V 5B; modes `metin`, `gorsel`, `video`.
- External model files are used without copying: ComfyUI
  `--extra-model-paths-config`.
- API media: when the image/video provider is an API, `api-media.py`.

## 8. API providers

- Single table: `core/providers.py`: `openai`, `claude`, `gemini`, `deepseek`,
  `custom`. A new provider = one row in the table (+ a converter if needed).
- **`custom`** ("Custom (OpenAI-compatible)"): Ollama, LM Studio, vLLM, etc. The base
  URL is read from settings; **the key is optional** (when empty, `Authorization` is
  not sent).
- **Claude:** `thinking` is not sent; `tool_choice` is `auto` only when present in the
  body; the `max_tokens` floor is 16000; in the tool loop signed `thinking` blocks are
  collected by `ClaudeStream` and sent back via the first `tool_use` id.
- **DeepSeek** does not accept images; `image_url` parts are reduced to a text note.
- Keys are stored preferably in the **OS keyring** (`keyring` / Secret Service),
  otherwise in `settings/api.json` with `0600` permissions. `Settings.secret_backend`
  reports which one is used.

## 9. Profiles, catalog and download

- `core/profiles.py`: the file list per profile (`target` relative to the root, `repo`,
  `revision`, `filename`, `bytes`, optional `sha256`).
- Download sizes: LITE ~36 GB, MAX/FLASH ~52 GB. `hf-hub.py` verifies the size with
  `bytes`, resumes a partial file (`hf_hub_download`) and verifies **SHA256** when the
  download finishes: the pinned `sha256` from the catalog when present, otherwise the
  `lfs.sha256` digest from the Hugging Face LFS metadata (cached per repo/revision). On
  a mismatch the corrupt file is **deleted** and an error is raised. `HF_HOME` lives
  under the root.
- Profile status only checks the file's **existence**, not its size.
- **Profile deletion:** only files **exclusive** to that profile are deleted
  (`unique_targets`); shared ones are kept. Because MAX and FLASH are the same set,
  they are treated as aliases.

## 10. Installation, update and removal

- `install-mamidlabs.sh [--root] [--profile] [--language en|tr] [--stage a,b]
  [--skip-media] [--skip-audio] [--skip-ocr] [--skip-models] [--no-desktop]
  [--no-cuda] [--force]`. Stages: `preflight`, `layout`, `llama`, `python`,
  `comfyui`, `models`, `verify`. The `--language` choice is written to
  `settings/api.json`; the stage loop writes progress to `logs/kurulum-adim.txt`
  (lines 1/2/3: step number, total, name) and the summary to
  `logs/kurulum-ozeti.txt` at the end (the wizard reads these).
- `layout` installs the program files, the launcher, the `.desktop` file and the icon;
  it also writes the `mamidlabs-launch` launcher.
- Pinned versions: llama.cpp `b10998`, ComfyUI `b0f4b7b`, ComfyUI-GGUF `6ea2651`,
  comfyui-krea2edit `86f886d`, torch cu130.
- **Removal:** `uninstall-mamidlabs.sh [--keep-user-data] [--dry-run] [--yes]`.
  It only touches the root, the `.desktop` file and the icon; it refuses to run on
  system/user folders.
- **Update:** close the application → `git pull` → `install-mamidlabs.sh --stage layout`.
- **Version and release:** the single sources of the version are
  `mamidlabs/__init__.py:__version__` and `pyproject.toml:version` (they must be equal).
  For a new release: bump both, add a section to `CHANGELOG.md`, push the `v<version>`
  tag. When the tag is pushed, `.github/workflows/installer.yml` builds the `.deb` and
  uploads it to the GitHub Release under a **fixed name** (`mamidlabs.deb`), so
  `releases/latest/download/mamidlabs.deb` always downloads the latest version.

## 11. Settings and user data

`settings/api.json` (the application keeps it in memory and writes it on change and on
exit; **editing it manually while the app is running is overwritten**):

- Model selection: `selected`, `selectedModel`, `selectedLocalModel`, `localProfile`.
- Providers: `providers.<id>.{key, model, models, contextLimit, baseUrl}`.
- Own models: `localModels`, `imageLocalModel`, `videoLocalModel`,
  `imageProvider`, `videoProvider`, `externalMediaModels`.
- Interface: `uiPreferences.{internet, agent, accessMode}`, `firstRunApiSettings`.
- LITE: `liteModel`, `liteContext`.
- Media: `comfyKeepAlive` (default `false`).
- Audio: `audioEvents` (default `true`).
- Other: `mtp` (default `true`), `autoEffort` (default `true`), `boundFolder`,
  `language` (default `en`).
- Secrets: OS keyring or this file (`0600`).

Chats are stored under `chats/`. `logs/audit.jsonl`: the tool-call record (not the
content; path/command ids only).

## 12. Tests

```bash
python -m pip install pytest -r requirements/app.txt
python -m pytest -q          # 205 tests; does not require PySide6 (Qt is only needed for the wizard tests)
./scripts/smoke-test.sh --profile flash
```

- `conftest.py` points `MAMIDLABS_ROOT` at a temporary root; tests run independently of
  `__file__`.
- The tests do **not import** PySide6; the core logic is pure Python. The GUI only runs
  on a real desktop (in the interface steps of the smoke test).
- New-behaviour tests: `test_model_download_integrity.py` (`sha256_file`,
  `lookup_sha256`/`verify_sha256`, `incomplete_bytes`, `_mtp_config`, fetch
  protection), `test_auto_effort.py` (`auto_reasoning_effort` score + `chat_template_kwargs`
  in the request body), `test_prompt_injection.py` (untrusted content label, system
  prompt, approval even under full access), `test_rag_tools.py` (`rag-tools.py` BM25
  + `search_folder` gate).
- `manage.FileLock` uses `fcntl` on Linux and `msvcrt` on Windows (so the tests can be
  imported on Windows too).
- **Smoke test steps:** `doctor`, `sunucu_baslat`, `saglik`, `sohbet`, `grafik`,
  `cevrimdisi`, `mtp`, `ocr`, `gorsel`, `video`, `sunucu_durdur` (stable step ids, kept
  as JSON keys). The result is written to `logs/smoke-test-son.json`.
- **CI:** `tests.yml` on every push/PR (ubuntu-latest, Python 3.12). The second job
  (`gui`) installs the Qt system libraries (`libegl1` etc.) and opens the wizard window
  headlessly with `QT_QPA_PLATFORM=offscreen`; `tests/test_wizard_gui.py` silently skips
  when Qt cannot be loaded (`test_wizard.py` pure helpers run without Qt).

## 13. Hardware facts (measured)

| | 16 GB MAX/FLASH | 8 GB LITE |
|---|---|---|
| Chat | ~42–58 tok/s (MTP on) | ~97 tok/s (with MTP on 16 GB) |
| Image (`new`) | 60–95 s | 68–139 s |
| Photo editing | 74–160 s | **not supported** |
| Post-media switch | ratio ~1.0 | ratio ~1.0 |

The 27B model takes **~15350 MiB** on the GPU (the file is 14,600 MiB; KV cache q4_0 +
compute buffers + MTP draft context). That is why the MAX/FLASH headroom is **750 MiB**:
the model loads only if it fits completely and then uses all free VRAM.

**Why `kimlik_duzenle` is absent on 8 GB:** Krea2EditGroundedEncode keeps the text/image
encoder (~5 GB) and the diffusion model (~7.5 GB) in the same graph; 5 + 7.5 GB > 8 GB.
That is why the mode is never offered on LITE.

**Audio transcription and VRAM:** the audio pipeline holds ~3.9 GB on the GPU; it does
not fit on the same 16 GB card together with the 27B model (~15350 MiB) → the language
model is closed before transcription (mandatory swap). The remaining CUDA context
measured ~140 MiB; that is why the warm audio worker is stopped before the language
model is restored and restarted in the background at the end of the turn.

## 14. Critical pitfalls

1. **Do not derive the install root from `__file__`.** On Linux the package lives inside
   `site-packages`; workers read the root via `MAMIDLABS_ROOT` → XDG default
   (`workers/_root.py`). Do not hard-code a path when adding a new path to a worker.
2. **KV cache match.** The message array kept by the interface must be byte-for-byte
   identical to what the server processed that turn. If the tool call/result is not
   stored, or if the system prompt changes per turn, the context is reprocessed from
   scratch every turn. Put turn-specific text in the last user message.
3. **VRAM headroom depends on the profile** (MAX/FLASH 750 MiB tolerance 0; LITE 300 MiB
   tolerance 1024 MiB). The idle ComfyUI is **always** closed before the model loads
   (on MAX/FLASH, if the MTP draft context spills to the CPU, chat drops to ~6 tok/s).
   Leaked ComfyUI instances push the 27B into shared memory.
4. **ComfyUI is a process pair** (venv launcher + base python child). The leak decision
   is made by process **roots**, not by process **count**; one healthy instance is
   already 2 processes.
5. **`fcntl` is Linux-specific.** `manage.FileLock` imports it lazily and falls back to
   `msvcrt` on Windows, so the tests pass there too.
6. **`done.data` may be empty.** The worker puts an empty list there when there is no
   tool call; the interface uses an `if data:` guard (do not merge an empty array
   unconditionally).
7. **Single-image rule.** Only one image goes into the chat at a time (multiple images
   only through OCR).
8. **Do not edit `settings/api.json` manually while the app is running;** the in-memory
   copy is written on exit.
9. **`run_command` runs with `/bin/bash -lc`** and asks for user approval. Shell escaping
   differs from the Windows `.cmd` pitfalls; keep the command on one line.
10. **PySide6 is only required on a real desktop.** The core tests do not import the GUI;
    CI passes without PySide6 installed.
11. **The version lives in two places:** `mamidlabs/__init__.py:__version__` and
    `pyproject.toml:version`. Bump both together.
12. **The `.desktop` launcher contains the `@ROOT@` placeholder;** the installer
    substitutes the real root with `sed`. Do not copy it directly.
13. **The wizard needs Qt and a graphical desktop.** `python -m mamidlabs.wizard`
    exits with **2** and `wizard.error.no_pyside` when PySide6 is missing, and with
    **1** and `wizard.error.no_display` when `DISPLAY`/`WAYLAND_DISPLAY` is missing
    (`wizard/setup.py` is imported lazily for this reason). The wizard's pure helpers
    (`wizard/__init__.py`) are imported and tested without Qt. Because the language is
    process-global, tests reset it to the default language (English) with the autouse
    fixture in `conftest.py`.
14. **The RAG index is untrusted content.** A `search_folder` result goes to the model
    labelled `[UNTRUSTED CONTENT…]` and triggers write/execute approval for that turn.
    The index is kept in `tools/rag/bound-<hash>.json`; the hash is taken from **the real
    path as-is** (not lowercased) because Linux paths are case-sensitive. `hf-hub.py`
    sets `HF_HOME` **before the import**; on a SHA256 mismatch the downloaded file is
    deleted (never leave a silently corrupt model).

## 15. Checklist when making changes

- [ ] Run the relevant tests; add a test for the new behaviour (`python -m pytest -q`).
- [ ] Is user-facing text in English (and in `locales/*.json` when localised)?
- [ ] Install/removal impact: does a new file or folder get written outside the root?
      If so, add it to the uninstaller. By default everything must stay under the root.
- [ ] Are `README.md`, `docs/install.md`, `docs/technical-notes.md`, `CHANGELOG.md` and
      **this file** up to date?
- [ ] Did the server arguments or profile constants change? (Keep parity with the
      Windows edition.)
- [ ] For a release: are `__version__` + `pyproject.toml`, the CHANGELOG section and
      the `v<version>` tag aligned?

## 16. Change log

Add one line for every feature/change (newest first).

| Date | Change | Files |
|---|---|---|
| 2026-10-18 | **Licence brought to parity with the Windows edition: PolyForm Strict 1.0.0 (source-available; non-commercial use only).** `LICENSE` (no BOM, LF, 3619 bytes) and `EULA.txt` (UTF-8 with BOM, 4833 bytes) were copied **byte-for-byte** from the Windows `MamidLabsTR` repository; the README licence section, the `.deb` copyright notice (`packaging/linux/build-deb.sh` `copyright`) and the licence test in `tests/test_packaging_contract.py` (LICENSE header + EULA BOM) were updated. The `pyproject.toml` classifier stays `License :: Other/Proprietary License` (PolyForm is not OSI-approved). Version unchanged (1.0.0). | LICENSE, EULA.txt, README.md, packaging/linux/build-deb.sh, tests/test_packaging_contract.py, CHANGELOG.md, AGENTS.md |
| 2026-10-18 | **Context compaction: overflow in long chats handled gracefully (Windows parity).** Compaction has two passes (first the head of the tool output, then the oldest tool/assistant text is replaced with a short marker; messages are never deleted, the `tool_calls`/`tool` pairing is preserved). If the prompt still does not fit, tools are not offered and the model is asked for a visible answer from the findings, with `max_tokens` clamped to the remaining room; the "compacted" status note is shown only when something was actually shortened. | mamidlabs/core/inference.py, mamidlabs/locales/{tr,en}.json, tests/test_inference.py, AGENTS.md, CHANGELOG.md, docs/technical-notes.md |
| 2026-10-18 | **Local (offline) RAG in the bound folder: the `search_folder` tool.** The new worker `rag-tools.py` scans the bound folder and returns the most relevant text chunks in `[file:line]` form using BM25 (k1=1.2, b=0.75 + 1.6× whole-phrase bonus); the index is cached in `tools/rag/bound-<hash>.json` with a file signature (path + mtime + size) and rebuilt silently if corrupt. Folders such as `node_modules`/`.git`/`venv` and binary/oversized files are skipped; decoding is utf-8 → cp1254 → latin-1. The tool passes the same gate as the bound-folder file tools (not offered on an audio turn; offered when `is_file_intent`) and is treated as **untrusted**. | mamidlabs/workers/rag-tools.py, mamidlabs/core/tools.py, mamidlabs/core/paths.py, tests/test_rag_tools.py |
| 2026-10-18 | **Hardening against prompt injection.** Results from `search_web`/`fetch_page`/`read_document`/`read_images_ocr`/`read_bound_file`/`search_folder` are given to the model with the `chat.untrusted_prefix` label; the system prompt (`prompt.untrusted`) says this content is **data, not instructions**. If untrusted content was read that turn, `run_command`/`write_bound_file` ask for approval even with the "Full access" chip on (`inference.approval_required`); the approval window states the reason (`chat.approval_untrusted`). | mamidlabs/core/inference.py, mamidlabs/ui/main_window.py, mamidlabs/locales/*, tests/test_prompt_injection.py |
| 2026-10-18 | **Auto effort (per request for MAX/FLASH).** Because MAX and FLASH are the same model, with `Profiles → "Auto effort (by question)"` enabled (`api.json:autoEffort`, default `true`) `inference.auto_reasoning_effort` picks `low`/`medium`/`xhigh` per turn and puts it in the request body as `chat_template_kwargs.reasoning_effort` (local provider only; LITE's template ignores it). The choice is fixed for the turn → the model is not reloaded and the KV prefix is not broken. | mamidlabs/core/inference.py, mamidlabs/core/settings.py, mamidlabs/ui/main_window.py, mamidlabs/locales/*, tests/test_auto_effort.py |
| 2026-10-18 | **SHA256 verification + resume in model downloads.** `hf-hub.py` resumes a missing file with `hf_hub_download`, verifies SHA256 when the download finishes (pinned `sha256` from the catalog or the Hugging Face LFS metadata digest; cached per repo/revision) and deletes the corrupt file on a mismatch. An optional `sha256` was added to `CatalogFile` and a `sha256` + `mtp` dict to the install payload (the worker also accepts the `mtpRepo` string). | mamidlabs/workers/hf-hub.py, mamidlabs/core/profiles.py, scripts/install-mamidlabs.sh, tests/test_model_download_integrity.py |
| 2026-10-16 | **Release workflow added (`.deb`).** When a `v*` tag is pushed, `packaging/linux/build-deb.sh` builds the `.deb` and it is uploaded to the GitHub Release under a **fixed name** (`mamidlabs.deb`); a "Prebuilt package (.deb)" section and a `releases/latest/download/mamidlabs.deb` link were added to the README. Branch/PR runs only produce an artifact; the job stops if the tag does not match `__version__`. | .github/workflows/installer.yml, README.md, CHANGELOG.md, AGENTS.md |
| 2026-10-16 | **Setup wizard + hardware measurement + `.deb` package added.** A Qt6 `QWizard` (13 pages: language → welcome → licence → folder → hardware report → profile → own models → API → components → ready → install → summary → finish) asks the user in the first step whether they want **English or Türkçe**; the choice retranslates live and is written to `settings/api.json:language`. `hwinfo` recommends a profile using VRAM thresholds (≥15000 MiB → PRO, ≥7000 MiB → LITE, no NVIDIA → API). The wizard runs `install-mamidlabs.sh` and reads progress from `logs/kurulum-adim.txt`; `--language` and progress/summary writing were added to the script. `packaging/linux/build-deb.sh` builds an architecture-independent `.deb` (`mamidlabs-setup` + desktop entries). The wizard was split into pure helpers (`wizard/__init__.py`) and the Qt window (`wizard/setup.py`); `conftest.py` resets the language state between tests. Tests: `test_hwinfo.py`, `test_wizard.py` (pure), `test_wizard_gui.py` (headless Qt), `test_i18n.py`, `test_packaging_contract.py` (152 in total). | `mamidlabs/core/hwinfo.py`, `mamidlabs/wizard/*`, `scripts/install-mamidlabs.sh`, `scripts/mamidlabs-setup.sh`, `packaging/linux/*`, `mamidlabs/locales/*`, `pyproject.toml`, `conftest.py`, `tests/*`, `README.md`, `CHANGELOG.md` |
| 2026-10-16 | **The Linux edition was written for the first time (1.0.0).** Because the Windows edition (PowerShell + WinForms) does not run on Linux, the application was rewritten from scratch in a single language (Python 3.12 + PySide6/Qt6); constants, behaviours and the tool set were preserved exactly. The core (`paths`, `settings`, `profiles`, `providers`, `manage`, `inference`, `tools`, `chart`, `runner`), the Qt6 interface, the ported Python workers, the bash install/manage/uninstall/smoke scripts, the `.desktop` + icon, the docs and 78 tests were added. Windows-specific pieces were replaced with Linux counterparts: DPAPI → OS keyring / `0600`; bundled PowerShell 7 → system Python; WinForms → Qt6; `System.Drawing` → matplotlib; `%ProgramFiles%\7-Zip` → `7z`/`7za` on PATH; PDF fonts → DejaVu. | everything |
