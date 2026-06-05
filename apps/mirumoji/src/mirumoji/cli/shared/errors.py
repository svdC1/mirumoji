"""
Defines the launcher's typed exceptions

tip: Usage
    The `shared` core raises these so the presentation layers (Rich CLI,
    Flet GUI) can map them to friendly messages and exit codes without parsing
    strings
"""


class LauncherError(Exception):
    """
    Base class for all launcher errors
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
