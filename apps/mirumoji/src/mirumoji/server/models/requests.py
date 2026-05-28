from pydantic import BaseModel, Field


class BreakdownRequest(BaseModel):
    """
    Pydantic Model for the `/gpt/breakdown` request.

    Args:
      sentence (str): The sentence to breakdown.
      focus (str, optional): Optional focus word.
    """

    sentence: str
    focus: str | None = None


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
    focus: str | None = None
    sysMsg: str
    prompt: str
    version: str
