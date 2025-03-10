from __future__ import annotations

from typing import TYPE_CHECKING

from twitchio.ext import commands

from bot import IreComponent

if TYPE_CHECKING:
    from bot import IreBot


class NewCog(IreComponent):
    """."""

    @commands.command()
    async def new_command(self, ctx: commands.Context) -> None:
        """."""
        await ctx.send("Not implemented yet!")


async def setup(bot: IreBot) -> None:
    """Load LueBot extension. Framework of twitchio."""
    await bot.add_component(NewCog(bot))
