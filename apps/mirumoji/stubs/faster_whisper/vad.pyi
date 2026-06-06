class VadOptions:
    threshold: float = 0.5
    neg_threshold: float | None = None
    min_speech_duration_ms: int = 0
    max_speech_duration_s: float = float("inf")
    min_silence_duration_ms: int = 2000
    speech_pad_ms: int = 400
    ...
