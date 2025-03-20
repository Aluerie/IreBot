from __future__ import annotations

from typing import TYPE_CHECKING

from twitchio.ext import commands

from utils import const

if TYPE_CHECKING:
    import twitchio

    from ..bot import IreBot


__all__ = ("IreComponent",)


class IreComponent(commands.Component):
    """Base component to use within IreBot."""

    def __init__(self, bot: IreBot) -> None:
        self.bot: IreBot = bot

    @property
    def irene(self) -> twitchio.PartialUser:
        """Get Irene's channel from the cache."""
        return self.bot.create_partialuser(const.UserID.Irene)

    async def deliver(self, content: str) -> None:
        """A shortcut to send a message in Irene's twitch channel."""
        await self.irene.send_message(
            sender=self.bot.bot_id,
            message=content,
        )
