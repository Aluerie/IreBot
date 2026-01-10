from __future__ import annotations

from typing import TYPE_CHECKING, override

from twitchio.ext import commands

from utils import const

if TYPE_CHECKING:
    from ..bot import IreBot, IreContext, Irene


__all__ = ("IreComponent", "IrePersonalComponent", "IrePublicComponent")


class IreComponent(commands.Component):
    """Base component to use within IreBot."""

    def __init__(self, bot: IreBot) -> None:
        self.bot: IreBot = bot

    @property
    def irene(self) -> Irene:
        """A shortcut to Irene's object."""
        return self.bot.irene


class IrePublicComponent(IreComponent):
    """Base component to use for public extensions."""


class IrePersonalComponent(IreComponent):
    """Base component to use for personal extensions.

    Features in personal components are only available in Irene's main and secondary twitch channels.
    """

    @staticmethod
    def is_owners(user_id: str) -> bool:
        """A check whether the user is a bot owner."""
        return user_id in const.BOT_OWNERS

    @override
    async def component_before_invoke(self, ctx: IreContext) -> bool:
        return self.is_owners(ctx.channel.id)
