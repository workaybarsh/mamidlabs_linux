"""Setup wizard: the pure helpers and (when PySide6 exists) the Qt window.

The helper tests run on a bare interpreter; the window tests are skipped without
PySide6, exactly like the rest of the suite.
"""

from __future__ import annotations

import os
import pathlib
import re

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from mamidlabs import wizard  # noqa: E402
from mamidlabs.core import i18n  # noqa: E402


# --- pure helpers ------------------------------------------------------------


def test_build_install_args_local_profile():
    args = wizard.build_install_args("/root", "lite", "tr")
    assert args == ["--root", "/root", "--language", "tr", "--profile", "lite"]


def test_build_install_args_skips_unchecked_components():
    args = wizard.build_install_args("/r", "flash", "en", media=False, audio=False,
                                     ocr=False)
    assert args[:6] == ["--root", "/r", "--language", "en", "--profile", "flash"]
    assert "--skip-media" in args and "--skip-audio" in args and "--skip-ocr" in args


def test_build_install_args_without_download_skips_models():
    args = wizard.build_install_args("/r", None, "tr", download_models=False)
    assert "--skip-models" in args
    assert "--profile" not in args


def test_build_install_args_still_skips_models_when_profile_is_none():
    args = wizard.build_install_args("/r", None, "en")
    assert "--skip-models" in args and "--profile" not in args


def test_build_smoke_args():
    assert wizard.build_smoke_args("/r", "lite") == ["--root", "/r", "--profile", "lite"]
    assert wizard.build_smoke_args("/r", None) == ["--root", "/r"]


@pytest.mark.parametrize("text,expected", [
    ("1\n7\nlayout\n", (1, 7, "layout")),
    ("2\n7\nllama\n", (2, 7, "llama")),
    ("", (0, 0, "")),
    ("x\ny\nz\n", (0, 0, "")),
    ("3\n7\n", (0, 0, "")),
    ("0\n0\npreflight\n", (0, 0, "")),
])
def test_parse_progress(text, expected):
    assert wizard.parse_progress(text) == expected


def test_stage_names_track_the_installer_script():
    script = wizard.repo_root() / "scripts" / "install-mamidlabs.sh"
    text = script.read_text(encoding="utf-8")
    stages = wizard.stage_names()
    for stage in stages:
        assert f"stage_{stage}()" in text, f"{stage} aşaması betikte yok"
    assert "for stage in " + " ".join(stages) in text


def test_step_label_translates_and_falls_back():
    i18n.set_language("tr")
    assert wizard.step_label("llama") == "llama.cpp"
    assert wizard.step_label("verify") == "Doğrulama"
    assert wizard.step_label("bilinmeyen-adim") == "bilinmeyen-adim"


def test_find_install_script_honours_the_env_override(tmp_path, monkeypatch):
    fake = tmp_path / "install-mamidlabs.sh"
    fake.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    monkeypatch.setenv("MAMIDLABS_INSTALL_SCRIPT", str(fake))
    assert wizard.find_install_script() == fake


def test_find_install_script_finds_the_repo_copy(monkeypatch):
    monkeypatch.delenv("MAMIDLABS_INSTALL_SCRIPT", raising=False)
    found = wizard.find_install_script()
    assert found is not None
    assert found.name == "install-mamidlabs.sh"


def test_find_eula_exists_in_the_repo(monkeypatch):
    assert wizard.find_eula() is not None


def test_every_wizard_key_used_in_code_is_in_the_catalogs():
    package = pathlib.Path(wizard.__file__).parent
    catalogs = {code: _catalog(code) for code in i18n.SUPPORTED}
    literal = re.compile(r"""["'](wizard\.[a-z_]+(?:\.[a-z_]+)*)["']""")
    for name in ("__init__.py", "setup.py", "__main__.py"):
        text = (package / name).read_text(encoding="utf-8")
        for key in literal.findall(text):
            for code, catalog in catalogs.items():
                assert _known(key, catalog), f"{code}.json eksik: {key}"
    # The dynamic families the window builds from lists.
    for code, catalog in catalogs.items():
        for stage in wizard.stage_names():
            assert f"wizard.stage.{stage}" in catalog, f"{code}: wizard.stage.{stage}"
        for comp in ("media", "audio", "ocr", "smoke"):
            assert f"wizard.components.{comp}" in catalog
        for profile in ("lite", "pro", "later", "own"):
            assert f"wizard.profile.{profile}" in catalog


def _catalog(code: str) -> dict[str, str]:
    import json

    path = i18n.LOCALES_DIR / f"{code}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _known(key: str, catalog: dict[str, str]) -> bool:
    return key in catalog or any(existing.startswith(key + ".") for existing in catalog)


# --- Qt window (skipped without PySide6) -------------------------------------

pytest.importorskip("PySide6", reason="PySide6 is only needed for the window tests")

from PySide6.QtWidgets import QApplication  # noqa: E402

from mamidlabs.core.paths import Paths  # noqa: E402
from mamidlabs.core.settings import Settings  # noqa: E402
from mamidlabs.wizard.setup import (ID_API, ID_COMPONENTS, ID_INSTALL, ID_LANG,  # noqa: E402
                                    ID_OWN, ID_PROFILE, ID_READY, ID_REPORT,
                                    SetupWizard)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture(autouse=True)
def _turkish():
    i18n.set_language("tr")
    yield
    i18n.set_language("tr")


def _wizard(tmp_path) -> SetupWizard:
    window = SetupWizard(root=tmp_path / "root", language="tr")
    window.restart()  # QWizard only tracks currentId() after it is started
    return window


def test_wizard_builds_all_pages(qapp, tmp_path):
    window = _wizard(tmp_path)
    try:
        assert window.windowTitle() == i18n.t("wizard.title")
        assert len(window.pages) == 13
        assert window.pages[ID_LANG].title() == i18n.t("wizard.lang.title")
    finally:
        window.close()


def test_language_switch_retranslates_live(qapp, tmp_path):
    window = _wizard(tmp_path)
    try:
        turkish = window.pages[ID_LANG].title()
        window._set_language("en")
        assert window.windowTitle() == "MamidLabs setup wizard"
        assert window.pages[ID_LANG].title() == "Language"
        window._set_language("tr")
        assert window.pages[ID_LANG].title() == turkish
    finally:
        window.close()


def test_language_switch_is_persisted(qapp, tmp_path):
    window = _wizard(tmp_path)
    try:
        window._set_language("en")
        saved = Settings(Paths(window.root()))
        saved.load()
        assert saved.language == "en"
    finally:
        window.close()


def test_profile_page_prefills_the_recommendation(qapp, tmp_path):
    from mamidlabs.core import hwinfo

    window = _wizard(tmp_path)
    try:
        window.report = hwinfo.Report(gpus=[hwinfo.Gpu("RTX 5060 Ti", 16311)])
        window.pages[ID_PROFILE].initializePage()
        assert window.pages[ID_PROFILE].choice() == "flash"
        assert window.install_profile() == "flash"

        window.report = hwinfo.Report()  # no NVIDIA → "later" + API hint
        window.pages[ID_PROFILE].initializePage()
        assert window.pages[ID_PROFILE].choice() == "later"
        assert window.install_profile() is None
    finally:
        window.close()


def test_report_page_formats_the_measurement(qapp, tmp_path):
    from mamidlabs.core import hwinfo

    window = _wizard(tmp_path)
    try:
        window.report = hwinfo.Report(gpus=[hwinfo.Gpu("RTX 5060 Ti", 16311)],
                                      ram_mib=64 * 1024, cpu="Ryzen 5 3600", cores=12,
                                      distro="Ubuntu 24.04", free_gib=200.0)
        text = window.format_report(window.report)
        assert "RTX 5060 Ti" in text
        assert "16311 MiB" in text
        assert i18n.t("wizard.report.recommend") in text
    finally:
        window.close()


def test_page_flow_depends_on_the_profile_choice(qapp, tmp_path):
    window = _wizard(tmp_path)
    try:
        window.setCurrentId(ID_PROFILE)
        for choice, expected in (("own", ID_OWN), ("later", ID_API),
                                 ("lite", ID_COMPONENTS), ("flash", ID_COMPONENTS)):
            window.pages[ID_PROFILE].buttons[choice].setChecked(True)
            assert window.nextId() == expected, choice
        # After the API page, "later" goes straight to the summary; a local
        # profile still shows the components page.
        window.setCurrentId(ID_API)
        window.pages[ID_PROFILE].buttons["later"].setChecked(True)
        assert window.nextId() == ID_READY
        window.pages[ID_PROFILE].buttons["lite"].setChecked(True)
        assert window.nextId() == ID_COMPONENTS
    finally:
        window.close()


def test_install_page_reads_a_progress_file(qapp, tmp_path):
    window = _wizard(tmp_path)
    try:
        logs = window.root() / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        (logs / "kurulum-adim.txt").write_text("3\n7\npython\n", encoding="utf-8")
        window.read_progress()
        assert window.progress == (3, 7, "python")
        # A malformed file must not crash the poll loop.
        (logs / "kurulum-adim.txt").write_text("cevap\n", encoding="utf-8")
        window.read_progress()
        assert window.progress == (0, 0, "")
    finally:
        window.close()


def test_summary_page_handles_a_missing_file(qapp, tmp_path):
    window = _wizard(tmp_path)
    try:
        expected = i18n.t("wizard.summary.missing",
                          path=window.root() / "logs" / "kurulum-ozeti.txt")
        assert window.format_summary_file() == expected
    finally:
        window.close()


def test_write_settings_records_the_choices(qapp, tmp_path):
    window = _wizard(tmp_path)
    try:
        window.pages[ID_PROFILE].buttons["own"].setChecked(True)
        window.pages[ID_OWN].edits["llm"].setText("/models/x.gguf")
        window.pages[ID_API].open_box.setChecked(True)
        window.write_settings()

        saved = Settings(Paths(window.root()))
        saved.load()
        assert saved["language"] == "tr"
        assert saved["localModels"] == ["/models/x.gguf"]
        assert saved["firstRunApiSettings"] is True
    finally:
        window.close()


def test_install_page_is_not_complete_until_finished(qapp, tmp_path):
    window = _wizard(tmp_path)
    try:
        page = window.pages[ID_INSTALL]
        assert page.isComplete() is False
        page.finished = True
        assert page.isComplete() is True
    finally:
        window.close()


def test_own_page_rejects_a_missing_file(qapp, tmp_path):
    window = _wizard(tmp_path)
    try:
        page = window.pages[ID_OWN]
        assert page.isComplete()  # empty fields are fine
        page.edits["llm"].setText(str(tmp_path / "yok.gguf"))
        assert not page.isComplete()
    finally:
        window.close()

