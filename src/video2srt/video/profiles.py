from __future__ import annotations


def encoder_args(encoder: str, quality: str) -> list[str]:
    value = "18" if quality == "original" else "23"
    if encoder == "h264_nvenc":
        return [
            "-c:v",
            encoder,
            "-preset",
            "p6",
            "-tune",
            "hq",
            "-rc",
            "vbr",
            "-cq",
            value,
            "-b:v",
            "0",
        ]
    if encoder == "h264_qsv":
        return ["-c:v", encoder, "-preset", "slow", "-global_quality", value]
    if encoder == "h264_amf":
        return [
            "-c:v",
            encoder,
            "-quality",
            "quality",
            "-rc",
            "cqp",
            "-qp_i",
            value,
            "-qp_p",
            value,
        ]
    return ["-c:v", "libx264", "-preset", "medium", "-crf", value]


def scale_filter(width: int, height: int, quality: str) -> str | None:
    if quality == "original":
        return None
    max_width, max_height = (1080, 1920) if height > width else (1920, 1080)
    if width <= max_width and height <= max_height:
        return None
    return (
        f"scale='min({max_width},iw)':'min({max_height},ih)':force_original_aspect_ratio=decrease"
    )
