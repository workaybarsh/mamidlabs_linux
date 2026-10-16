#!/usr/bin/env bash
# MamidLabs kurulum sihirbazını başlatır (Python 3.12 + PySide6 / Qt6).
#
# Kurulu bir kök varsa onun venv'ini, yoksa sistem python3'ünü kullanır; böylece
# hem "git clone + ./scripts/mamidlabs-setup.sh" hem de kurulmuş sistemde
# "mamidlabs-setup" aynı sihirbazı açar. Seçenekler (--root, --lang) sihirbaza
# aynen geçirilir.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

ROOT_DIR="${MAMIDLABS_ROOT:-$HOME/.local/share/mamidlabs}"

PYTHON=""
if [[ -x "$ROOT_DIR/venv/app/bin/python" ]]; then
  PYTHON="$ROOT_DIR/venv/app/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON="$(command -v python)"
fi

if [[ -z "$PYTHON" ]]; then
  echo "[hata] python3 bulunamadı (apt install python3 python3-venv python3-pyside6.qtwidgets)" >&2
  exit 1
fi

export PYTHONPATH="${REPO_DIR}${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON" -m mamidlabs.wizard "$@"
