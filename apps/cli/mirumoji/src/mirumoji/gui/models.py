"""
Pydantic models for the GUI FastAPI application.
"""

from pydantic import BaseModel, Field
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
      MIRUMOJI_LOGGING_LEVEL (str, optional): Level of logging to run the
                                              application inside the container.
                                              Defaults to `INFO`
      MIRUMOJI_MODAL_GPU (str, optional): Which GPU to request Modal. Defaults
                                          to `A10G`
      MODAL_FORCE_BUILD (bool, optional): Whether to re-pull the Modal Image
                                          on every Modal run. Defaults to False
      repository (str, optional): Wether to pull images from `GitHub` or
                                 `DockerHub` if `local=False`
    """
    gpu: bool
    local: bool
    OPENAI_API_KEY: str
    MIRUMOJI_LOGGING_LEVEL: str = Field(default="INFO")
    MODAL_TOKEN_ID: Optional[str]
    MODAL_TOKEN_SECRET: Optional[str]
    MIRUMOJI_MODAL_GPU: Optional[str] = Field(default="A10G")
    MODAL_FORCE_BUILD: Optional[bool] = Field(default=False)
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
