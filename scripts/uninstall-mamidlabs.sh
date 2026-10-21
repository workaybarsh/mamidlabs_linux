#!/usr/bin/env bash
# MamidLabs (Linux) uninstaller.
#
# Removes everything the installer created under the install root, plus the
# .desktop launcher and icon. Never touches anything outside the root.
#
#   --keep-user-data   keep settings/, chats/, models/, outputs/, tools/
#   --dry-run          show what would be removed, change nothing
#   --yes              do not ask for confirmation
set -euo pipefail

ROOT="${MAMIDLABS_ROOT:-$HOME/.local/share/mamidlabs}"
KEEP_USER_DATA=0
DRY_RUN=0
ASSUME_YES=0

usage() {
  cat <<'EOF'
Usage: uninstall-mamidlabs.sh [options]

  --root <path>       Install root (default: ~/.local/share/mamidlabs)
  --keep-user-data    Keep settings/chats/models/outputs
  --dry-run           Only show what would be deleted
  --yes               Do not ask for confirmation
  -h, --help          This text
EOF
}

log()  { printf '\033[1;34m[MamidLabs]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warning]\033[0m %s\n' "$*" >&2; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root) ROOT="$2"; shift 2 ;;
    --keep-user-data) KEEP_USER_DATA=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --yes) ASSUME_YES=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) warn "unknown option: $1"; usage; exit 2 ;;
  esac
done

export MAMIDLABS_ROOT="$ROOT"
ROOT="$(realpath -m "$ROOT")"

# Safety: refuse to delete obviously wrong locations.
case "$ROOT" in
  "/"|"$HOME"|"/home"|"/usr"|"/etc"|"/var"|"/opt"|"/tmp"|"")
    warn "Safety: '$ROOT' will not be removed."; exit 1 ;;
esac
[[ "$ROOT" == "$HOME"/* ]] || [[ -n "${MAMIDLABS_ALLOW_OUTSIDE_HOME:-}" ]] || {
  warn "Install root is outside the home directory: $ROOT (force with MAMIDLABS_ALLOW_OUTSIDE_HOME=1)."
  exit 1
}

log "Install root: $ROOT"

# 1. Stop anything running from this root.
if [[ $DRY_RUN -eq 0 ]]; then
  for pid in $(pgrep -f "$ROOT" 2>/dev/null || true); do
    [[ "$pid" == "$$" ]] && continue
    kill "$pid" 2>/dev/null || true
  done
  sleep 1
  for pid in $(pgrep -f "$ROOT" 2>/dev/null || true); do
    [[ "$pid" == "$$" ]] && continue
    kill -9 "$pid" 2>/dev/null || true
  done
  log "Stopped the processes running from this root."
fi

# 2. Remove the launcher and icon.
APPS="$HOME/.local/share/applications/mamidlabs.desktop"
ICON="$HOME/.local/share/icons/hicolor/scalable/apps/mamidlabs.svg"
for f in "$APPS" "$ICON"; do
  [[ -e "$f" ]] || continue
  if [[ $DRY_RUN -eq 1 ]]; then log "would delete: $f"; else rm -f "$f"; log "deleted: $f"; fi
done

# 3. Remove the root (or only program files when keeping user data).
if [[ ! -e "$ROOT" ]]; then
  log "The install root does not exist."
  exit 0
fi

if [[ $KEEP_USER_DATA -eq 1 ]]; then
  log "Keeping user data (--keep-user-data)."
  KEEP=(settings chats models outputs tools logs)
  if [[ $DRY_RUN -eq 1 ]]; then
    for entry in "$ROOT"/*; do
      base="$(basename "$entry")"
      for k in "${KEEP[@]}"; do [[ "$base" == "$k" ]] && continue 2; done
      log "would delete: $entry"
    done
  else
    for entry in "$ROOT"/*; do
      base="$(basename "$entry")"
      for k in "${KEEP[@]}"; do [[ "$base" == "$k" ]] && continue 2; done
      rm -rf "$entry"
    done
    log "Program files deleted; user data kept."
  fi
  exit 0
fi

if [[ $ASSUME_YES -eq 0 && $DRY_RUN -eq 0 ]]; then
  read -r -p "The entire MamidLabs installation will be deleted ($ROOT). Do you confirm? [y/N] " reply
  [[ "$reply" =~ ^[yY] ]] || { log "Cancelled."; exit 0; }
fi

if [[ $DRY_RUN -eq 1 ]]; then
  log "would delete: $ROOT (everything)"
else
  rm -rf "$ROOT"
  log "Installation fully removed: $ROOT"
fi
