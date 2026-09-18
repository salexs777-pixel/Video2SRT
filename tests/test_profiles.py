import pytest

from video2srt.core.config import HardwareConfig
from video2srt.hardware.profiles import cpu_threads, select_profile


@pytest.mark.parametrize(
    ("hardware", "model", "device", "encoder"),
    [
        (
            HardwareConfig(
                cpu="Ryzen",
                logical_cores=16,
                physical_cores=8,
                ram_gb=32,
                gpu_vendor="NVIDIA",
                gpu_name="RTX 3070",
                vram_gb=8,
                cuda_available=True,
                nvenc_available=True,
            ),
            "large-v3",
            "cuda",
            "h264_nvenc",
        ),
        (
            HardwareConfig(
                cpu="Core",
                logical_cores=8,
                physical_cores=4,
                ram_gb=16,
                gpu_vendor="NVIDIA",
                vram_gb=4,
                cuda_available=True,
                nvenc_available=True,
            ),
            "medium",
            "cuda",
            "h264_nvenc",
        ),
        (
            HardwareConfig(
                cpu="Core i7",
                logical_cores=8,
                physical_cores=4,
                ram_gb=16,
                gpu_vendor="Intel",
                qsv_available=True,
            ),
            "medium",
            "cpu",
            "h264_qsv",
        ),
        (
            HardwareConfig(
                cpu="Core i3",
                logical_cores=4,
                physical_cores=2,
                ram_gb=8,
                gpu_vendor="Intel",
                qsv_available=True,
            ),
            "small",
            "cpu",
            "h264_qsv",
        ),
        (
            HardwareConfig(cpu="Weak CPU", logical_cores=2, physical_cores=2, ram_gb=8),
            "base",
            "cpu",
            "libx264",
        ),
    ],
)
def test_expected_hardware_profiles(hardware, model, device, encoder):
    profile = select_profile(hardware)
    assert (profile.whisper.model, profile.whisper.device, profile.encoder) == (
        model,
        device,
        encoder,
    )
    assert profile.whisper.compute_type == ("int8_float16" if device == "cuda" else "int8")


def test_cpu_threads_leave_resources_for_windows():
    assert cpu_threads(2) == 1
    assert cpu_threads(4) == 3
    assert cpu_threads(16) == 8


def test_gpu_failure_falls_back_to_cpu():
    hw = HardwareConfig(
        logical_cores=8,
        physical_cores=4,
        ram_gb=16,
        gpu_vendor="NVIDIA",
        vram_gb=8,
        cuda_available=False,
    )
    assert select_profile(hw).whisper.device == "cpu"
