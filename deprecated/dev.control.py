from __future__ import annotations

from typing import TYPE_CHECKING

from twitchio.ext import commands

from bot import IreComponent
from utils import const

if TYPE_CHECKING:
    from bot import IreContext


class Control(IreComponent):
    """xd."""

    @commands.command()
    async def online(self, ctx: IreContext) -> None:
        """Make the bot treat streamer as online.

        * forces availability for commands which normally are only allowed during online streams
            via `@guards.is_online` (useful for debug);
        * If somehow eventsub missed stream_online notification - this can "manually"
            fix the problem of soft-locking the commands.
        """
        self.bot.irene.online = True  # pyright: ignore[reportAttributeAccessIssue]
        self.bot.dispatch("irene_online")
        await ctx.send(f"I'll treat {ctx.broadcaster.display_name} as online now {const.STV.dankHey}")

    @commands.command()
    async def offline(self, ctx: IreContext) -> None:
        """Make the bot treat streamer as offline."""
        self.bot.irene.online = False  # pyright: ignore[reportAttributeAccessIssue]
        self.bot.dispatch("irene_offline")
        await ctx.send(f"I'll treat {ctx.broadcaster.display_name} as offline now {const.STV.donkSad}")
