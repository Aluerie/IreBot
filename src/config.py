"""
_Insert Module Docstring Here._

License
-------
* This Source Code Form is subject to the terms of the [Mozilla Public License v2.0](<http://mozilla.org/MPL/2.0/>).
* Copyright (C) 2020-present [Aluerie](<https://github.com/Aluerie>).
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types_.config import Config

__all__ = ("config", "replace_secrets")


with Path("config.toml").open("rb") as fp:
    config: Config = tomllib.load(fp)  # pyright: ignore[reportAssignmentType]


DO_NOT_SPOIL_LIST: list[str] = [config["TWITCH"]["CLIENT_ID"], config["TWITCH"]["CLIENT_SECRET"], config["TOKENS"]["STEAM"]]
DO_NOT_SPOIL_PATTERN = re.compile("|".join(map(re.escape, DO_NOT_SPOIL_LIST)))


def replace_secrets(text: str) -> str:
    """Hide Secrets from my config files from a string."""
    return DO_NOT_SPOIL_PATTERN.sub("SECRET", text)
