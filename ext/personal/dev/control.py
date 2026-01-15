from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Annotated

from twitchio.ext import commands

from utils import const, guards

from ._base import BaseDevComponent

if TYPE_CHECKING:
    from bot import IreBot, IreContext

log = logging.getLogger(__name__)


def to_extension(_: IreContext, extension: str) -> str:
    """Just a shortcut to add `ext.` so I can use command like this `!reload emotes_check`."""
    return f"ext.{extension}"


class Control(BaseDevComponent):
    """Dev Only Commands."""

    @guards.is_vps()
    @commands.command(aliases=["kill"])
    async def maintenance(self, ctx: IreContext) -> None:
        """Kill the bot process on VPS.

        Usable for bot testing so I don't have double responses.

        Note that this will turn off the whole bot functionality so things like main bot alerts will also stop.
        """
        await ctx.send("Shutting down the bot in 3 2 1")
        await asyncio.sleep(3.0)
        try:
            await asyncio.create_subprocess_shell("sudo systemctl stop irebot")
        except Exception:
            log.exception("Failed to Stop the bot's process", stack_info=True)
            # it might not go off
            await ctx.send("Something went wrong.")

    @guards.is_vps()
    @commands.command(aliases=["restart"])
    async def reboot(self, ctx: IreContext) -> None:
        """Restart the bot process on VPS.

        Usable to restart the bot without logging to VPS machine or committing something.
        """
        await ctx.send("Rebooting in 3 2 1")
        await asyncio.sleep(3.0)
        try:
            await asyncio.create_subprocess_shell("sudo systemctl restart irebot")
        except Exception:
            log.exception("Failed to Restart the bot's process", stack_info=True)
            # it might not go off
            await ctx.send("Something went wrong.")

    @commands.command()
    async def unload(self, ctx: IreContext, *, extension: Annotated[str, to_extension]) -> None:
        """Unload the extension."""
        await self.bot.unload_module(extension)
        await ctx.send(f"{const.STV.DankApprove} unloaded {extension}")

    @commands.command()
    async def reload(self, ctx: IreContext, *, extension: Annotated[str, to_extension]) -> None:
        """Reload the extension."""
        await self.bot.reload_module(extension)
        await ctx.send(f"{const.STV.DankApprove} reloaded {extension}")

    @commands.command()
    async def load(self, ctx: IreContext, *, extension: Annotated[str, to_extension]) -> None:
        """Load the extension."""
        await self.bot.load_module(extension)
        await ctx.send(f"{const.STV.DankApprove} loaded {extension}")

    @commands.command(name="modules", aliases=["extensions", "components"])  # module != component but whatever
    async def list_modules(self, ctx: IreContext) -> None:
        """List modules that are currently loaded by the bot.

        Examples
        --------
        * "ext.personal.dev ext.public.states"
        """
        response = " ".join(module.__name__ for module in ctx.bot.modules.values())
        await ctx.send(response)


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(Control(bot))
