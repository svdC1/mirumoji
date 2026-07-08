"""
Mirumoji, A Japanese Immersion Toolkit
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mirumoji")
except PackageNotFoundError:
    __version__ = "3.3.0"
