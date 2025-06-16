from pydantic import BaseModel
from typing import List


class FocusInfo(BaseModel):
    word: str
    reading: str
    meanings: List[str]
    jlpt: str
    examples: List[str]
