from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from twitchio.ext import commands

from utils import const

if TYPE_CHECKING:
    import twitchio

    from ..bot import LueBot


__all__ = ("LueComponent",)

log = logging.getLogger("alerts")
log.setLevel(logging.INFO)  # DEBUG


class LueComponent(commands.Component):
    """Base component to use with LueBot."""

    def __init__(self, bot: LueBot) -> None:
        self.bot: LueBot = bot

    @property
    def irene(self) -> twitchio.PartialUser:
        """Get Irene's channel from the cache."""
        return self.bot.create_partialuser(const.UserID.Irene)

    async def deliver(self, content: str) -> None:
        await self.irene.send_message(
            sender=self.bot.bot_id,
            message=content,
        )
