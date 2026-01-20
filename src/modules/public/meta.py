from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from twitchio.ext import commands

from core import IrePublicComponent
from utils import const

if TYPE_CHECKING:
    from core import IreBot, IreContext

    class RunDict(TypedDict):
        keywords: list[str]
        game: str
        desc: str


__all__ = ("MetaCommands",)


class MetaCommands(IrePublicComponent):
    """Meta commands."""

    @commands.command()
    async def about(self, ctx: IreContext) -> None:
        """A bit bio information about the bot."""
        await ctx.send(f"I'm a personal Irene's bot, made by Irene. {const.STV.AYAYA}")

    @commands.command(name="commands", aliases=["help", "irenesbot"])
    async def command_list(self, ctx: IreContext) -> None:
        """Get a list of bot commands."""
        await ctx.send("aluerie.github.io/IreBot")

    @commands.command()
    async def irene(self, ctx: IreContext) -> None:
        """Just a random command that is unlikely to be in other bots."""
        await ctx.send(const.Global.FeelsDankMan)

    @commands.command()
    async def ping(self, ctx: IreContext) -> None:
        """Ping the bot.

        Currently doesn't provide any useful info.
        """
        await ctx.send("\N{TABLE TENNIS PADDLE AND BALL} Pong!")

    @commands.command()
    async def source(self, ctx: IreContext) -> None:
        """Get the link to the bot's GitHub repository."""
        await ctx.send("github.com/Aluerie/IreBot")


async def setup(bot: IreBot) -> None:
    """Load IreBot module. Framework of twitchio."""
    await bot.add_component(MetaCommands(bot))
