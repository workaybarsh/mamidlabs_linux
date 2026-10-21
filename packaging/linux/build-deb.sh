#!/usr/bin/env bash
# MamidLabs (Linux) .deb package — together with the SETUP WIZARD.
#
# The package is architecture-independent (Architecture: all): it contains no
# compiled binaries, only Python sources + wizard launchers. After installation the
# "MamidLabs Setup" icon in the application menu opens the wizard; the wizard then
# performs the real installation (llama.cpp, ComfyUI, models) with the user's choices.
#
# Usage:
#   packaging/linux/build-deb.sh [--output <dir>] [--arch all]
#
# Requirement: dpkg-deb (Debian/Ubuntu). Python is not needed on the build machine;
# the version is read from `mamidlabs/__init__.py`.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

OUTPUT_DIR="${SCRIPT_DIR}/Output"
ARCH="all"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT_DIR="$2"; shift 2 ;;
    --arch) ARCH="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,14p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "[error] unknown option: $1" >&2; exit 1 ;;
  esac
done

command -v dpkg-deb >/dev/null 2>&1 || {
  echo "[error] dpkg-deb not found (apt install dpkg-dev)" >&2; exit 1; }

VERSION="$(sed -n 's/^__version__ = "\([^"]*\)".*/\1/p' "$REPO_DIR/mamidlabs/__init__.py" | head -n1)"
[[ -n "$VERSION" ]] || { echo "[error] could not read the version: mamidlabs/__init__.py" >&2; exit 1; }

PKG="mamidlabs_${VERSION}_${ARCH}"
STAGE="${SCRIPT_DIR}/build/${PKG}"

echo "[MamidLabs] building the .deb: $PKG"
rm -rf "$STAGE"
mkdir -p "$STAGE/DEBIAN" \
         "$STAGE/usr/lib/mamidlabs" \
         "$STAGE/usr/bin" \
         "$STAGE/usr/share/applications" \
         "$STAGE/usr/share/icons/hicolor/scalable/apps" \
         "$STAGE/usr/share/doc/mamidlabs"

# --- program files -----------------------------------------------------------
cp -r "$REPO_DIR/mamidlabs" "$STAGE/usr/lib/mamidlabs/mamidlabs"
find "$STAGE/usr/lib/mamidlabs" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$STAGE/usr/lib/mamidlabs" -name '*.pyc' -delete 2>/dev/null || true
cp -r "$REPO_DIR/scripts" "$STAGE/usr/lib/mamidlabs/scripts"
cp -r "$REPO_DIR/requirements" "$STAGE/usr/lib/mamidlabs/requirements"
cp "$REPO_DIR/pyproject.toml" "$STAGE/usr/lib/mamidlabs/"
for extra in EULA.txt LICENSE README.md CHANGELOG.md; do
  [[ -f "$REPO_DIR/$extra" ]] && cp "$REPO_DIR/$extra" "$STAGE/usr/lib/mamidlabs/"
done

# --- launchers ---------------------------------------------------------------
cat > "$STAGE/usr/bin/mamidlabs-setup" <<'EOF'
#!/bin/sh
# MamidLabs setup wizard (Qt6).
export PYTHONPATH="/usr/lib/mamidlabs${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m mamidlabs.wizard "$@"
EOF
chmod 0755 "$STAGE/usr/bin/mamidlabs-setup"

cat > "$STAGE/usr/bin/mamidlabs" <<'EOF'
#!/bin/sh
# MamidLabs application (Qt6).
export PYTHONPATH="/usr/lib/mamidlabs${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m mamidlabs "$@"
EOF
chmod 0755 "$STAGE/usr/bin/mamidlabs"

# --- desktop entries and icon ------------------------------------------------
cp "$SCRIPT_DIR/mamidlabs-setup.desktop" "$STAGE/usr/share/applications/"
cp "$SCRIPT_DIR/mamidlabs.desktop" "$STAGE/usr/share/applications/"
[[ -f "$REPO_DIR/packaging/mamidlabs.svg" ]] \
  && cp "$REPO_DIR/packaging/mamidlabs.svg" "$STAGE/usr/share/icons/hicolor/scalable/apps/mamidlabs.svg"

[[ -f "$REPO_DIR/README.md" ]] && cp "$REPO_DIR/README.md" "$STAGE/usr/share/doc/mamidlabs/README.md"
cat > "$STAGE/usr/share/doc/mamidlabs/copyright" <<'EOF'
MamidLabs
Copyright (c) 2026 Aybars Haydar Altuntaş.
This software is licensed under the PolyForm Strict License 1.0.0 (source-available; non-commercial use only).
Official text: https://polyformproject.org/licenses/strict/1.0.0
EOF

# --- DEBIAN/control ----------------------------------------------------------
INSTALLED_SIZE="$(du -sk "$STAGE" | awk '{print $1}')"
cat > "$STAGE/DEBIAN/control" <<EOF
Package: mamidlabs
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.11), python3-venv, python3-pyside6.qtwidgets
Recommends: git, curl, p7zip-full, python3-pip
Installed-Size: ${INSTALLED_SIZE}
Maintainer: Aybars Haydar Altuntas <workaybarsh@users.noreply.github.com>
Homepage: https://github.com/workaybarsh/mamidlabs_linux
Description: MamidLabs — a fully local, multimodal AI workspace
 Setup wizard and application. Chat, web search, documents, OCR, audio
 transcription, image understanding, image/video generation and chart drawing in
 one window; the models run on the user's GPU (llama.cpp + ComfyUI).
 .
 After installation the "MamidLabs Setup" icon in the application menu opens the
 wizard; it measures the hardware, suggests a suitable profile and installs.
EOF

cat > "$STAGE/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
echo "MamidLabs installed. To open the setup wizard: mamidlabs-setup"
exit 0
EOF
chmod 0755 "$STAGE/DEBIAN/postinst"

cat > "$STAGE/DEBIAN/prerm" <<'EOF'
#!/bin/sh
set -e
exit 0
EOF
chmod 0755 "$STAGE/DEBIAN/prerm"

cat > "$STAGE/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q /usr/share/applications || true
fi
exit 0
EOF
chmod 0755 "$STAGE/DEBIAN/postrm"

# --- build -------------------------------------------------------------------
mkdir -p "$OUTPUT_DIR"
dpkg-deb --root-owner-group --build "$STAGE" "${OUTPUT_DIR}/${PKG}.deb"
echo "[MamidLabs] ready: ${OUTPUT_DIR}/${PKG}.deb"
echo "[MamidLabs] install: sudo apt install ./${PKG}.deb && mamidlabs-setup"
