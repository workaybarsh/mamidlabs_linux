"""Hardware measurement and profile recommendation (pure parsers + thresholds)."""

from __future__ import annotations

import pytest

from mamidlabs.core import hwinfo


def test_parse_nvidia_smi_reads_name_memory_driver():
    text = ("NVIDIA GeForce RTX 5060 Ti, 16311, 617.42\n"
            "NVIDIA GeForce RTX 4060 Laptop GPU, 8188, 560.95\n")
    gpus = hwinfo.parse_nvidia_smi(text)
    assert [g.name for g in gpus] == ["NVIDIA GeForce RTX 5060 Ti",
                                     "NVIDIA GeForce RTX 4060 Laptop GPU"]
    assert gpus[0].vram_mib == 16311
    assert gpus[1].driver == "560.95"


def test_parse_nvidia_smi_skips_malformed_lines():
    assert hwinfo.parse_nvidia_smi("bogus\n\n,,\n") == []


def test_parse_meminfo_total_in_mib():
    assert hwinfo.parse_meminfo("MemTotal:       32768000 kB\nMemFree: 100 kB\n") == 32000


def test_parse_meminfo_without_memtotal():
    assert hwinfo.parse_meminfo("MemFree: 100 kB\n") == 0


def test_parse_cpuinfo_model_and_cores():
    text = ("processor\t: 0\nmodel name\t: AMD Ryzen 5 3600\n\n"
            "processor\t: 1\nmodel name\t: AMD Ryzen 5 3600\n")
    model, cores = hwinfo.parse_cpuinfo(text, ncpu=12)
    assert model == "AMD Ryzen 5 3600"
    assert cores == 2


def test_parse_cpuinfo_falls_back_to_ncpu():
    assert hwinfo.parse_cpuinfo("", ncpu=8)[1] == 8


@pytest.mark.parametrize("vram,expected", [
    (16311, "flash"),
    (15000, "flash"),
    (14000, "lite"),
    (8188, "lite"),
    (7000, "lite"),
    (4096, "own"),
    (0, "own"),
])
def test_recommend_thresholds_match_windows(vram, expected):
    report = hwinfo.Report(gpus=[hwinfo.Gpu("Test", vram)])
    assert hwinfo.recommend(report) == expected


def test_report_gpu_helpers_pick_the_largest_card():
    report = hwinfo.Report(gpus=[hwinfo.Gpu("small", 4096), hwinfo.Gpu("big", 16311)])
    assert report.gpu_name == "big"
    assert report.vram_mib == 16311


def test_warnings_without_nvidia_tell_the_user_to_use_api():
    assert "wizard.report.no_nvidia" in hwinfo.warnings(hwinfo.Report())


def test_warnings_flag_a_tight_disk():
    report = hwinfo.Report(gpus=[hwinfo.Gpu("big", 16311)], free_gib=10.0,
                           ram_mib=64 * 1024)
    assert "wizard.report.low_disk" in hwinfo.warnings(report)


def test_measure_never_raises(tmp_path):
    report = hwinfo.measure(tmp_path)
    assert isinstance(report, hwinfo.Report)
