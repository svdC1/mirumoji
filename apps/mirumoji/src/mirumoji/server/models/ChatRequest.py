"""
Pydantic Model for the `/gpt/stream` request.
"""
from pydantic import (BaseModel,
                      Field)


class ChatRequest(BaseModel):
    """
    Pydantic Model for the `/gpt/stream` request.

    Args:
      prompt (str): The model prompt.
      model (str): The GPT version.
      system_message (str): The GPT system message
    """
    prompt: str = Field(...)
    model: str = Field("gpt-4.1")
    system_message: str = Field("You are a helpful assistant.")
