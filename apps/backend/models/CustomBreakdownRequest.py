from pydantic import BaseModel
from typing import Optional


class CustomBreakdownRequest(BaseModel):
    sentence: str
    focus: Optional[str] = None
    sysMsg: str
    prompt: str
