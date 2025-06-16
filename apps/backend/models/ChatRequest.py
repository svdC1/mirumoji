from processing.gpt_wrapper import GptModel
from pydantic import (BaseModel,
                      Field)


class ChatRequest(BaseModel):
    prompt: str = Field(..., description="The user’s message")
    model: str = Field(
        "gpt-4.1",
        description="One of: " + ", ".join(GptModel.model_versions)
    )
    system_message: str = Field(
        "You are a helpful assistant.",
        description="Custom system prompt"
    )
