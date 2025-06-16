from pydantic import BaseModel
from typing import Optional


class BreakdownRequest(BaseModel):
    sentence: str
    focus: Optional[str] = None
