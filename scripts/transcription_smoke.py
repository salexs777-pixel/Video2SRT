"""Real local RTX/CPU transcription acceptance test with Russian Windows TTS."""

from __future__ import annotations

import argparse
import logging
import subprocess

from video2srt.core.config import AppConfig, VideoConfig, WhisperConfig
from video2srt.core.logging import setup_logging
from video2srt.core.paths import discover_paths
from video2srt.core.pipeline import Pipeline
from video2srt.core.runtime import configure_nvidia_dll_search
from video2srt.hardware.detector import detect_and_validate
from video2srt.subtitles import srt
from video2srt.transcription.segmentation import Cue


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpu", action="store_true", help="Force the CPU-only acceptance path")
    args = parser.parse_args()
    configure_nvidia_dll_search()
    paths = discover_paths()
    suffix = "cpu" if args.cpu else "gpu"
    wav = paths.output / f"acceptance_{suffix}_input.wav"
    source = paths.output / f"acceptance_{suffix}_input.mp4"
    safe_wav = str(wav).replace("'", "''")
    speech = (
        "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        "$s.SelectVoice('Microsoft Irina Desktop');"
        f"$s.SetOutputToWaveFile('{safe_wav}');"
        "$s.Speak('Добрый день. Это проверка программы создания русских субтитров.');"
        "$s.Dispose()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Add-Type -AssemblyName System.Speech;" + speech],
        check=True,
    )
    subprocess.run(
        [
            str(paths.executable("ffmpeg")),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=navy:s=640x360:r=25",
            "-i",
            str(wav),
            "-shortest",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(source),
        ],
        check=True,
    )
    hardware = detect_and_validate(paths.executable("ffmpeg"))
    device = "cpu" if args.cpu else "cuda" if hardware.cuda_available else "cpu"
    compute_type = "int8_float16" if device == "cuda" else "int8"
    encoder = "libx264" if args.cpu else "h264_nvenc" if hardware.nvenc_available else "libx264"
    model = "small" if args.cpu else "base"
    config = AppConfig(
        first_run_complete=True,
        hardware=hardware,
        whisper=WhisperConfig("auto", model, device, compute_type, 4),
        video=VideoConfig(encoder),
    )
    logger = setup_logging(paths.logs / "acceptance.log")
    logger.setLevel(logging.INFO)
    pipeline = Pipeline(paths, config, logger)
    job = pipeline.new_job(source)
    job = pipeline.transcribe(job, lambda percent, stage, status: print(percent, stage, status))
    cues = srt.read(job.srt_path)
    if not cues:
        raise RuntimeError("Whisper did not produce subtitle cues")

    # This is the same boundary used after the user saves SRT; Whisper is not called again.
    edited = [Cue(cues[0].start, cues[0].end, "Проверка ручного редактирования"), *cues[1:]]
    srt.write(edited, job.srt_path)
    pipeline.burn(job, "original", lambda percent, stage, status: print(percent, stage, status))
    if not job.video_path.exists() or job.video_path.stat().st_size < 1_000:
        raise RuntimeError("Final MP4 was not created")
    print("TRANSCRIPTION SMOKE PASS", device, encoder, job.video_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
