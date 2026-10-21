# Changelog

This file lists the user-visible changes. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/).

The single source of the version is `__version__` in `mamidlabs/__init__.py` and the
`version` field in `pyproject.toml` (they must be equal).

## [1.0.0] — 2026-10-16

### Added
- **SHA256 verification and resume of partial downloads in profile downloads.** `mamidlabs/workers/
  hf-hub.py` compares the downloaded file's SHA256 digest with Hugging Face's LFS digest
  (offline too when the catalog has an optional `sha256` field); on a mismatch the file is **deleted**
  and a clear error is raised, so a corrupt model is never left behind silently. Verification happens
  **before** MTP injection (injection changes the file). A partial download is resumed from where it
  stopped by `hf_hub_download`, and the worker reports this on the status line. Tests:
  `tests/test_model_download_integrity.py`.
- **Auto effort: MAX/FLASH behaviour based on question difficulty (without reloading the model).**
  Because MAX and FLASH are the same model, instead of switching profiles `reasoning_effort`
  is given per request for that turn: short question/greeting `low`, medium `medium`, multi-step
  maths/code/analysis `xhigh`. The choice is made once at the start of a turn and stays fixed for the
  turn (the KV prefix is not broken). It can be disabled with **"Auto effort (by question)"** in the
  Profiles menu (`settings/api.json → autoEffort`). It is not applied on LITE or API providers.
  Tests: `tests/test_auto_effort.py`.
- **Prompt injection hardening.** Web page, document, OCR and bound-file content is given to the model
  labelled as `[UNTRUSTED CONTENT …]` and treated as **data**; the fixed system prompt says that
  instructions in the content must not be applied. If untrusted content was read during that turn,
  approval is asked for `run_command` and `write_bound_file` **even with the "Full access" chip on**
  (`approval_required`), so an instruction hidden in the content cannot make it act on the user's
  behalf. Tests: `tests/test_prompt_injection.py`.
- **Local RAG: offline (BM25) search in the bound folder.** The new `search_folder` tool finds the
  relevant text chunks before reading files one by one in the bound folder:
  `mamidlabs/workers/rag-tools.py` scans plain-text files (skipping `node_modules`/`venv`/`.git`),
  produces ~900-character chunks that preserve line boundaries and ranks them with BM25 + a
  whole-phrase bonus; the result is returned as `path:line`. The index is kept under `tools/rag/` and
  is not rebuilt while the source files stay unchanged; no extra Python package is required. The
  result is labelled as **untrusted data** like other external sources. Tests:
  `tests/test_rag_tools.py`.
- **GitHub Actions release workflow (`.deb`).** When a `v*` tag is pushed, the `.deb`
  package is built and uploaded to a GitHub Release under a **fixed name**
  (`mamidlabs.deb`), so `releases/latest/download/mamidlabs.deb` always downloads the
  latest version directly. The single source of the version is `__version__` (checked
  against the tag) and the release notes are read from `CHANGELOG.md`. Branch/PR runs
  only produce an artifact.
- **Setup wizard (Qt6).** The "MamidLabs Setup" icon in the application menu
  (or `scripts/mamidlabs-setup.sh`) opens a wizard that measures the hardware and
  suggests a suitable profile: language (English/Türkçe) → welcome → licence → folder →
  hardware report → profile (LITE/PRO/no download/own model–API) → (own models) →
  (API) → (components) → ready → install → summary → finish. 13 pages;
  `mamidlabs/wizard/`. The wizard writes the language and the choices into
  `settings/api.json`, runs the installation through `install-mamidlabs.sh` and reads
  progress from `logs/kurulum-adim.txt`.
- **Hardware measurement** (`mamidlabs/core/hwinfo.py`): `nvidia-smi`, `/proc/meminfo`,
  `/proc/cpuinfo`, `/etc/os-release` and free disk; VRAM ≥ 15000 MiB → PRO,
  ≥ 7000 MiB → LITE, otherwise or without NVIDIA → API providers (Windows thresholds).
- **`.deb` package** (`packaging/linux/build-deb.sh`, `Architecture: all`): installs the
  application **and the wizard**; `mamidlabs-setup` + `mamidlabs` launchers, desktop
  entries and the icon.
- `install-mamidlabs.sh --language en|tr` (writes to the settings file), and progress
  (`logs/kurulum-adim.txt`) and summary (`logs/kurulum-ozeti.txt`) files for the wizard.
- New tests: `test_hwinfo.py`, `test_wizard.py` (headless Qt), `test_i18n.py`,
  `test_packaging_contract.py`, `test_model_download_integrity.py`,
  `test_auto_effort.py`, `test_prompt_injection.py`, `test_rag_tools.py`
  (205 tests in total).
- **MamidLabs Linux edition.** A complete Linux port of the Windows edition
  (`MamidLabsTR` / `MamidLabsENG`): a single-language **Python 3.12 + PySide6 (Qt6)**
  desktop application instead of WinForms/PowerShell.
- Qt6 main window: streaming chat, profile/provider/model selectors, Internet /
  Agent / Full access chips, model start-stop, tool approval dialog.
- API connections window; keys are stored preferably via **Secret Service (keyring)**,
  otherwise in a `0600` settings file.
- Command-line interface: `python -m mamidlabs {doctor,profiles,manage}`.
- Bash install/manage scripts: `install-mamidlabs.sh` (staged),
  `manage-mamidlabs.sh`, `uninstall-mamidlabs.sh`, `smoke-test.sh`.
- `.desktop` launcher and SVG icon.
- Core modules: `paths` (XDG install root), `settings`, `profiles`,
  `providers` (OpenAI ↔ Claude converters + streaming), `manage`
  (`ModelManager`, VRAM gate, ComfyUI/orphan cleanup), `inference`
  (chat loop, tool loop, approval, context compaction), `tools`
  (tool registry + gates + web-failure honesty), `chart`, `runner`.
- Python workers ported to Linux (web, document, OCR, media, whisper/transcriber,
  `mtp_inject`, `hf-hub`, `api-media`); the install root is now read from
  `MAMIDLABS_ROOT` (not derived from `__file__`).
- 78 unit tests (`pytest`).

### Fixed
- **Context overflow in long chats is now handled gracefully (Windows parity).** Compaction has two
  passes: first only the head of the oldest tool outputs is kept, and if that is not enough the
  oldest tool outputs and old assistant text are replaced with a short marker (messages are never
  deleted, the `tool_calls`/`tool` pairing is not broken). If the prompt still does not fit, tools are
  not offered at all and the model is asked for a **visible answer from the findings**
  (an overflowing prompt used to be a hard error because `llama-server --no-context-shift` is used).
  The output budget (`max_tokens`) is clamped to the remaining room and the "Approaching the context
  limit" note is shown only when something was actually shortened (no needless misleading note).
  Tests: `tests/test_inference.py`.

### Changed
- **The licence is now PolyForm Strict 1.0.0 (source-available; non-commercial use only).**
  `LICENSE` and `EULA.txt` carry the official PolyForm Strict 1.0.0 text: no right to distribute
  or modify/create derivative works; commercial use requires prior written permission.
  The README licence section, the `.deb` copyright notice (`copyright`) and the licence test were
  updated accordingly. The version number did not change (1.0.0).

### Changed (compared with the Windows edition)
- OS keyring / `0600` file instead of Windows **DPAPI**.
- System Python instead of the Windows **bundled PowerShell 7 runtime**
  (no `runtime/` under the install root).
- **Qt6** instead of Windows **WinForms**; **matplotlib** instead of `System.Drawing`
  graphics.
- 7-Zip path `7z`/`7za` (PATH); PDF fonts DejaVu; HTTP User-Agent
  `X11; Linux x86_64`.

### Preserved
- Profile aliases (`qwen3.8-27b-max` / `-flash`, `qwen3.5-9b-lite`), model
  ids, tool names, server argument bundles, MTP, the VRAM gate and the
  ComfyUI lifecycle — identical to the Windows edition.
