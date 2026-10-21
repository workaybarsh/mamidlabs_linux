# MamidLabs Linux packaging (.deb)

This folder builds the **`.deb` package** of the MamidLabs Linux edition. The package
contains the application sources and the **setup wizard**; after installing the
package, the **"MamidLabs Setup"** icon in the application menu opens the wizard.

## Why `.deb`

The installation (llama.cpp, ComfyUI, ~36–52 GB of models) has to be done by asking the
user questions. The `.deb` therefore is not a *ready installation* but a distributor of
the **installation tool**:

1. `sudo apt install ./mamidlabs_1.0.0_all.deb`
2. **MamidLabs Setup** from the application menu → wizard:
   language (EN/TR) → welcome → licence → folder → hardware report → profile
   (LITE/PRO/no download/own model) → (own models) → (API) →
   (components) → ready → install → summary → finish.

## Building

```bash
packaging/linux/build-deb.sh
# output: packaging/linux/Output/mamidlabs_1.0.0_all.deb
```

Options: `--output <dir>` (output location), `--arch <all|amd64>` (default `all`).

Requirement: `dpkg-deb` (`apt install dpkg-dev`). Python is not needed on the build
machine; the version is read from `mamidlabs/__init__.py`.

## Files the package installs

| Path | Contents |
|---|---|
| `/usr/lib/mamidlabs/mamidlabs` | Python package (application + wizard + locale catalogs) |
| `/usr/lib/mamidlabs/scripts` | `install-mamidlabs.sh`, `manage-…`, `smoke-test.sh`, `mamidlabs-setup.sh` |
| `/usr/bin/mamidlabs-setup` | Wizard launcher (`python3 -m mamidlabs.wizard`) |
| `/usr/bin/mamidlabs` | Application launcher (`python3 -m mamidlabs`) |
| `/usr/share/applications/mamidlabs-setup.desktop` | Setup wizard icon |
| `/usr/share/applications/mamidlabs.desktop` | Application icon |
| `/usr/share/icons/hicolor/scalable/apps/mamidlabs.svg` | Icon |

The package is **architecture-independent** (`Architecture: all`): it contains no
compiled binaries, only Python. The default install root is
`~/.local/share/mamidlabs` (change it with `MAMIDLABS_ROOT`).

## Dependencies

`Depends: python3 (>= 3.11), python3-venv, python3-pyside6.qtwidgets`

The `python3-pyside6.qtwidgets` package exists on Debian trixie / Ubuntu 24.04 and
later. If an older distribution does not have this name, install Qt with pip:

```bash
pip install --break-system-packages PySide6
```

Without Qt the wizard prints the `wizard.error.no_pyside` message and exits with code
**2**; the installation can also be done from the terminal:

```bash
/usr/lib/mamidlabs/scripts/install-mamidlabs.sh --profile flash --language en
```

## Without a desktop (server/SSH)

The wizard needs a graphical desktop (`DISPLAY`/`WAYLAND_DISPLAY`); without it, it
exits with code **1** and the `wizard.error.no_display` message and suggests the
terminal script. This behaviour lives in `mamidlabs/wizard/__main__.py`.
