"""
Minimal stubs for the `srt` library (only what the server uses)
"""

import datetime
from collections.abc import Iterable

class Subtitle:
    index: int
    start: datetime.timedelta
    end: datetime.timedelta
    content: str

    def __init__(
        self,
        index: int,
        start: datetime.timedelta,
        end: datetime.timedelta,
        content: str,
        proprietary: str = ...,
    ) -> None: ...

def compose(subtitles: Iterable[Subtitle]) -> str: ...
