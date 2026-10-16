"""MamidLabs — Linux edition.

A fully local multimodal AI workspace for Linux. This package is the whole
application: the Qt6 desktop UI, the chat/tool worker, the model manager and
the installer helpers.

The Windows edition (github.com/workaybarsh/MamidLabsTR) is written in
PowerShell + WinForms; none of that runs on Linux, so this edition is a
from-scratch port in a single language (Python) that reuses the cross-platform
Python tooling (web search, document I/O, OCR, media, transcription) and the
same llama.cpp / ComfyUI engines.
"""

__version__ = "1.0.0"

APP_NAME = "MamidLabs"
