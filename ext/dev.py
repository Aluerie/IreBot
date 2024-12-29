from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING, Annotated

from twitchio.ext import commands

from bot import LueComponent
from utils import const, guards

if TYPE_CHECKING:
    from bot import LueBot

log = logging.getLogger(__name__)


def to_extension(_: commands.Context, extension: str) -> str:
    return f"ext.{extension}"


class Development(LueComponent):
    """Dev Only Commands."""

    @guards.is_vps()
    @commands.is_owner()
    @commands.command(aliases=["kill"])
    async def maintenance(self, ctx: commands.Context) -> None:
        """Kill the bot process on VPS.

        Usable for bot testing so I don't have double responses.

        Note that this will turn off the whole bot functionality so things like main bot alerts will also stop.
        """
        await ctx.send("Shutting down the bot in 3 2 1")
        await asyncio.sleep(3)
        try:
            # non systemctl users - sorry
            os.system("sudo systemctl stop luebot")
        except Exception as error:
            log.error(error, stack_info=True)
            # it might not go off
            await ctx.send("Something went wrong.")

    @guards.is_vps()
    @commands.is_owner()
    @commands.command(aliases=["restart"])
    async def reboot(self, ctx: commands.Context) -> None:
        """Restart the bot process on VPS.

        Usable to restart the bot without logging to VPS machine or committing something.
        """
        await ctx.send("Rebooting in 3 2 1")
        await asyncio.sleep(3)
        try:
            # non systemctl users - sorry
            os.system("sudo systemctl restart luebot")
        except Exception as error:
            log.error(error, stack_info=True)
            # it might not go off
            await ctx.send("Something went wrong.")

    @commands.is_owner()
    @commands.command()
    async def unload(self, ctx: commands.Context, *, extension: Annotated[str, to_extension]) -> None:
        await self.bot.unload_module(extension)
        await ctx.send(f"{const.STV.DankApprove} unloaded {extension}")

    @commands.is_owner()
    @commands.command()
    async def reload(self, ctx: commands.Context, *, extension: Annotated[str, to_extension]) -> None:
        await self.bot.reload_module(extension)
        await ctx.send(f"{const.STV.DankApprove} reloaded {extension}")

    @commands.is_owner()
    @commands.command()
    async def load(self, ctx: commands.Context, *, extension: Annotated[str, to_extension]) -> None:
        await self.bot.load_module(extension)
        await ctx.send(f"{const.STV.DankApprove} loaded {extension}")

    @commands.is_owner()
    @commands.command()
    async def online(self, ctx: commands.Context) -> None:
        """Make the bot treat streamer as online.

        * forces availability for commands which normally are only allowed during online streams
            via `@guards.is_online` (useful for debug);
        * If somehow eventsub missed stream_online notification - this can "manually"
            fix the problem of soft-locking the commands.
        """
        self.bot.aluerie_online = True
        await ctx.send(f"I'll treat {ctx.broadcaster.display_name} as online now {const.STV.dankHey}")

    @commands.is_owner()
    @commands.command()
    async def offline(self, ctx: commands.Context) -> None:
        """Make the bot treat streamer as offline."""
        self.bot.aluerie_online = False
        await ctx.send(f"I'll treat {ctx.broadcaster.display_name} as offline now {const.STV.donkSad}")


async def setup(bot: LueBot) -> None:
    """Load LueBot extension. Framework of twitchio."""
    await bot.add_component(Development(bot))
