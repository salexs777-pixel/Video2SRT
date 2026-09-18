from video2srt.transcription.segmentation import Word, segment_words, wrap_text


def test_wraps_to_two_lines_without_splitting_words():
    text = "Один два три четыре пять шесть семь восемь девять десять"
    result = wrap_text(text, width=24)
    assert result.count("\n") == 1
    assert result.replace("\n", " ") == text


def test_segments_on_sentence_and_duration():
    words = [
        Word("Это", 0, 0.4),
        Word("первое", 0.4, 1),
        Word("предложение.", 1, 2),
        Word("Это", 2.2, 2.5),
        Word("второе", 2.5, 3.2),
        Word("предложение.", 3.2, 4),
    ]
    cues = segment_words(words, max_chars=84)
    assert len(cues) == 2
    assert cues[0].text.endswith("предложение.")
    assert all(cue.end > cue.start for cue in cues)


def test_long_stream_is_split():
    words = [Word("длинноеслово", i, i + 0.9) for i in range(10)]
    cues = segment_words(words, max_chars=30, max_duration=3)
    assert len(cues) >= 4
