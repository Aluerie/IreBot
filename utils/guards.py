"""My custom guards.

Notes
-----
1. Remember, group guards apply to children as well.
2. Due to my weird implementation - each guard also needs an error message
    defined directly in the `IreBot.event_command_error`
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from twitchio.ext import commands

if TYPE_CHECKING:
    from bot import IreContext

__all__ = (
    "is_online",
    "is_vps",
)


def is_vps() -> Any:
    """Allow the command to be completed only on VPS machine.

    A bit niche, mainly used for developer commands to interact with VPS machine such as
    kill the bot process or reboot it.
    """

    def predicate(ctx: IreContext) -> bool:
        # Still allow Irene to use the command during the testing;
        return ctx.bot.test or ctx.chatter.id == ctx.bot.owner_id

    return commands.guard(predicate)


def is_online() -> Any:
    """Allow the command to be completed only when Irene's stream is online."""

    def predicate(ctx: IreContext) -> bool:
        return ctx.bot.is_online(ctx.broadcaster.id)

    return commands.guard(predicate)
