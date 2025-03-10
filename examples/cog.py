from __future__ import annotations

from typing import TYPE_CHECKING

from twitchio.ext import commands

from bot import LueComponent

if TYPE_CHECKING:
    from bot import IreBot


class NewCog(LueComponent):
    """."""

    @commands.command()
    async def new_command(self, ctx: commands.Context) -> None:
        """."""
        await ctx.send("Not implemented yet!")


async def setup(bot: IreBot) -> None:
    """Load LueBot extension. Framework of twitchio."""
    await bot.add_component(NewCog(bot))
