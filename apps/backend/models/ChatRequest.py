"""
Pydantic Model for the `/gpt/stream` request.
"""
from processing.gpt_wrapper import GptModel
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
    prompt: str = Field(..., description="The user’s message")
    model: str = Field(
        "gpt-4.1",
        description="One of: " + ", ".join(GptModel.model_versions)
    )
    system_message: str = Field(
        "You are a helpful assistant.",
        description="Custom system prompt"
    )
