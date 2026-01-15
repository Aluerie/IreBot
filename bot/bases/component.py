from __future__ import annotations

from typing import TYPE_CHECKING, override

from twitchio.ext import commands

from utils import errors

if TYPE_CHECKING:
    from bot import IreBot, IreContext


__all__ = ("IrePersonalComponent", "IrePublicComponent")


class IreComponent(commands.Component):
    """Base component to use within IreBot."""

    def __init__(self, bot: IreBot) -> None:
        self.bot: IreBot = bot


class IrePublicComponent(IreComponent):
    """Base component to use for public extensions."""


class IrePersonalComponent(IreComponent):
    """Base component to use for personal extensions.

    Features in personal components are only available in Irene's main and secondary twitch channels.
    """

    def is_owner(self, user_id: str) -> bool:
        """A check whether the user is a bot owner."""
        return user_id == self.bot.owner_id

    @override
    async def component_before_invoke(self, ctx: IreContext) -> bool:
        if not self.is_owner(ctx.broadcaster.id):
            msg = "Command is not allowed anywhere except Irene's channel"
            raise errors.SilentError(msg)
        return True

