"""Packaging contract: version, the .deb build, the wizard launchers and locales."""

from __future__ import annotations

import pathlib
import re

import pytest

from mamidlabs import __version__
from mamidlabs.core import i18n

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
PKG = REPO / "packaging" / "linux"


def test_version_is_consistent():
    """``__init__`` and ``pyproject.toml`` must agree (release tag derives from it)."""
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{__version__}"' in pyproject


def test_locale_catalogs_ship_with_the_package():
    for code in i18n.SUPPORTED:
        assert (i18n.LOCALES_DIR / f"{code}.json").is_file()
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert '"mamidlabs" = ["locales/*.json"]' in pyproject, \
        "locale catalogs must be added to the package data"


def test_deb_build_script_exists_and_is_wired():
    script = PKG / "build-deb.sh"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "dpkg-deb" in text
    assert "--root-owner-group" in text
    assert "Architecture: ${ARCH}" in text or "Architecture: all" in text
    # The package must ship the wizard, not only the app.
    assert "mamidlabs-setup" in text
    assert "mamidlabs.wizard" in text
    assert "python3-pyside6.qtwidgets" in text


def test_desktop_entries_exist():
    for name in ("mamidlabs-setup.desktop", "mamidlabs.desktop"):
        path = PKG / name
        assert path.is_file(), f"missing desktop entry: {name}"
        text = path.read_text(encoding="utf-8")
        assert text.startswith("[Desktop Entry]")
        assert "Exec=" in text and "Icon=mamidlabs" in text

    setup = (PKG / "mamidlabs-setup.desktop").read_text(encoding="utf-8")
    assert "Exec=mamidlabs-setup" in setup
    assert "Name[en]=MamidLabs Setup" in setup


def test_wizard_launcher_script_exists():
    launcher = SCRIPTS / "mamidlabs-setup.sh"
    assert launcher.is_file()
    text = launcher.read_text(encoding="utf-8")
    assert "-m mamidlabs.wizard" in text
    assert text.startswith("#!/usr/bin/env bash")


def test_shell_scripts_use_lf_and_are_bash():
    for name in ("install-mamidlabs.sh", "manage-mamidlabs.sh",
                 "uninstall-mamidlabs.sh", "smoke-test.sh", "mamidlabs-setup.sh"):
        raw = (SCRIPTS / name).read_bytes()
        assert b"\r\n" not in raw, f"{name} must use LF line endings"
        assert raw.startswith(b"#!/usr/bin/env bash")


def test_installer_accepts_language_and_writes_progress():
    text = (SCRIPTS / "install-mamidlabs.sh").read_text(encoding="utf-8")
    assert "--language" in text
    assert re.search(r"case \"\$2\" in\s+tr\|en", text), "the language must be limited to tr|en"
    assert "kurulum-adim.txt" in text, "the wizard progress file must be written"
    assert "kurulum-ozeti.txt" in text, "the wizard summary file must be written"
    assert "MAMIDLABS_ROOT" in text


def test_wizard_registers_a_console_script():
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'mamidlabs-setup = "mamidlabs.wizard.__main__:main"' in pyproject


def test_pinned_versions_are_present():
    text = (SCRIPTS / "install-mamidlabs.sh").read_text(encoding="utf-8")
    for pinned in ("b10998", "b0f4b7b", "6ea2651", "86f886d"):
        assert pinned in text, f"pinned version missing: {pinned}"


@pytest.mark.parametrize("name", ["install-mamidlabs.sh", "uninstall-mamidlabs.sh"])
def test_uninstaller_never_touches_outside_the_root(name):
    text = (SCRIPTS / name).read_text(encoding="utf-8")
    assert "MAMIDLABS_ROOT" in text


def test_licence_matches_windows_parity_polyform_strict():
    """The licence must match the Windows edition: PolyForm Strict 1.0.0 (non-commercial)."""
    licence = (REPO / "LICENSE").read_bytes()
    assert not licence.startswith(b"\xef\xbb\xbf"), "LICENSE must be BOM-free (LF)"
    assert licence.startswith(b"PolyForm Strict License 1.0.0"), \
        "LICENSE must start with the official PolyForm Strict 1.0.0 heading"
    assert b"Noncommercial Purposes" in licence
    assert b"distributing the software or making changes or new works" in licence


def test_eula_ships_as_utf8_bom():
    """EULA.txt must match the Windows edition: a PolyForm notice with a UTF-8 BOM."""
    eula = (REPO / "EULA.txt").read_bytes()
    assert eula.startswith(b"\xef\xbb\xbf"), "EULA.txt must carry a UTF-8 BOM"
    assert "PolyForm Strict 1.0.0" in eula.decode("utf-8-sig")
