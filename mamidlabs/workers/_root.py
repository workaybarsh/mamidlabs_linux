"""Resolve the install root for standalone workers.

The workers run as separate processes (often in their own virtualenvs) and may
not have the ``mamidlabs`` package importable, so they cannot use
``mamidlabs.core.paths``. They must not derive the root from their own location
either: in the Linux edition the package lives in site-packages, not under the
install root. ``MAMIDLABS_ROOT`` (set by the app for every child process) is the
authoritative source; the XDG default is the fallback.
"""

from __future__ import annotations

import os
from pathlib import Path


def install_root() -> Path:
    env = os.environ.get("MAMIDLABS_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "share"
    return (base / "mamidlabs").resolve()
