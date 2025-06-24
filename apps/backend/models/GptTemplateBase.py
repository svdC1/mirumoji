"""
Pydantic Model representing the base for a profile's gpt template.
"""
from pydantic import BaseModel, Field


class GptTemplateBase(BaseModel):
    """
    Pydantic Model representing the base for a profile's gpt template.

    Args:
      sys_msg (str): The GPT's system message
      prompt (str): Prompt to use for calls.
    """
    sys_msg: str = Field(..., alias="sysMsg")
    prompt: str
