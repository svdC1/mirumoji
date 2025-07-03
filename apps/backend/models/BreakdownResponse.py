"""
Pydantic Model for the `/gpt/breakdown` response.
"""
from pydantic import BaseModel
from models.FocusInfo import FocusInfo
from models.Token import Token
from typing import List


class BreakdownResponse(BaseModel):
    """
    Pydantic Model for the `/gpt/breakdown` response.

    Args:
      sentence (str): The analyzed sentence.
      focus (FocusInfo): The `FocusInfo` model.
      tokens (list): List of `Token` models.
      gpt_explanation (str): The GPT API call response.
    """
    sentence: str
    focus:  FocusInfo
    tokens:  List[Token]
    gpt_explanation: str
