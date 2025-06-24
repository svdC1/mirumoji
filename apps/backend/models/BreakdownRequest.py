"""
Pydantic Model for the `/gpt/breakdown` request.
"""
from pydantic import BaseModel
from typing import Optional


class BreakdownRequest(BaseModel):
    """
    Pydantic Model for the `/gpt/breakdown` request.

    Args:
      sentence (str): The sentence to breakdown.
      focus (str, optional): Optional focus word.
    """
    sentence: str
    focus: Optional[str] = None
