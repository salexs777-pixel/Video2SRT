from video2srt.subtitles.ass import dumps, escape_text, font_size, margin_v
from video2srt.transcription.segmentation import Cue


def test_ass_escaping():
    assert escape_text("a{b}\nc") == r"a\{b\}\Nc"


def test_style_uses_local_white_box_and_black_text():
    content = dumps([Cue(0, 1, "Текст")], 1920, 1080)
    assert "BorderStyle, Outline" in content
    assert "Default,Arial,43,&H00000000" in content
    assert ",3,8,0,2," in content


def test_portrait_and_landscape_have_same_adaptive_size():
    assert font_size(1080, 1920) == font_size(1920, 1080) == 43
    assert margin_v(1080, 1920) == margin_v(1920, 1080)


def test_font_size_is_clamped():
    assert font_size(320, 240) == 24
    assert font_size(8000, 8000) == 64
