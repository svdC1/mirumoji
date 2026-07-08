"""
Defines typed exception that the launcher may raise

tip: Usage
    This sub-package (`core`) raises these so that the presentation layers
    (Rich CLI, Flet GUI) can map them to friendly messages and exit codes
    without parsing strings
"""

from ...exceptions import MirumojiLauncherError


class LauncherError(MirumojiLauncherError):
    """
    Base class for all launcher errors

    Roots under `MirumojiLauncherError` (and so under `MirumojiError`), so the
    whole launcher error tree is part of the package hierarchy
    """


class DependencyError(LauncherError):
    """
    A required external dependency is missing or not functioning

    Raised when `Docker`, `Git`, or another pre-requisite the requested action
    needs is unavailable
    """


class EnvConfigError(LauncherError):
    """
    The resolved environment is invalid for the requested action

    Raised when a required environment variable is missing and prompts are
    disabled, or when a `.env` file cannot be read
    """


class BuildSourceError(LauncherError):
    """
    Local image building cannot proceed

    Raised when the managed source checkout is unavailable and could not be
    created (e.g. git missing, or the clone failed)
    """
