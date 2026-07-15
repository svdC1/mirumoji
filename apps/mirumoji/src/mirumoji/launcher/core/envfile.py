"""
Defines functions to read, edit, and write a `.env` configuration file for an
end-user

The `.env` file is stored in the application's data directory in the user's
machine and is used to start the `Mirumoji` Docker Compose application with the
configuration that was selected by the user via the launcher. It is also
used to perist that information for future runs
"""

import logging
import os
from collections.abc import Iterable, Mapping
from pathlib import Path

from dotenv import dotenv_values

from ... import __version__
from .constants import IMAGE_SOURCE_VAR, TRANSCRIBE_BACKEND_VAR, VERSION_VAR
from .errors import EnvConfigError
from .models import Backend, EnvVar, ImageSource

LOGGER = logging.getLogger(__name__)

_BACKEND_VALUES = {b.value for b in Backend}
_SOURCE_VALUES = {s.value for s in ImageSource}


def read(path: Path) -> dict[str, str]:
    """
    Reads a `.env` file into a dict, ignoring blank/unset entries

    Args:
        path (Path): The `.env` file path

    Returns:
        The parsed key/value pairs, or an empty dict when the file is absent
    """
    if not path.is_file():
        return {}
    parsed = dotenv_values(path)
    return {k: v for k, v in parsed.items() if v is not None}


def overlay_environ(
    values: Mapping[str, str],
    names: Iterable[str],
) -> dict[str, str]:
    """
    Merges the environment variables stored in `values` with the ones set in
    the current proccess' context (accessed via os.environ) if they're listed
    in `names`

    For each named variable not already set in `values`, adds a non-empty
    value from `os.environ` if present. The values in `values` take precedence
    when a named variable is present both in `values` and `os.environ`.
    Empty string values are considered as not set

    Example:
        ```python

        values = {"VAR_0": "0", "VAR_1": "V1A", "VAR_2": "V2"}
        names = ["VAR_1", "VAR_2", "VAR_3"]

        # os.environ = {"VAR_1": "V1B", "VAR_3": "V3"}

        merged = overlay_environ(values, names)
        print(merged)

        # {"VAR_0": "0", "VAR_1": "V1A", "VAR_2": "V2", "VAR_3": "V3"}
        ```

    Args:
        values (Mapping[str, str]): The values read from the `.env` file
        names (Iterable[str]): The variable names to consider

    Returns:
        A new dict combining the file values and any environment fallbacks
    """
    merged = dict(values)
    for name in names:
        if not merged.get(name) and os.environ.get(name):
            merged[name] = os.environ[name]
    return merged


def missing_required(
    specs: Iterable[EnvVar],
    values: Mapping[str, str],
) -> list[EnvVar]:
    """
    Returns the required environment variables that still have no value set

    Checks the `EnvVar.required` attribute to check if the environment
    variable is required and appends it to a list if it doesn't contain a
    value in `values`

    Args:
        specs (Iterable[EnvVar]): The environment variables to check
        values (Mapping[str, str]): The currently resolved values

    Returns:
        The required environment variables with no non-empty values
    """
    return [
        spec for spec in specs if spec.required and not values.get(spec.name)
    ]


def _quote(value: str) -> str:
    """
    Sanitizes `value` when it contains whitespaces, `#` or `'`
    in order to correctly write it to a `.env` file

    Args:
        value (str): The raw value

    Returns:
        The value, double-quoted if needed
    """
    if value and (value != value.strip() or any(c in value for c in ' #"')):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return value


def write(path: Path, values: Mapping[str, str]) -> None:
    """
    Writes resolved values to a `.env` file, skipping blanks

    Args:
        path (Path): The `.env` file path to write to
        values (Mapping[str, str]): The values to persist
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"{key}={_quote(value)}" for key, value in values.items() if value
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    LOGGER.debug(f"Wrote {len(lines)} Variables To {path}")


def import_file(source: Path, target: Path) -> dict[str, str]:
    """
    Merges an external `.env` file into the managed config file

    Reads the managed `target`, overrides its values with the values present
    in `source` (keys absent from `source` are kept),
    and writes the merged result back to `target`

    Args:
        source (Path): The external `.env` file to import
        target (Path): The managed config file to overwrite

    Returns:
        The merged values now persisted in `target`

    Raises:
        EnvConfigError: If `source` does not exist or cannot be read
    """
    if not source.is_file():
        raise EnvConfigError(f"Couldn't Find {source}")
    try:
        incoming = read(source)
    except OSError as exc:
        raise EnvConfigError(f"Could Not Read {source}  ↦  {exc}") from exc
    merged = {**read(target), **incoming}
    write(target, merged)
    LOGGER.debug(
        f"Imported {len(incoming)} Variables From {source} Into {target}"
    )
    return merged


def set_value(path: Path, key: str, value: str) -> None:
    """
    Upserts a single key into the `.env` file, preserving the others

    Args:
        path (Path): The `.env` file to update
        key (str): The variable name to set
        value (str): The value to write
    """
    values = read(path)
    values[key] = value
    write(path, values)
    LOGGER.debug(f"Set {key} In {path}")


def delete_value(path: Path, key: str) -> bool:
    """
    Removes a single key from the `.env` file, preserving the others

    Args:
        path (Path): The `.env` file to update
        key (str): The variable name to remove

    Returns:
        `True` when the key was present and removed, `False` otherwise
    """
    values = read(path)
    if key not in values:
        return False
    del values[key]
    write(path, values)
    LOGGER.debug(f"Deleted {key} From {path}")
    return True


def read_deployment(
    env: Mapping[str, str],
) -> tuple[Backend | None, ImageSource | None]:
    """
    Parses the persisted deployment choice from the resolved values
    of a managed config file


    Missing or unrecognised values return `None` so that callers can
    fall back to a flag or a built-in default

    Args:
        env (Mapping[str, str]): The resolved environment values

    Returns:
        The persisted `(backend, source)`, each `None` when absent/invalid
    """
    raw_backend = env.get(TRANSCRIBE_BACKEND_VAR)
    raw_source = env.get(IMAGE_SOURCE_VAR)
    backend = Backend(raw_backend) if raw_backend in _BACKEND_VALUES else None
    source = ImageSource(raw_source) if raw_source in _SOURCE_VALUES else None
    return backend, source


def resolve_version(env_path: Path, flag: str | None = None) -> str:
    """
    Resolves the published image version the launcher pulls and composes with

    info: Order of Precedence
        The value is considered in the following order

        - The `flag` passed to a command (`--version`)

        - The persisted `MIRUMOJI_VERSION`, overlaid with the process
          environment

        - The installed package version

    Args:
        env_path (Path): The managed config file to read
        flag (str | None): An explicit override (the CLI `--version`)

    Returns:
        The version that fills the `{version}` in the image references
    """
    if flag:
        return flag
    values = overlay_environ(read(env_path), [VERSION_VAR])
    return values.get(VERSION_VAR) or __version__
