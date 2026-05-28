from pydantic import BaseModel, Field


class GptTemplateBase(BaseModel):
    """
    Pydantic Model representing the base for a profile's gpt template.

    Args:
      sys_msg (str): The GPT's system message
      prompt (str): Prompt to use for calls
      version (str): The GPT model version to use
    """

    sys_msg: str = Field(..., alias="sysMsg")
    prompt: str
    version: str = Field(default="gpt-4.1-mini")
