from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Annotated

from twitchio.ext import commands

from core import IreDevComponent
from utils import const, guards

if TYPE_CHECKING:
    from core import IreBot, IreContext

log = logging.getLogger(__name__)


def to_module(_: IreContext, module: str) -> str:
    """Just a shortcut to add `modules.` prefix to user input.

    So I can use command like this `!reload personal.emotes_check`.
    """
    return f"modules.{module}"


class Control(IreDevComponent):
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
    async def unload(self, ctx: IreContext, *, modules: Annotated[str, to_module]) -> None:
        """Unload the modules."""
        await self.bot.unload_module(modules)
        await ctx.send(f"{const.STV.DankApprove} unloaded {modules}")

    @commands.command()
    async def reload(self, ctx: IreContext, *, modules: Annotated[str, to_module]) -> None:
        """Reload the modules."""
        await self.bot.reload_module(modules)
        await ctx.send(f"{const.STV.DankApprove} reloaded {modules}")

    @commands.command()
    async def load(self, ctx: IreContext, *, modules: Annotated[str, to_module]) -> None:
        """Load the modules."""
        await self.bot.load_module(modules)
        await ctx.send(f"{const.STV.DankApprove} loaded {modules}")

    @commands.command(name="modules", aliases=["extensions", "components"])  # module != component but whatever
    async def list_modules(self, ctx: IreContext) -> None:
        """List modules that are currently loaded by the bot.

        Examples
        --------
        * "modules.personal.dev modules.public.states"
        """
        index = {"personal": [], "public": [], "dev": [], "other": []}
        for module in ctx.bot.modules.values():
            name = module.__name__
            for category in ("public", "personal", "dev"):
                if name.startswith(f"modules.{category}."):
                    index[category].append(name.removeprefix(f"modules.{category}."))
                    break
            else:
                index["other"].append(name.removeprefix("modules."))

        response = f" {const.STV.DankDolmes} ".join(f"{c}: {', '.join(m)}" for c, m in index.items() if m)
        await ctx.send(response)


async def setup(bot: IreBot) -> None:
    """Load IreBot module. Framework of twitchio."""
    await bot.add_component(Control(bot))
