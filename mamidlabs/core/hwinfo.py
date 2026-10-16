"""Hardware measurement and profile recommendation (Linux).

The setup wizard asks this module *what this machine can run* before it asks the
user anything. Everything is best-effort: a missing tool (``nvidia-smi``,
``lspci``, ``/proc``) degrades the report instead of failing the wizard, and the
recommendation falls back to "use an API provider" when no NVIDIA GPU is found.

Two kinds of functions live here, on purpose:

* **pure parsers** (:func:`parse_nvidia_smi`, :func:`parse_meminfo`,
  :func:`parse_cpuinfo`, :func:`recommend`, :func:`warnings`) take text/values and
  return data — the tests exercise these without touching the host;
* **probes** (:func:`measure`) run the actual commands and hand the text to the
  parsers.

The thresholds mirror the Windows edition (``AGENTS.md`` §13): the 27B profile
needs ~15000 MiB of VRAM, the 9B profile fits in ~7000 MiB. Local models require
CUDA, so a machine without an NVIDIA GPU is told to use API providers instead of
being offered a profile that would run at a crawl.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

#: VRAM (MiB) at or above which the 27B profile fits (matches the Windows gate).
PRO_VRAM_MIB = 15000

#: VRAM (MiB) at or above which the 9B profile fits.
LITE_VRAM_MIB = 7000

#: Free disk (GiB) we recommend before downloading a profile's models.
PRO_DISK_GIB = 64.0
LITE_DISK_GIB = 48.0


@dataclass
class Gpu:
    name: str = ""
    vram_mib: int = 0
    driver: str = ""


@dataclass
class Report:
    """Everything the wizard shows on the hardware page."""

    gpus: list[Gpu] = field(default_factory=list)
    ram_mib: int = 0
    cpu: str = ""
    cores: int = 0
    distro: str = ""
    free_gib: float = 0.0

    @property
    def gpu_name(self) -> str:
        if not self.gpus:
            return ""
        return max(self.gpus, key=lambda g: g.vram_mib).name

    @property
    def vram_mib(self) -> int:
        return max((g.vram_mib for g in self.gpus), default=0)

    @property
    def has_nvidia(self) -> bool:
        return any(g.vram_mib > 0 for g in self.gpus) or bool(self.gpus)


# --- pure parsers ------------------------------------------------------------


def parse_nvidia_smi(text: str) -> list[Gpu]:
    """Parse ``nvidia-smi --query-gpu=name,memory.total,driver_version`` output.

    The query uses ``--format=csv,noheader,nounits``; ``memory.total`` here is in
    MiB (nounits). Malformed lines are skipped.
    """
    gpus: list[Gpu] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2 or not parts[0]:
            continue
        digits = "".join(ch for ch in parts[1] if ch.isdigit())
        memory = int(digits) if digits else 0
        driver = parts[2] if len(parts) > 2 else ""
        gpus.append(Gpu(name=parts[0], vram_mib=memory, driver=driver))
    return gpus


def parse_meminfo(text: str) -> int:
    """Total system RAM in MiB from ``/proc/meminfo`` (``MemTotal:`` in kB)."""
    for line in text.splitlines():
        if line.startswith("MemTotal:"):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                return int(parts[1]) // 1024
    return 0


def parse_cpuinfo(text: str, ncpu: int = 0) -> tuple[str, int]:
    """``(model name, core count)`` from ``/proc/cpuinfo``.

    ``ncpu`` (``os.cpu_count()``) is only used when the file does not list
    processors, so the value stays honest on a partial file.
    """
    model = ""
    count = 0
    for line in text.splitlines():
        if not model and line.lower().startswith("model name"):
            _, _, value = line.partition(":")
            model = value.strip()
        if line.startswith("processor"):
            count += 1
    if not count:
        count = ncpu
    return model, count


def recommend(report: Report) -> str:
    """Pick a profile id: ``flash`` (PRO), ``lite`` or ``own``.

    Local models need CUDA, so no NVIDIA GPU means ``own`` (API providers).
    """
    vram = report.vram_mib
    if vram >= PRO_VRAM_MIB:
        return "flash"
    if vram >= LITE_VRAM_MIB:
        return "lite"
    return "own"


def warnings(report: Report) -> list[str]:
    """Translation keys for the yellow notes under the recommendation."""
    notes: list[str] = []
    profile = recommend(report)
    if profile == "own" and not report.vram_mib:
        notes.append("wizard.report.no_nvidia")
    elif profile == "own":
        notes.append("wizard.report.low_vram")
    need = PRO_DISK_GIB if profile == "flash" else LITE_DISK_GIB
    if report.free_gib and report.free_gib < need:
        notes.append("wizard.report.low_disk")
    if report.ram_mib and report.ram_mib < 32 * 1024:
        notes.append("wizard.report.low_ram")
    return notes


# --- probes ------------------------------------------------------------------


def _run(cmd: list[str], timeout: int = 15) -> str:
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                              check=False)
    except (OSError, subprocess.SubprocessError):
        return ""
    return done.stdout or ""


def _read(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def measure(root: Path | str | None = None) -> Report:
    """Measure the host; never raises, degrades to an empty report."""
    report = Report()

    if shutil.which("nvidia-smi"):
        text = _run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
                     "--format=csv,noheader,nounits"])
        report.gpus = parse_nvidia_smi(text)

    report.ram_mib = parse_meminfo(_read("/proc/meminfo"))
    report.cpu, report.cores = parse_cpuinfo(_read("/proc/cpuinfo"),
                                             ncpu=__import__("os").cpu_count() or 0)

    release = _read("/etc/os-release")
    for line in release.splitlines():
        if line.startswith("PRETTY_NAME="):
            report.distro = line.partition("=")[2].strip().strip('"')
    if not report.distro:
        report.distro = _run(["uname", "-srm"]).strip()

    try:
        usage = shutil.disk_usage(str(root or Path.home()))
        report.free_gib = usage.free / (1024 ** 3)
    except OSError:
        report.free_gib = 0.0

    return report
