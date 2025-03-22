from __future__ import annotations

from typing import TYPE_CHECKING

from twitchio.ext import commands

if TYPE_CHECKING:
    from bot import IreBot


class IreContext(commands.Context):
    """My custom context."""

    if TYPE_CHECKING:
        bot: IreBot
