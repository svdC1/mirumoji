from pydantic import BaseModel, Field


class GptTemplateBase(BaseModel):
    sys_msg: str = Field(..., alias="sysMsg")
    prompt: str
