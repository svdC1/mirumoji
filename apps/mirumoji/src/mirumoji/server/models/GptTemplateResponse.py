"""
Pydantic Model representing the response of `profile/gpt_template`
endpoint.
"""

from mirumoji.server.models.GptTemplateBase import GptTemplateBase


class GptTemplateResponse(GptTemplateBase):
    """
    Pydantic Model representing the response of `profile/gpt_template`
    endpoint.

    Args:
      id (str): The database ID of the template.
    """
    id: str
