from __future__ import annotations

from typing import TYPE_CHECKING

from twitchio.ext import commands

if TYPE_CHECKING:
    import twitchio

    from bot import IreBot


class IreContext(commands.Context):
    """My custom context."""

    if TYPE_CHECKING:
        bot: IreBot

        # I will only use IreContext with message commands
        # (twitchio also provides channel points commands).
        # therefore some type-hints can be reduced for convenience.
        chatter: twitchio.Chatter
        message: twitchio.ChatMessage
