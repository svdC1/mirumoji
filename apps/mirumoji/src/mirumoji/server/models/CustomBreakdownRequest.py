"""
Pydantic Model for the `/gpt/custom_breakdown` request.
"""

from pydantic import BaseModel
from typing import Optional


class CustomBreakdownRequest(BaseModel):
    """
    Pydantic Model for the `/gpt/custom_breakdown` request.

    Args:
      sentence (str): The sentence to analyze
      focus (str, optional): The optinal focus word.
      sysMsg (str): The custom system message for the model.
      prompt (str): The custom prompt for the model.
      version (str): The custom model version
    """
    sentence: str
    focus: Optional[str] = None
    sysMsg: str
    prompt: str
    version: str
