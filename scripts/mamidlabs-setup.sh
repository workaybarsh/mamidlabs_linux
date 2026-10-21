#!/usr/bin/env bash
# Starts the MamidLabs setup wizard (Python 3.12 + PySide6 / Qt6).
#
# Uses the venv of an existing install root when present, otherwise the system
# python3; so both "git clone + ./scripts/mamidlabs-setup.sh" and "mamidlabs-setup"
# on an installed system open the same wizard. Options (--root, --lang) are passed
# through to the wizard unchanged.
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
  echo "[error] python3 not found (apt install python3 python3-venv python3-pyside6.qtwidgets)" >&2
  exit 1
fi

export PYTHONPATH="${REPO_DIR}${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON" -m mamidlabs.wizard "$@"
