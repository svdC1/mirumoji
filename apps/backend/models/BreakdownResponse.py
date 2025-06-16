from pydantic import BaseModel, ConfigDict
from models.FocusInfo import FocusInfo
from models.Token import Token
from typing import List


class BreakdownResponse(BaseModel):
    sentence: str
    focus:  FocusInfo
    tokens:  List[Token]
    gpt_explanation: str

    # Pydantic v2 style config
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore"
    )
