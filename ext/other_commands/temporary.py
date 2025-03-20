from __future__ import annotations

from typing import TYPE_CHECKING

from twitchio.ext import commands

from bot import IreComponent
from utils import const

if TYPE_CHECKING:
    from bot import IreBot


class MiscellaneousCommands(IreComponent):
    """Miscellaneous commands.

    Commands that are likely to be removed in future.
    """

    @commands.command()
    async def erdoc(self, ctx: commands.Context) -> None:
        """Link to my Elden Ring notes."""
        await ctx.send(  # cspell: disable-next-line
            "My notes with everything Elden Ring related: "
            "docs.google.com/document/d/19vTJVS7k1zdmShOAcO41KBWepfybMsTprQ208O7HpLU",
        )

    @commands.command()
    async def run(self, ctx: commands.Context) -> None:
        """Explanation of my first Sekiro hitless run."""
        msg = (
            "Bosses I like % Sword+Shuriken Focused. "
            "On paper it's Immortal Severance with 4 extra bosses and loading a save file "
            "for Emma, Fire Isshin and Inner Owl reflections. "
            "DB NKC No Loop No Cheese No Glitch. "
            "Sword+Shuriken focused. "
            "The only boss that I blast with MDs is Ape. "
            "My notes: docs.google.com/document/d/1rjp7lhvP0vwwlO7bC7TyFAjKcGDovFuo2EYUaX66QiA."
        )
        await ctx.send(msg)

    @commands.command(aliases=["sekironotes", "notes", "skdoc"])
    async def sekirodoc(self, ctx: commands.Context) -> None:
        """Link to my Sekiro notes."""
        await ctx.send(  # cspell: disable-next-line
            "My notes with everything Sekiro related: "
            "docs.google.com/document/d/1rjp7lhvP0vwwlO7bC7TyFAjKcGDovFuo2EYUaX66QiA",
        )

    @commands.group(invoke_fallback=True)
    async def gunfort(self, ctx: commands.Context) -> None:
        """Commands to count my successful and failed Yolo Gunfort attempts."""
        query = "SELECT value FROM ttv_counters WHERE name = $1;"
        success: int = await self.bot.pool.fetchval(query, "gunfort_success")
        query = "SELECT value FROM ttv_counters WHERE name = $1;"
        attempts: int = await self.bot.pool.fetchval(query, "gunfort_attempts")

        stats = f" Success Rate: {success / attempts:.1%} (over {attempts} attempts)"
        await ctx.send(f"{const.STV.science} Yolo Gunfort {stats}")

    @commands.is_owner()
    @gunfort.command()
    async def no(self, ctx: commands.Context) -> None:
        """Count a failed Yolo Gunfort attempt in."""
        query = "SELECT value FROM ttv_counters WHERE name = $1;"
        success: int = await self.bot.pool.fetchval(query, "gunfort_success")
        query = "UPDATE ttv_counters SET value = value + 1 WHERE name = $1 RETURNING value;"
        attempts: int = await self.bot.pool.fetchval(query, "gunfort_attempts")

        stats = f" Success Rate: {success / attempts:.1%} (over {attempts} attempts)"
        await ctx.send(f"Failed yolo gunfort? {const.STV.classic} {stats}")

    @commands.is_owner()
    @gunfort.command()
    async def yes(self, ctx: commands.Context) -> None:
        """Count a successful Yolo Gunfort attempt in."""
        query = "UPDATE ttv_counters SET value = value + 1 WHERE name = $1 RETURNING value;"
        success: int = await self.bot.pool.fetchval(query, "gunfort_success")
        query = "UPDATE ttv_counters SET value = value + 1 WHERE name = $1 RETURNING value;"
        attempts: int = await self.bot.pool.fetchval(query, "gunfort_attempts")

        stats = f" Success Rate: {success / attempts:.1%} (over {attempts} attempts)"
        await ctx.send(f"Yolo Gunfort is easy {const.STV.EZdodge} {stats}")


async def setup(bot: IreBot) -> None:
    """Load IreBot extension. Framework of twitchio."""
    await bot.add_component(MiscellaneousCommands(bot))
