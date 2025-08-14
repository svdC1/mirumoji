"""
Pydantic models for the GUI FastAPI application.
"""

from pydantic import BaseModel
from typing import Literal, Union, Optional


class StartRequest(BaseModel):
    """
    Format of request to launch the mirumoji application
    with `api/start` endpoint

    Args:
      gpu (bool): If `True` run GPU version, otherwise run CPU version
      local (bool): If `True` run with locally built images, otherwise pull
                    from repository
      OPENAI_API_KEY (str): API Key to the OpenAI API
      MODAL_TOKEN_ID (str, optional): Modal Token ID if using CPU version
      MODAL_TOKEN_SECRET (str, optional): Modal Token Secret if using CPU
                                          version
      repository (str, optional): Wether to pull images from `GitHub` or
                                 `DockerHub` if `local=False`
    """
    gpu: bool
    local: bool
    OPENAI_API_KEY: str
    MODAL_TOKEN_ID: Optional[str]
    MODAL_TOKEN_SECRET: Optional[str]
    repository: Optional[Union[Literal["GitHub"], Literal["DockerHub"]]]


class StopRequest(BaseModel):
    """
    Format of request to stop the mirumoji application
    with `api/stop` endpoint

    Args:
      clean (bool): Wether to delete created Docker volumes and networks
    """
    clean: bool


class BuildRequest(BaseModel):
    """
    Format of request to build images locally with `api/build` endpoint

    Args:
      gpu (bool): If `True`, build GPU version of backend, otherwise build CPU
                  version
    """
    gpu: bool
