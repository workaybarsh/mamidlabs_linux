#!/usr/bin/env bash
# MamidLabs (Linux) installer.
#
# Stages (run in order): preflight, layout, llama, python, comfyui, models, verify
#
# Everything is installed under the install root (default ~/.local/share/mamidlabs,
# override with --root or MAMIDLABS_ROOT). Nothing is written outside it except the
# .desktop launcher, which you can skip with --no-desktop.
set -euo pipefail

LLAMA_BUILD="b10998"
COMFY_COMMIT="b0f4b7b"
COMFY_GGUF_COMMIT="6ea2651"
KREA2EDIT_COMMIT="86f886d"
COMFY_REPO="https://github.com/comfyanonymous/ComfyUI.git"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

ROOT="${MAMIDLABS_ROOT:-$HOME/.local/share/mamidlabs}"
STAGES="preflight,layout,llama,python,comfyui,models,verify"
PROFILE=""
NO_DESKTOP=0
SKIP_MEDIA=0
SKIP_AUDIO=0
SKIP_OCR=0
SKIP_MODELS=0
FORCE=0
WITH_CUDA=1

usage() {
  cat <<'EOF'
Kullanım: install-mamidlabs.sh [seçenekler]

  --root <yol>        Kurulum kökü (varsayılan: ~/.local/share/mamidlabs)
  --profile <ad>      max | flash | lite  (model indirme profili)
  --stage <liste>     Çalıştırılacak aşamalar (virgülle):
                      preflight,layout,llama,python,comfyui,models,verify
  --skip-media        ComfyUI ve görsel/video modellerini atla
  --skip-audio        Ses dökümü (asr) ortamını atla
  --skip-ocr          OCR ortamını atla
  --skip-models       Dil modeli indirmeyi atla
  --no-desktop        .desktop başlatıcısını kurma
  --no-cuda           CPU-only torch (CUDA yoksa otomatik seçilir)
  --force             Var olanı yeniden kur
  -h, --help          Bu metin
EOF
}

log()  { printf '\033[1;34m[MamidLabs]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[uyarı]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[hata]\033[0m %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root) ROOT="$2"; shift 2 ;;
    --profile) PROFILE="$2"; shift 2 ;;
    --stage) STAGES="$2"; shift 2 ;;
    --skip-media) SKIP_MEDIA=1; shift ;;
    --skip-audio) SKIP_AUDIO=1; shift ;;
    --skip-ocr) SKIP_OCR=1; shift ;;
    --skip-models) SKIP_MODELS=1; shift ;;
    --no-desktop) NO_DESKTOP=1; shift ;;
    --no-cuda) WITH_CUDA=0; shift ;;
    --force) FORCE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "bilinmeyen seçenek: $1" ;;
  esac
done

export MAMIDLABS_ROOT="$ROOT"
ROOT="$(realpath -m "$ROOT")"
export MAMIDLABS_ROOT="$ROOT"

has_stage() { [[ ",${STAGES}," == *",$1,"* ]]; }

have_cmd() { command -v "$1" >/dev/null 2>&1; }

detect_gpu() {
  if have_cmd nvidia-smi && nvidia-smi -L >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

# --- stages ------------------------------------------------------------------
stage_preflight() {
  log "Ön koşullar denetleniyor"
  have_cmd python3 || die "python3 bulunamadı (apt install python3 python3-venv)"
  local pyver
  pyver="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  [[ "$pyver" == "3.12" || "$pyver" == "3.11" || "$pyver" == "3.13" ]] \
    || warn "Python $pyver önerilmez; 3.11–3.13 desteklenir."
  python3 -c 'import venv' >/dev/null 2>&1 || die "python3-venv eksik (apt install python3-venv)"
  have_cmd git || warn "git yok; ComfyUI aşaması atlanacak."
  have_cmd curl || have_cmd wget || warn "curl/wget yok; indirmeler başarısız olabilir."
  if [[ $SKIP_MEDIA -eq 0 ]]; then
    detect_gpu || warn "NVIDIA GPU görünmüyor; görsel/video üretimi çok yavaş olur."
  fi
  if have_cmd 7z || have_cmd 7za; then
    :
  else
    warn "7-Zip (p7zip) yok; RAR okuma devre dışı olur (apt install p7zip-full)."
  fi
  local free_gb
  free_gb="$(df -Pk "$ROOT" 2>/dev/null | awk 'NR==2 {print int($4/1024/1024)}' || echo 0)"
  [[ "${free_gb:-0}" -ge 60 ]] || warn "Boş disk ${free_gb} GB; LITE ~36 GB, MAX/FLASH ~52 GB ister."
}

stage_layout() {
  log "Program dosyaları yerleştiriliyor: $ROOT"
  mkdir -p "$ROOT"
  local venv_dir="$ROOT/venv/app"
  python3 -m venv --upgrade-deps "$venv_dir"
  "$venv_dir/bin/python" -m pip install --quiet --upgrade pip
  "$venv_dir/bin/python" -m pip install --quiet -r "$REPO_DIR/requirements/app.txt"
  "$venv_dir/bin/python" -m pip install --quiet --no-deps -e "$REPO_DIR"

  # Launcher helper (so the .desktop file is a one-liner).
  cat > "$ROOT/mamidlabs-launch" <<EOF
#!/usr/bin/env bash
export MAMIDLABS_ROOT="$ROOT"
exec "$venv_dir/bin/python" -m mamidlabs "\$@"
EOF
  chmod +x "$ROOT/mamidlabs-launch"

  if [[ $NO_DESKTOP -eq 0 ]]; then
    local apps="$HOME/.local/share/applications"
    local icons="$HOME/.local/share/icons/hicolor/scalable/apps"
    mkdir -p "$apps" "$icons"
    sed "s|@ROOT@|$ROOT|g" "$REPO_DIR/packaging/mamidlabs.desktop" > "$apps/mamidlabs.desktop"
    cp -f "$REPO_DIR/packaging/mamidlabs.svg" "$icons/mamidlabs.svg"
    have_cmd update-desktop-database && update-desktop-database "$apps" >/dev/null 2>&1 || true
    have_cmd gtk-update-icon-cache && gtk-update-icon-cache -q -t -f "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
    log "Masaüstü başlatıcısı kuruldu: $apps/mamidlabs.desktop"
  fi
}

stage_llama() {
  log "llama.cpp ($LLAMA_BUILD) indiriliyor"
  local dir="$ROOT/llama.cpp/$LLAMA_BUILD"
  if [[ -x "$dir/llama-server" && $FORCE -eq 0 ]]; then
    log "llama-server zaten var; atlanıyor."
    return
  fi
  mkdir -p "$dir"
  local asset url tmp
  if detect_gpu; then
    asset="llama-${LLAMA_BUILD}-bin-ubuntu-x64.zip"
  else
    asset="llama-${LLAMA_BUILD}-bin-ubuntu-x64.zip"
  fi
  url="https://github.com/ggml-org/llama.cpp/releases/download/${LLAMA_BUILD}/${asset}"
  tmp="$ROOT/tools/downloads/llama.zip"
  mkdir -p "$(dirname "$tmp")"
  log "İndiriliyor: $url"
  if have_cmd curl; then curl -fL --retry 3 -o "$tmp" "$url"; else wget -O "$tmp" "$url"; fi
  (cd "$dir" && unzip -o -j "$tmp" 'llama-server' '*.so*' >/dev/null 2>&1 || true)
  # Some archives keep the binary in a subfolder.
  if [[ ! -x "$dir/llama-server" ]]; then
    find "$dir" -name 'llama-server' -type f -exec cp {} "$dir/llama-server" \; || true
  fi
  chmod +x "$dir/llama-server" 2>/dev/null || true
  [[ -x "$dir/llama-server" ]] || die "llama-server çıkarılamadı ($url)"
}

stage_python() {
  log "Sanal ortamlar hazırlanıyor"
  if [[ $SKIP_MEDIA -eq 0 ]]; then
    local venv_dir="$ROOT/venv/imagegen"
    python3 -m venv --upgrade-deps "$venv_dir"
    "$venv_dir/bin/python" -m pip install --quiet --upgrade pip
    if [[ $WITH_CUDA -eq 1 ]] && detect_gpu; then
      "$venv_dir/bin/python" -m pip install --quiet \
        -r "$REPO_DIR/requirements/imagegen.txt" \
        --extra-index-url https://download.pytorch.org/whl/cu130
    else
      "$venv_dir/bin/python" -m pip install --quiet -r "$REPO_DIR/requirements/imagegen.txt"
    fi
  fi
  if [[ $SKIP_AUDIO -eq 0 ]]; then
    local venv_dir="$ROOT/venv/asr"
    python3 -m venv --upgrade-deps "$venv_dir"
    "$venv_dir/bin/python" -m pip install --quiet --upgrade pip
    if [[ $WITH_CUDA -eq 1 ]] && detect_gpu; then
      "$venv_dir/bin/python" -m pip install --quiet \
        -r "$REPO_DIR/requirements/asr.txt" \
        --extra-index-url https://download.pytorch.org/whl/cu130
    else
      "$venv_dir/bin/python" -m pip install --quiet -r "$REPO_DIR/requirements/asr.txt"
    fi
  fi
  if [[ $SKIP_OCR -eq 0 ]]; then
    local venv_dir="$ROOT/venv/ocr"
    python3 -m venv --upgrade-deps "$venv_dir"
    "$venv_dir/bin/python" -m pip install --quiet --upgrade pip
    "$venv_dir/bin/python" -m pip install --quiet -r "$REPO_DIR/requirements/ocr.txt"
  fi
}

stage_comfyui() {
  [[ $SKIP_MEDIA -eq 0 ]] || { log "ComfyUI atlanıyor (--skip-media)"; return; }
  have_cmd git || { warn "git yok; ComfyUI atlanıyor."; return; }
  log "ComfyUI ($COMFY_COMMIT) hazırlanıyor"
  local dir="$ROOT/ComfyUI"
  if [[ -d "$dir/.git" ]]; then
    (cd "$dir" && git fetch --quiet --tags origin && git checkout --quiet "$COMFY_COMMIT")
  else
    git clone --quiet "$COMFY_REPO" "$dir"
    (cd "$dir" && git checkout --quiet "$COMFY_COMMIT")
  fi
  local nodes="$dir/custom_nodes"
  mkdir -p "$nodes"
  clone_node() {
    local url="$1" commit="$2" name="$3"
    if [[ -d "$nodes/$name/.git" ]]; then
      (cd "$nodes/$name" && git fetch --quiet origin && git checkout --quiet "$commit")
    else
      git clone --quiet "$url" "$nodes/$name"
      (cd "$nodes/$name" && git checkout --quiet "$commit")
    fi
  }
  clone_node "https://github.com/city96/ComfyUI-GGUF.git" "$COMFY_GGUF_COMMIT" "ComfyUI-GGUF"
  clone_node "https://github.com/conradlocke/comfyui-krea2edit.git" "$KREA2EDIT_COMMIT" "comfyui-krea2edit"
  log "ComfyUI bağımlılıkları kuruluyor"
  "$ROOT/venv/imagegen/bin/python" -m pip install --quiet -r "$dir/requirements.txt" || \
    warn "ComfyUI requirements kurulumu kısmen başarısız."
}

stage_models() {
  [[ $SKIP_MODELS -eq 0 ]] || { log "Model indirme atlanıyor (--skip-models)"; return; }
  [[ -n "$PROFILE" ]] || { log "Profil verilmedi (--profile); model indirme atlandı."; return; }
  log "Profil modelleri indiriliyor: $PROFILE"
  "$ROOT/venv/app/bin/python" - "$PROFILE" <<'PY'
import json, sys
sys.path.insert(0, ".")
from mamidlabs.core.paths import Paths
from mamidlabs.core.profiles import get_profile
from mamidlabs.core.runner import WorkerRunner
from mamidlabs.core.settings import Settings

profile_id = sys.argv[1]
paths = Paths()
paths.ensure_dirs()
settings = Settings(paths)
runner = WorkerRunner(paths, settings)
profile = get_profile(profile_id)
for item in profile.files:
    target = paths.root / item.target
    if target.exists():
        print(f"var: {item.target}")
        continue
    payload = {"action": "download", "repo": item.repo, "revision": item.revision,
               "filename": item.filename, "target": str(target),
               "bytes": item.bytes, "mtpRepo": item.mtp_repo}
    result = runner.run("hf-hub.py", payload, env_name="app", timeout=7200)
    if result.get("error"):
        print(f"HATA {item.target}: {result['error']}")
    else:
        print(f"indirildi: {item.target}")
PY
}

stage_verify() {
  log "Kurulum doğrulanıyor"
  local ok=1
  "$ROOT/venv/app/bin/python" -c 'import mamidlabs; print("mamidlabs", mamidlabs.__version__)' || ok=0
  [[ -x "$ROOT/llama.cpp/$LLAMA_BUILD/llama-server" ]] || { warn "llama-server eksik"; ok=0; }
  if [[ $SKIP_MEDIA -eq 0 ]]; then
    [[ -f "$ROOT/ComfyUI/main.py" ]] || { warn "ComfyUI eksik"; ok=0; }
  fi
  "$ROOT/venv/app/bin/python" -m mamidlabs doctor || ok=0
  [[ $ok -eq 1 ]] && log "Kurulum tamam." || warn "Kurulum eksiklerle bitti; 'mamidlabs doctor' çıktısına bak."
}

mkdir -p "$ROOT/tools/downloads" "$ROOT/logs"
log "Kurulum kökü: $ROOT"
log "Aşamalar: $STAGES"

for stage in preflight layout llama python comfyui models verify; do
  has_stage "$stage" || continue
  "stage_${stage}"
done

log "Bitti. Başlatmak için: $ROOT/mamidlabs-launch"
