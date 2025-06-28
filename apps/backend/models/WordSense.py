"""
Pydantic Model representing a single sense on a JMDictEntry model
"""
from pydantic import BaseModel


class WordSense(BaseModel):
    """
    Pydantic Model representing a single sense on a JMDictEntry model

    Args:
      order (int): Sense order of precedence
      pos (str): Sense part of speech
      gloss (str): Sense gloss
    """
    order: int
    pos: str
    gloss: str
